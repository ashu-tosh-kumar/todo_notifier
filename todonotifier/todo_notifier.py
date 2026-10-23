"""This module contains the core logic of the application

A TODO item is a tag (`TODO` by default) followed by optional parts, in this order. Whitespace between the parts does not matter.

    TAG[(owner)] [{date}] [@user] message

The tag is matched on word boundaries, so `TODO_LIST` and `todonotifier` are not tags. By default the parts are exactly as described in
`models`. With `extended_syntax` (what `scanner.scan` uses) the form is more forgiving, to accept what people usually write: `TAG(owner)` is
the same as `@owner` (Google style, Ruff TD002), and one `:` between the tag, owner, date or user and the message is dropped, so
`# TODO(ashu): fix this` has the owner `ashu` and the message `fix this`.
"""

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional, Sequence

from todonotifier.constants import DEFAULT_TAG, UNKNOWN_USER_NAME
from todonotifier.languages import (
    CommentIndex,
    CommentLexer,
    find_comment_end,
    get_comment_syntax,
)
from todonotifier.log import get_logger
from todonotifier.models import POSITION, TODO, USER
from todonotifier.utils import (
    compute_file_line_no_to_chars_map,
    compute_line_and_pos_given_span,
)

logger = get_logger(__name__)

# Kept for backwards compatibility with code that imports it. Parsing now builds its patterns with `_get_patterns`, which also match the tag on word boundaries
TODO_REGEX_PATTERN = r"TODO\s*(\{.*\})?\s*(@[^\s]*)?\s*(.*)?"

# File size threshold for switching to streaming parser (10 MB)
STREAMING_THRESHOLD_BYTES = 10 * 1024 * 1024

# Files with a NUL byte in their first bytes are treated as binary and skipped
BINARY_SNIFF_BYTES = 8 * 1024

# What follows the tag. The default form is the original one: the date is everything between the first `{` and the last `}`, the user is the next word
_LEGACY_TAIL = r"\s*(?:\{(?P<date>.*)\})?\s*(?:@(?P<user>[^\s]*))?\s*(?P<msg>.*)"
# The extended form adds `(owner)` right after the tag and drops one `:` before and after the date and user. An owner starts with a letter, so that
# issue references (a number, a hash sign or a URL in the parentheses) are not mistaken for people
_EXTENDED_TAIL = r"(?:\((?P<owner>[^\W\d][^()\s/]*)\))?[ \t]*:?[ \t]*(?:\{(?P<date>[^}]*)\})?[ \t]*(?:@(?P<user>[^\s:]*))?[ \t]*:?[ \t]*(?P<msg>.*)"


@dataclass(frozen=True)
class _TagPatterns:
    """Compiled patterns for one set of tags

    Attributes:
        find (re.Pattern[str]): Finds a tag on word boundaries
        parse (re.Pattern[str]): Parses text that starts at a tag into the groups `tag`, `owner`, `date`, `user` and `msg`
        canonical (dict[str, str]): Tag as spelled in the settings by the lower-cased tag, used to report `TODO` for `todo` when ignoring case
        ignore_case (bool): Whether tags are matched case insensitively
    """

    find: "re.Pattern[str]"
    parse: "re.Pattern[str]"
    canonical: Dict[str, str]
    ignore_case: bool


