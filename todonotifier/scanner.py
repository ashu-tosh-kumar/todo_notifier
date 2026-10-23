"""This module provides `scan`, a pure function that finds TODO items in place and returns them as a structured `ScanResult`.

Unlike `driver.run`, scanning copies nothing, writes nothing, sends nothing and leaves no temporary directories behind.
"""

import os
from datetime import date, datetime, time
from typing import Optional

from todonotifier.git_meta import enrich_with_git, list_git_files
from todonotifier.log import get_logger
from todonotifier.results import ScanResult, TodoItem
from todonotifier.settings import ScanSettings
from todonotifier.todo_notifier import parse_files_for_todo_items
from todonotifier.utils import _ignore_dir_or_file, get_files_in_dir

logger = get_logger(__name__)


class ScanException(Exception):
    """Raised if `scan` is given settings it cannot act on, e.g. no paths or a path that does not exist"""

    pass


def _resolve_root(abs_paths: list[str]) -> str:
    """Decides the directory that item paths are made relative to

    - A single directory is its own root, so `scan(".")` reports `src/a.py`, not `./src/a.py`.
    - Otherwise (individual files or several paths) the current working directory is the root if every path is inside it. This keeps
      paths repository relative when the caller passes staged files. If some path is outside, the closest common directory is used.

    Args:
        abs_paths (list[str]): Absolute paths that exist

    Returns:
        str: Absolute path of the root directory
    """
    if len(abs_paths) == 1 and os.path.isdir(abs_paths[0]):
        return abs_paths[0]

    cwd = os.getcwd()
    if all(os.path.commonpath([cwd, path]) == cwd for path in abs_paths):
        return cwd

    return os.path.commonpath([path if os.path.isdir(path) else os.path.dirname(path) for path in abs_paths])


def _is_excluded(path: str, root: str, settings: ScanSettings) -> bool:
    """Tells whether the directory walk would have skipped a file, for files that did not come from the walk

    Args:
        path (str): Absolute path of the file
        root (str): Absolute path of the directory being scanned, which itself is never excluded (like in the walk)
        settings (ScanSettings): Scan settings

    Returns:
        bool: True if the file has another extension than `settings.extensions`, is excluded by name, or is below an excluded directory
    """
    if not path.endswith(tuple(f".{extension}" for extension in settings.extensions)) or _ignore_dir_or_file(path, settings.exclude_files):
        return True

    directory: str = os.path.dirname(path)
    while len(directory) > len(root):
        if _ignore_dir_or_file(directory, settings.exclude_dirs):
            return True
        directory = os.path.dirname(directory)

    return False


def _git_files_below(directory: str, settings: ScanSettings) -> Optional[list[str]]:
    """Lists the files below `directory` that git does not ignore and the extension and exclusion settings allow

    Args:
        directory (str): Absolute path of a directory
        settings (ScanSettings): Scan settings

    Returns:
        list[str] | None: Absolute paths, or None if `directory` is not in a git repository (or git is not available)
    """
    git_files: Optional[list[str]] = list_git_files(directory)
    if git_files is None:
        return None

    return [path for path in git_files if not _is_excluded(path, directory, settings)]


def _is_listed_by_git(path: str) -> bool:
    """Tells whether git lists a file (tracked, or untracked and not ignored). Files outside a git repository count as listed

    Args:
        path (str): Absolute path of a file

    Returns:
        bool: False only if the file is in a git repository and git ignores it
    """
    git_files: Optional[list[str]] = list_git_files(os.path.dirname(path), pathspec=os.path.basename(path))

    return git_files is None or path in git_files


