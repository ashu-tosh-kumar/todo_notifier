"""This module defines which file types TODO Notifier knows about and how comments look in each of them.

It holds the `"common"` extension preset (`expand_extensions`) and, for `ScanSettings.require_comment`, a table from file extension to comment
syntax (`COMMENT_SYNTAX`, `get_comment_syntax`) plus a small per-line lexer (`CommentLexer`, `CommentIndex`) that tells whether a column of a
line is inside a comment.

The comment detection is a pragmatic heuristic, not a parser. It is designed to reject the usual decoys (a tag inside a string, a Markdown code
sample) while accepting every ordinary comment. Its limits:

- A tag counts when it comes after a line comment marker (`#`, `//`, `--`) that is not inside a string literal on the same line, or when it is
  inside a block comment (`/* */`, `<!-- -->`). The state of block comments is tracked across the lines of a file, so the lines of a
  multi-line block comment, including the ones that start with `*`, are comments.
- String literals are `"..."` and `'...'` on one line (a backslash escapes the next character) plus multi-line strings for the languages
  that have them (triple quotes in Python, Java, Kotlin, Swift, Scala and C#, backticks in JavaScript, TypeScript and Go). A quote that is not
  closed on its line is treated as an ordinary character, so an apostrophe or a Rust lifetime does not hide the comment after it.
- In YAML and shell a `#` starts a comment only at the start of the line or after whitespace, so `http://host/#TODO` or `$#` are not comments.
- A tag in a docstring or any other string, including a multi-line one, is not a comment and is not reported.
- Not handled: nested block comments (Rust, Swift, Scala), Python raw or f-string subtleties, heredocs, Ruby `=begin`/`=end`, regular
  expression literals and PHP/HTML pieces embedded in other languages, for example a `<script>` block inside HTML. Each can lead to a missed
  or a spurious TODO in unusual code.
- Markdown code fences (lines between ``` or ~~~) are skipped entirely, so a code sample is never reported.
- A file whose extension is not in `COMMENT_SYNTAX` has no known comment syntax, and a tag is then matched anywhere in it.
"""

from dataclasses import dataclass
from typing import Optional

COMMON_EXTENSIONS: list[str] = [
    "py",
    "js",
    "jsx",
    "ts",
    "tsx",
    "java",
    "kt",
    "go",
    "rs",
    "rb",
    "php",
    "c",
    "h",
    "cpp",
    "hpp",
    "cs",
    "swift",
    "scala",
    "sh",
    "sql",
    "yaml",
    "yml",
    "toml",
    "html",
    "css",
    "scss",
    "md",
]

COMMON_PRESET_NAME: str = "common"


def expand_extensions(value: str | list[str]) -> list[str]:
    """Expands the `"common"` preset and normalizes a list of file extensions

    Leading dots are stripped, blank entries are dropped and duplicates are removed, keeping the first occurrence. `"common"` (matched case
    insensitively) may be given alone or as an element of a list, and is replaced in place by `COMMON_EXTENSIONS`.

    Args:
        value (str | list[str]): A single extension or preset name, or a list of them. For example `"common"`, `"py"` or `["common", ".proto"]`

    Returns:
        list[str]: Extensions without the leading dot, without duplicates, in order of first appearance
    """
    items: list[str] = [value] if isinstance(value, str) else value
    expanded: list[str] = []
    seen: set[str] = set()

    for item in items:
        names: list[str] = COMMON_EXTENSIONS if item.strip().lower() == COMMON_PRESET_NAME else [item]
        for name in names:
            extension: str = name.strip().lstrip(".")
            if extension and extension not in seen:
                seen.add(extension)
                expanded.append(extension)

    return expanded