@lru_cache(maxsize=32)
def _get_patterns(tags: tuple, ignore_case: bool, extended_syntax: bool) -> _TagPatterns:
    """Builds (once per combination) the regular expressions for a set of tags

    The tags are escaped and alternated, longest first, so that `FIXME` is preferred over `FIX`.

    Args:
        tags (tuple): Tags to look for
        ignore_case (bool): Whether to match case insensitively
        extended_syntax (bool): Whether to accept `TAG(owner)` and a colon after the tag, owner, date and user

    Returns:
        _TagPatterns: The compiled patterns

    Raises:
        ValueError: Raised if a tag is not a string, or is empty or has surrounding whitespace only, or if there is no tag
    """
    unique: Dict[str, str] = {}
    for tag in tags:
        if not isinstance(tag, str) or not tag.strip():
            raise ValueError(f"Invalid tag: {tag!r}. A tag must be a non-empty string")
        unique.setdefault(tag.strip().lower() if ignore_case else tag.strip(), tag.strip())

    if not unique:
        raise ValueError("At least one tag is needed")

    alternation: str = "|".join(re.escape(tag) for tag in sorted(unique.values(), key=len, reverse=True))
    tag_pattern: str = rf"(?<!\w)(?P<tag>{alternation})(?!\w)"
    flags: int = re.IGNORECASE if ignore_case else 0
    tail: str = _EXTENDED_TAIL if extended_syntax else _LEGACY_TAIL

    return _TagPatterns(
        find=re.compile(tag_pattern, flags),
        parse=re.compile(tag_pattern + tail, flags),
        canonical={tag.lower(): tag for tag in unique.values()} if ignore_case else {tag: tag for tag in unique.values()},
        ignore_case=ignore_case,
    )


def _patterns_for(tags: Optional[Sequence[str]], ignore_case: bool, extended_syntax: bool) -> _TagPatterns:
    """Gets the compiled patterns for `tags`, where None means the default tag

    Args:
        tags (Sequence[str] | None): Tags to look for. None means ["TODO"]
        ignore_case (bool): Whether to match case insensitively
        extended_syntax (bool): Whether to accept `TAG(owner)` and a colon after the tag, owner, date and user

    Returns:
        _TagPatterns: The compiled patterns
    """
    if tags is None:
        tags = [DEFAULT_TAG]
    elif isinstance(tags, str):
        tags = [tags]

    return _get_patterns(tuple(tags), ignore_case, extended_syntax)


def _parse_todo_from_match(
    todo_item_group: str,
    flags: int,
    rel_file_path: str,
    line_no: int,
    tags: Optional[Sequence[str]] = None,
    extended_syntax: bool = False,
) -> TODO:
    """Helper function to parse a TODO object from a regex match. All parsing of the parts of a TODO happens here

    Args:
        todo_item_group (str): The matched text, starting at the tag and running to the end of the line
        flags (int): Regex flags to use. Only `re.IGNORECASE` matters
        rel_file_path (str): Relative path of the file
        line_no (int): Line number where TODO was found
        tags (Sequence[str] | None, optional): Tags that are looked for. Defaults to None, which means ["TODO"]
        extended_syntax (bool, optional): Whether to accept `TAG(owner)` and a colon after the tag, owner, date and user. Defaults to False

    Returns:
        TODO: Parsed TODO object

    Raises:
        ValueError: Raised if `todo_item_group` does not contain a tag
    """
    patterns = _patterns_for(tags, bool(flags & re.IGNORECASE), extended_syntax)
    match = patterns.parse.search(todo_item_group)
    if match is None:
        raise ValueError(f"No tag found in: {todo_item_group!r}")

    owner: str = match.groupdict().get("owner") or match.group("user") or UNKNOWN_USER_NAME  # By default we assume an unknown user
    matched_tag: str = match.group("tag")
    tag: str = patterns.canonical.get(matched_tag.lower() if patterns.ignore_case else matched_tag, matched_tag)

    return TODO(match.group("msg") or "", USER(owner), match.group("date") or "", rel_file_path, POSITION(line_no), tag=tag)


def _first_tag_in_line(line: str, patterns: _TagPatterns, lexer: Optional[CommentLexer]) -> Optional[str]:
    """Finds the TODO on one line, for the streaming parser

    Args:
        line (str): The line without its line break
        patterns (_TagPatterns): Compiled patterns
        lexer (CommentLexer | None): Comment lexer of the file when a comment is required, else None. It must see every line in order

    Returns:
        str | None: Text from the first tag (if no comment is required) or from the first tag inside a comment, up to the end of that comment,
            or None if the line has no TODO
    """
    if lexer is None:
        match = patterns.find.search(line)
        if match is None:
            return None

        start = match.start()
        return line[start:]

    spans: Optional[List[tuple]] = lexer.comment_spans(line) if lexer.stateful else None
    for match in patterns.find.finditer(line):
        if spans is None:
            spans = lexer.comment_spans(line)
        end = find_comment_end(spans, match.start())
        if end is not None:
            start = match.start()
            return line[start:end]

    return None