def _collect_files(abs_paths: list[str], settings: ScanSettings) -> list[str]:
    """Collects the files to parse from directories (walked recursively) and individual files

    Individual files are filtered by extension and `exclude_files`, just like files found while walking a directory. With
    `settings.respect_gitignore`, the files of a directory and the individual files that are in a git repository are limited to the ones git
    lists (tracked, or untracked and not ignored); where there is no repository, the tree is walked as usual.

    Args:
        abs_paths (list[str]): Absolute paths of directories and files that exist
        settings (ScanSettings): Scan settings

    Returns:
        list[str]: Sorted absolute paths of the files to parse, without duplicates
    """
    extensions = tuple(f".{extension}" for extension in settings.extensions)
    files: set[str] = set()

    for path in abs_paths:
        if os.path.isdir(path):
            git_files: Optional[list[str]] = _git_files_below(path, settings) if settings.respect_gitignore else None
            if git_files is not None:
                files.update(git_files)
            else:
                files.update(get_files_in_dir(path, settings.extensions, settings.exclude_dirs, settings.exclude_files))
        elif path.endswith(extensions) and not _ignore_dir_or_file(path, settings.exclude_files):
            if settings.respect_gitignore and not _is_listed_by_git(path):
                logger.debug(f"Skipping file ignored by git: {path}")
            else:
                files.add(path)
        else:
            logger.debug(f"Skipping file not matching extensions or excluded: {path}")

    return sorted(files)


def _enrich_items(items: list[TodoItem], settings: ScanSettings, root: str, today: date) -> list[TodoItem]:
    """Hook for adding information that is not in the source text, after parsing and before the result is built

    With `settings.use_git_blame` it fills the author, creation date, default due date and deep link from git
    (`git_meta.enrich_with_git`, which calls `TodoItem.refresh_status` on every item whose due date it changes). Otherwise it does nothing.

    Args:
        items (list[TodoItem]): Items found by the parser
        settings (ScanSettings): Scan settings
        root (str): Absolute path the item paths are relative to
        today (date): Reference day of the scan

    Returns:
        list[TodoItem]: The enriched items
    """
    if settings.use_git_blame:
        return enrich_with_git(items, settings, root, today)

    return items


def scan(settings: ScanSettings, today: Optional[date] = None) -> ScanResult:
    """Scans `settings.paths` in place for TODO items

    Args:
        settings (ScanSettings): What and how to scan. Relative paths are resolved against the current working directory
        today (date | None, optional): Reference day for overdue and stale checks. Defaults to the current local date. Pass it to get
            deterministic results in tests

    Returns:
        ScanResult: Items found, ordered by file and line. Item paths are POSIX paths relative to `ScanResult.root`

    Raises:
        ScanException: Raised if `settings.paths` is empty or contains a path that does not exist
    """
    if not settings.paths:
        raise ScanException("No paths to scan")

    abs_paths: list[str] = [os.path.abspath(path) for path in settings.paths]
    for path in abs_paths:
        if not os.path.exists(path):
            raise ScanException(f"Path does not exist: {path}")

    reference_day: date = today or date.today()
    # The date of `generated_at` is the reference day of the status fields, so that `ScanResult.due_within` agrees with them
    generated_at: datetime = datetime.combine(today, time.min).astimezone() if today else datetime.now().astimezone()

    root: str = _resolve_root(abs_paths)
    files: list[str] = _collect_files(abs_paths, settings)
    logger.info(f"Scanning {len(files)} files under {root}")

    # `parse_files_for_todo_items` makes paths relative to its first argument, which is the root here
    try:
        todos_by_file = parse_files_for_todo_items(root, files, settings.ignore_case, settings.tags, settings.require_comment, extended_syntax=True)
    except ValueError as e:
        raise ScanException(f"Invalid settings: {e}") from e

    items: list[TodoItem] = []
    for todos in todos_by_file.values():
        items.extend(TodoItem.from_legacy(todo, today=reference_day, repo_web_url=settings.repo_web_url, commit_sha=settings.commit_sha) for todo in todos)

    items = _enrich_items(items, settings, root, reference_day)
    scanned_files: list[str] = sorted(rel_file.replace(os.sep, "/") for rel_file in todos_by_file)
    items.sort(key=lambda item: (item.file, item.line))

    return ScanResult(items=items, scanned_files=scanned_files, root=root, generated_at=generated_at)