@dataclass(frozen=True)
class CommentSyntax:
    """How comments (and the strings that can hide comment markers) look in one language

    Attributes:
        line_markers (tuple[str, ...]): Markers that start a comment running to the end of the line, e.g. ("//",)
        block_comments (tuple[tuple[str, str], ...]): Pairs of (open, close) markers of comments that may span lines, e.g. (("/*", "*/"),)
        multiline_strings (tuple[str, ...]): Delimiters of string literals that may span lines, e.g. triple double quotes. The closing delimiter is the same
        fenced_code (bool): Whether lines between ``` or ~~~ fences are code samples that must be skipped (Markdown)
        spaced_line_markers (bool): Whether a line marker starts a comment only at the start of the line or after whitespace, as in YAML and shell,
            where `#` in `http://host/#anchor` or `$#` is not a comment
    """

    line_markers: tuple[str, ...] = ()
    block_comments: tuple[tuple[str, str], ...] = ()
    multiline_strings: tuple[str, ...] = ()
    fenced_code: bool = False
    spaced_line_markers: bool = False

    @property
    def stateful(self) -> bool:
        """Whether the lexer state can carry over from one line to the next, so lines cannot be looked at in isolation"""
        return bool(self.block_comments or self.multiline_strings or self.fenced_code)


_HASH = CommentSyntax(line_markers=("#",))
_SPACED_HASH = CommentSyntax(line_markers=("#",), spaced_line_markers=True)
_C_LIKE = CommentSyntax(line_markers=("//",), block_comments=(("/*", "*/"),))
_C_LIKE_TRIPLE = CommentSyntax(line_markers=("//",), block_comments=(("/*", "*/"),), multiline_strings=('"""',))
_C_LIKE_BACKTICK = CommentSyntax(line_markers=("//",), block_comments=(("/*", "*/"),), multiline_strings=("`",))
_DASH_DASH = CommentSyntax(line_markers=("--",), block_comments=(("/*", "*/"),))

COMMENT_SYNTAX: dict[str, CommentSyntax] = {
    "py": CommentSyntax(line_markers=("#",), multiline_strings=('"""', "'''")),
    "pyi": CommentSyntax(line_markers=("#",), multiline_strings=('"""', "'''")),
    "sh": _SPACED_HASH,
    "bash": _SPACED_HASH,
    "rb": _HASH,
    "yaml": _SPACED_HASH,
    "yml": _SPACED_HASH,
    "toml": CommentSyntax(line_markers=("#",), multiline_strings=('"""', "'''")),
    "js": _C_LIKE_BACKTICK,
    "jsx": _C_LIKE_BACKTICK,
    "mjs": _C_LIKE_BACKTICK,
    "cjs": _C_LIKE_BACKTICK,
    "ts": _C_LIKE_BACKTICK,
    "tsx": _C_LIKE_BACKTICK,
    "go": _C_LIKE_BACKTICK,
    "java": _C_LIKE_TRIPLE,
    "kt": _C_LIKE_TRIPLE,
    "kts": _C_LIKE_TRIPLE,
    "swift": _C_LIKE_TRIPLE,
    "scala": _C_LIKE_TRIPLE,
    "cs": _C_LIKE_TRIPLE,
    "c": _C_LIKE,
    "h": _C_LIKE,
    "cpp": _C_LIKE,
    "hpp": _C_LIKE,
    "cc": _C_LIKE,
    "cxx": _C_LIKE,
    "hh": _C_LIKE,
    "rs": _C_LIKE,
    "scss": _C_LIKE,
    "php": CommentSyntax(line_markers=("//", "#"), block_comments=(("/*", "*/"),)),
    "css": CommentSyntax(block_comments=(("/*", "*/"),)),
    "sql": _DASH_DASH,
    "lua": CommentSyntax(line_markers=("--",), block_comments=(("--[[", "]]"),)),
    "html": CommentSyntax(block_comments=(("<!--", "-->"),)),
    "htm": CommentSyntax(block_comments=(("<!--", "-->"),)),
    "md": CommentSyntax(block_comments=(("<!--", "-->"),), fenced_code=True),
}
"""Comment syntax by lower-case file extension without the dot. Extensions that are missing here are matched anywhere in the file"""