def _parse_file_streaming(
    file: str,
    rel_file_path: str,
    ignore_todo_case: bool,
    tags: Optional[Sequence[str]] = None,
    require_comment: bool = False,
    extended_syntax: bool = False,
) -> List[TODO]:
    """Parse a file line-by-line using streaming approach for large files

    Args:
        file (str): Absolute path to the file
        rel_file_path (str): Relative path of the file
        ignore_todo_case (bool): Whether to ignore case when matching tags
        tags (Sequence[str] | None, optional): Tags that are looked for. Defaults to None, which means ["TODO"]
        require_comment (bool, optional): Whether a tag must be inside a comment, for files whose language is known. Defaults to False
        extended_syntax (bool, optional): Whether to accept `TAG(owner)` and a colon after the tag, owner, date and user. Defaults to False

    Returns:
        List[TODO]: List of TODO objects found in the file
    """
    todos = []
    flags = re.MULTILINE
    if ignore_todo_case:
        flags |= re.IGNORECASE

    try:
        patterns = _patterns_for(tags, ignore_todo_case, extended_syntax)
        syntax = get_comment_syntax(file) if require_comment else None
        lexer = CommentLexer(syntax) if syntax else None

        with open(file, "r", encoding="utf-8", errors="replace") as f:
            for line_no, line in enumerate(f, start=1):
                text = line.rstrip("\n")
                todo_item_group = _first_tag_in_line(text, patterns, lexer)
                if todo_item_group is not None:
                    try:
                        todo = _parse_todo_from_match(todo_item_group.strip(), flags, rel_file_path, line_no, tags, extended_syntax)
                        todos.append(todo)
                    except Exception:
                        logger.exception(f"Error parsing TODO on line {line_no} in file: {file}")
    except Exception:
        logger.exception(f"Error in streaming parse of file: {file}")

    return todos


def _parse_file_in_memory(
    file: str,
    rel_file_path: str,
    ignore_todo_case: bool,
    tags: Optional[Sequence[str]] = None,
    require_comment: bool = False,
    extended_syntax: bool = False,
) -> List[TODO]:
    """Parse a file by loading it entirely into memory (original approach)

    Args:
        file (str): Absolute path to the file
        rel_file_path (str): Relative path of the file
        ignore_todo_case (bool): Whether to ignore case when matching tags
        tags (Sequence[str] | None, optional): Tags that are looked for. Defaults to None, which means ["TODO"]
        require_comment (bool, optional): Whether a tag must be inside a comment, for files whose language is known. Defaults to False
        extended_syntax (bool, optional): Whether to accept `TAG(owner)` and a colon after the tag, owner, date and user. Defaults to False

    Returns:
        List[TODO]: List of TODO objects found in the file
    """
    todos = []
    try:
        patterns = _patterns_for(tags, ignore_todo_case, extended_syntax)
        line_no_to_chars_map = compute_file_line_no_to_chars_map(file)
        with open(file, "r", encoding="utf-8", errors="replace") as f:
            file_content = f.read()

        flags = re.MULTILINE
        if ignore_todo_case:
            flags |= re.IGNORECASE

        syntax = get_comment_syntax(file) if require_comment else None
        comment_index = CommentIndex(syntax, file_content.split("\n")) if syntax else None

        last_todo_line_no = 0
        todo_items = list(patterns.find.finditer(file_content))
        for todo_item_idx, todo_item in enumerate(todo_items):
            try:
                todo_position = todo_item.span()
                line_no = compute_line_and_pos_given_span(line_no_to_chars_map, todo_position)
                if line_no == last_todo_line_no:
                    continue  # Only one todo item is allowed per line, the rest of the line is its message

                line_end = file_content.find("\n", todo_position[0])
                if line_end == -1:
                    line_end = len(file_content)

                if comment_index is not None:
                    line_start = file_content.rfind("\n", 0, todo_position[0]) + 1
                    comment_end = comment_index.comment_end(line_no, todo_position[0] - line_start)
                    if comment_end is None:
                        continue
                    line_end = line_start + comment_end

                todo_start = todo_position[0]
                todo_item_group = file_content[todo_start:line_end].rstrip()

                todo = _parse_todo_from_match(todo_item_group, flags, rel_file_path, line_no, tags, extended_syntax)
                todos.append(todo)
                last_todo_line_no = line_no
            except Exception:
                logger.exception(f"Error in parsing todo item: {todo_item}, idx: {todo_item_idx}")
    except Exception:
        logger.exception(f"Error in parsing todo items in file: {file}")

    return todos