_FENCES: tuple[str, ...] = ("```", "~~~")
_SIMPLE_QUOTES: tuple[str, ...] = ('"', "'")


def get_comment_syntax(path: str) -> Optional[CommentSyntax]:
    """Looks up the comment syntax of a file by its extension

    Args:
        path (str): File path or file name. The extension is the text after the last dot of the file name, compared case insensitively

    Returns:
        CommentSyntax | None: The syntax, or None if the extension is unknown (or the file has none)
    """
    name: str = path.replace("\\", "/").rsplit("/", 1)[-1]
    if "." not in name:
        return None

    return COMMENT_SYNTAX.get(name.rsplit(".", 1)[-1].lower())


def find_comment_end(spans: list[tuple[int, int]], column: int) -> Optional[int]:
    """Finds the comment range that contains a column

    Args:
        spans (list[tuple[int, int]]): Ranges as returned by `CommentLexer.comment_spans`
        column (int): 0-indexed column

    Returns:
        int | None: End of the range that contains `column`, or None if no range does
    """
    for start, end in spans:
        if start <= column < end:
            return end

    return None


def _find_string_end(line: str, start: int, delimiter: str) -> int:
    """Finds the end of a string literal on one line

    Args:
        line (str): The line
        start (int): Index of the first character after the opening delimiter
        delimiter (str): The closing delimiter

    Returns:
        int: Index of the first character after the closing delimiter, or -1 if the string is not closed on this line. A backslash escapes the next character
    """
    index: int = start
    while index < len(line):
        if line[index] == "\\":
            index += 2
        elif line.startswith(delimiter, index):
            return index + len(delimiter)
        else:
            index += 1

    return -1