def _is_binary_file(file: str) -> bool:
    """Tells whether a file looks binary, i.e. has a NUL byte in its first `BINARY_SNIFF_BYTES` bytes

    Args:
        file (str): Path of the file

    Returns:
        bool: True if the file looks binary
    """
    with open(file, "rb") as f:
        return b"\0" in f.read(BINARY_SNIFF_BYTES)


def parse_files_for_todo_items(
    project_parent_dir: str,
    files: List[str],
    ignore_todo_case: bool,
    tags: Optional[List[str]] = None,
    require_comment: bool = False,
    *,
    extended_syntax: bool = False,
) -> Dict[str, List[TODO]]:
    """Parses the list of `files` one by one to collect all todo items

    Uses streaming parser for files larger than STREAMING_THRESHOLD_BYTES, otherwise loads file into memory. Binary files (a NUL byte in the
    first 8 KB) are skipped and do not appear in the result. Text is read as UTF-8, and bytes that are not valid UTF-8 are replaced.

    Args:
        project_parent_dir (str): Parent directory of the project folder (required to get relative path of files and avoid exposing temporary paths)
        files (List[str]): List of all files that need to be parsed
        ignore_todo_case (bool): Boolean whether to look for case insensitive todo items like todo, Todo etc.
        tags (List[str] | None, optional): Tags to look for, e.g. ["TODO", "FIXME"]. Defaults to None, which means ["TODO"]
        require_comment (bool, optional): Whether a tag counts only when it is inside a comment. This depends on the language of the file, taken from
            its extension (see `languages.COMMENT_SYNTAX`); files with an unknown extension are matched anywhere. Defaults to False
        extended_syntax (bool, optional): Whether to accept `TAG(owner)` as an owner and drop one `:` after the tag, owner, date and user. Defaults to
            False, which keeps the original behavior

    Returns:
        Dict[str, List[TODO]]: Returns a key-value pair where key is relative path of file parsed and value is list of todo objects in that file

    Raises:
        ValueError: Raised if `tags` is empty or has an empty tag
    """
    _patterns_for(tags, ignore_todo_case, extended_syntax)  # Fail early on bad tags, not once per file

    all_todos_objs = {}
    for file in files:
        try:
            rel_file_path = os.path.relpath(file, project_parent_dir)
            file_size = os.path.getsize(file)

            if _is_binary_file(file):
                logger.debug(f"Skipping binary file: {file}")
                continue

            # Choose parsing strategy based on file size
            if file_size > STREAMING_THRESHOLD_BYTES:
                logger.info(f"Using streaming parser for large file ({file_size / (1024 * 1024):.2f} MB): {file}")
                todos = _parse_file_streaming(file, rel_file_path, ignore_todo_case, tags, require_comment, extended_syntax)
            else:
                todos = _parse_file_in_memory(file, rel_file_path, ignore_todo_case, tags, require_comment, extended_syntax)

            all_todos_objs[rel_file_path] = todos
        except Exception:
            logger.exception(f"Error in parsing todo items in file: {file}")
            all_todos_objs[rel_file_path] = []

    return all_todos_objs