class CommentLexer:
    """Finds the comment parts of the lines of one file, one line at a time, in file order

    The lexer remembers whether the previous line ended inside a block comment, a multi-line string or a Markdown code fence. Feed it every line
    of a file in order when `CommentSyntax.stateful` is true. Otherwise lines can be fed in any order.
    """

    def __init__(self, syntax: CommentSyntax) -> None:
        """Initializer for `CommentLexer`

        Args:
            syntax (CommentSyntax): Comment syntax of the language of the file
        """
        self._syntax: CommentSyntax = syntax
        self._block_closers: dict[str, str] = dict(syntax.block_comments)
        # Longest token first, so that a triple quote wins over a single one and `--[[` over `--`
        tokens: list[str] = [*syntax.line_markers, *self._block_closers, *syntax.multiline_strings, *_SIMPLE_QUOTES]
        self._tokens: tuple[str, ...] = tuple(sorted(set(tokens), key=len, reverse=True))
        # State carried to the next line: None (code), ("comment", closing marker), ("string", delimiter) or ("fence", fence characters)
        self._state: Optional[tuple[str, str]] = None

    @property
    def stateful(self) -> bool:
        """Whether lines must be fed in file order (see `CommentSyntax.stateful`)"""
        return self._syntax.stateful

    def comment_spans(self, line: str) -> list[tuple[int, int]]:
        """Lexes one line and returns the column ranges of it that are comment text

        Args:
            line (str): The line, without the line break

        Returns:
            list[tuple[int, int]]: `(start, end)` column ranges of comment text, `end` exclusive. A range starts at a line comment marker, or after the
                opening marker of a block comment, and ends before the closing marker. A line without comments gives []
        """
        spans: list[tuple[int, int]] = []
        length: int = len(line)
        position: int = 0
        next_token: dict[str, int] = {}  # Where each token occurs next, shared by all the steps over this line, see `_lex_code`

        if self._syntax.fenced_code and self._update_fence(line):
            return spans

        while position < length:
            if self._state is not None:
                kind, closer = self._state
                if kind == "comment":
                    end: int = line.find(closer, position)
                    spans.append((position, length if end == -1 else end))
                    if end == -1:
                        return spans
                    position = end + len(closer)
                else:
                    end = _find_string_end(line, position, closer)
                    if end == -1:
                        return spans
                    position = end
                self._state = None
                continue

            position = self._lex_code(line, position, spans, next_token)
            if position < 0:
                return spans

        return spans

    def _update_fence(self, line: str) -> bool:
        """Tracks Markdown code fences

        Args:
            line (str): The line

        Returns:
            bool: True if the line is a fence marker or is inside a fenced block, i.e. the line is a code sample and has no comments
        """
        stripped: str = line.lstrip()
        if self._state is not None and self._state[0] == "fence":
            if stripped.startswith(self._state[1]):
                self._state = None
            return True

        if self._state is None:
            for fence in _FENCES:
                if stripped.startswith(fence):
                    self._state = ("fence", fence)
                    return True

        return False

    def _lex_code(self, line: str, position: int, spans: list[tuple[int, int]], next_token: dict[str, int]) -> int:
        """Lexes code (not inside a comment or string) from `position` up to the next comment or multi-line string

        Args:
            line (str): The line
            position (int): Column to start at
            spans (list[tuple[int, int]]): Comment ranges found so far. A new range is appended when the code is followed by a comment
            next_token (dict[str, int]): Column of the next occurrence of each token (-1 if there is none), as found so far on this line. A token is
                searched for again only once the lexer has moved past its remembered column. Searching every token from scratch at every step is
                quadratic on a long line, and a minified bundle is one line of a megabyte with thousands of string literals

        Returns:
            int: Column to continue at, or -1 if the rest of the line was consumed
        """
        length: int = len(line)
        while position < length:
            match_index: int = -1
            token: str = ""
            for candidate in self._tokens:
                found: int = next_token.get(candidate, -2)
                if found == -2 or (found != -1 and found < position):
                    found = next_token[candidate] = line.find(candidate, position)
                if found != -1 and (match_index == -1 or found < match_index):
                    match_index, token = found, candidate
            if match_index == -1:
                return -1

            after: int = match_index + len(token)
            if token in self._syntax.line_markers:
                if self._syntax.spaced_line_markers and match_index > 0 and not line[match_index - 1].isspace():
                    position = after
                    continue
                spans.append((match_index, length))
                return -1
            if token in self._block_closers:
                self._state = ("comment", self._block_closers[token])
                return after
            end: int = _find_string_end(line, after, token)
            if token in self._syntax.multiline_strings and end == -1:
                self._state = ("string", token)
                return -1
            # An unclosed single-line quote (an apostrophe, a Rust lifetime) is just a character
            position = after if end == -1 else end

        return -1


class CommentIndex:
    """Answers "is this column of this line inside a comment?" for the lines of one file

    Block comment state is computed incrementally in file order, so asking about a line costs lexing the lines up to it, once.
    """

    def __init__(self, syntax: CommentSyntax, lines: list[str]) -> None:
        """Initializer for `CommentIndex`

        Args:
            syntax (CommentSyntax): Comment syntax of the language of the file
            lines (list[str]): All lines of the file, without line breaks
        """
        self._syntax: CommentSyntax = syntax
        self._lines: list[str] = lines
        self._lexer: CommentLexer = CommentLexer(syntax)
        self._spans: list[list[tuple[int, int]]] = []

    def comment_end(self, line_no: int, column: int) -> Optional[int]:
        """Tells where the comment that a position is in ends

        Args:
            line_no (int): 1-indexed line number
            column (int): 0-indexed column in that line

        Returns:
            int | None: Column where the comment text ends on that line (before the closing marker of a block comment, else the end of the line),
                or None if the position is not in a comment
        """
        if self._syntax.stateful:
            while len(self._spans) < line_no:
                self._spans.append(self._lexer.comment_spans(self._lines[len(self._spans)]))
            spans: list[tuple[int, int]] = self._spans[line_no - 1]
        else:
            spans = CommentLexer(self._syntax).comment_spans(self._lines[line_no - 1])

        return find_comment_end(spans, column)
