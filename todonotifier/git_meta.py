"""This module provides git metadata for scans: who introduced a line and when (`git blame`), and where the repository lives on the web.

`enrich_with_git` is what `scanner.scan` calls when `ScanSettings.use_git_blame` is on. It fills `TodoItem.author`, `created_date`,
default due dates (decision D4) and deep links. Everything degrades gracefully: if `git` is missing, the path is not a repository or a
blame call fails, the items are left as they are and the reason is logged once per scan, never raised.

`changed_lines` backs `--since GIT_REF` of the command line: it tells which lines of which files differ from a git ref.

All git calls use `subprocess.run` with list arguments (never a shell) and a timeout. Credentials found in remote URLs are always dropped.
"""

import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Iterable, Optional
from urllib.parse import urlsplit

from todonotifier.log import get_logger
from todonotifier.results import (
    AUTHOR_SOURCE_ANNOTATION,
    AUTHOR_SOURCE_GIT_BLAME,
    DUE_SOURCE_DEFAULT,
    DUE_SOURCE_NONE,
    TodoItem,
    build_web_url,
)
from todonotifier.settings import ScanSettings

logger = get_logger(__name__)

BLAME_TIMEOUT_SECONDS = 60
GIT_TIMEOUT_SECONDS = 10
LIST_FILES_TIMEOUT_SECONDS = 60
DIFF_TIMEOUT_SECONDS = 60
# Pathspecs are passed on the command line. Windows allows about 32,000 characters, so long lists are split into several calls
MAX_PATHSPEC_CHARS = 24000
DEFAULT_BLAME_WORKERS = 8
# Above this many lines in one file, a plain whole-file blame is used instead of one `-L` range per line, to keep the command line short
MAX_BLAME_RANGES = 200

# Warnings are module constants so that other integrations (e.g. the GitHub Action) can match or reuse them
WARNING_GIT_NOT_INSTALLED = (
    "git blame skipped: the `git` executable was not found (or did not answer in time). Authors, creation dates and default due dates are unavailable."
)
WARNING_NOT_A_GIT_REPO = (
    "git blame skipped: {path} is not inside a git repository (or git could not read it). Authors, creation dates and default due dates are unavailable."
)
WARNING_SHALLOW_CLONE = (
    "The repository is a shallow clone, so git blame authors and creation dates may be wrong (every line may be attributed to the newest commit). "
    "Fetch the full history, e.g. `fetch-depth: 0` for actions/checkout."
)
INFO_UNCOMMITTED = "{count} TODO(s) are on lines that are not committed yet: author unknown, creation date set to today."

_HUNK_PATTERN = re.compile(r"^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
_ZERO_SHA_PATTERN = re.compile(r"^0+$")
_HEADER_PATTERN = re.compile(r"^([0-9a-f]{40}|[0-9a-f]{64}) \d+ (\d+)(?: \d+)?$")
_SCP_LIKE_PATTERN = re.compile(r"^(?:[^@/\s]+@)?([^:/\s]+):(?!//)(.+)$")
_SHA_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class GitError(Exception):
    """Raised when a git query that the caller depends on fails, e.g. an unknown ref. The message is meant to be shown to the user"""


@dataclass(frozen=True)
class BlameLine:
    """Who introduced a line, and when

    Attributes:
        author_name (str | None): Name of the commit author, or None if the line is not committed
        author_email (str | None): Lower-cased email of the commit author without the angle brackets, or None if the line is not committed
        created_date (date): UTC date of the author time of the commit that introduced the line. Today if the line is not committed
        committed (bool): False if the line is not committed yet (all-zero commit hash)
    """

    author_name: Optional[str]
    author_email: Optional[str]
    created_date: date
    committed: bool = True


def _run_git(args: list[str], cwd: str, timeout: int = GIT_TIMEOUT_SECONDS) -> Optional["subprocess.CompletedProcess[bytes]"]:
    """Runs a git command without raising

    Args:
        args (list[str]): Arguments after `git`
        cwd (str): Directory to run in
        timeout (int, optional): Seconds before the command is abandoned. Defaults to `GIT_TIMEOUT_SECONDS`

    Returns:
        subprocess.CompletedProcess[bytes] | None: The finished process (check `returncode` yourself), or None if git is not installed, the
            directory cannot be entered or the command timed out
    """
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, check=False, timeout=timeout)
    except FileNotFoundError:
        logger.debug(f"git (or the directory {cwd}) not found")
    except subprocess.TimeoutExpired:
        logger.debug(f"git {args[0]} timed out after {timeout}s")
    except OSError as e:
        logger.debug(f"git {args[0]} could not run: {e.__class__.__name__}")

    return None


def _git_output(args: list[str], cwd: str) -> Optional[str]:
    """Runs a git command and returns its stripped standard output

    Args:
        args (list[str]): Arguments after `git`
        cwd (str): Directory to run in

    Returns:
        str | None: Output, or None if the command could not run, failed or printed nothing
    """
    process = _run_git(args, cwd)
    if process is None or process.returncode != 0:
        return None

    return process.stdout.decode("utf-8", errors="replace").strip() or None


def _locate_git_root(path: str) -> tuple[Optional[str], Optional[str]]:
    """Finds the repository root of `path` and says why it could not

    Args:
        path (str): File or directory

    Returns:
        tuple[str | None, str | None]: `(root, None)` on success, else `(None, warning)` where warning is one of the `WARNING_*` constants
    """
    directory: str = path if os.path.isdir(path) else os.path.dirname(os.path.abspath(path))
    process = _run_git(["rev-parse", "--show-toplevel"], directory)
    if process is None:
        return None, WARNING_GIT_NOT_INSTALLED

    root: str = process.stdout.decode("utf-8", errors="replace").strip()
    if process.returncode != 0 or not root:
        return None, WARNING_NOT_A_GIT_REPO.format(path=path)

    return root, None


def find_git_root(path: str) -> Optional[str]:
    """Finds the top level directory of the git repository that contains `path`

    Args:
        path (str): File or directory

    Returns:
        str | None: Absolute path of the repository root, or None if `path` is not in a repository, git is not installed or it timed out
    """
    return _locate_git_root(path)[0]


def _decode_paths(output: bytes, directory: str) -> list[str]:
    """Turns the NUL separated output of `git ls-files -z` into sorted absolute paths of the files that exist on disk"""
    relative_paths: list[str] = [os.fsdecode(entry) for entry in output.split(b"\0") if entry]
    absolute_paths: set[str] = {os.path.join(directory, relative_path) for relative_path in relative_paths}

    return sorted(path for path in absolute_paths if os.path.isfile(path))


def list_git_files(directory: str, pathspec: Optional[str] = None) -> Optional[list[str]]:
    """Lists the files below `directory` that git does not ignore: tracked files plus untracked ones that `.gitignore` does not exclude

    This is `git ls-files -z --cached --others --exclude-standard` run in `directory`, so only the files of that directory and its subdirectories
    are listed. Files that are tracked but deleted from disk are left out.

    Args:
        directory (str): Directory inside a git repository
        pathspec (str | None, optional): Limits the listing to this one path relative to `directory`, e.g. a file name. Defaults to None

    Returns:
        list[str] | None: Sorted absolute paths of the files, or None if `directory` is not in a repository, git is not installed, or the command
            failed or timed out. In that case callers should fall back to walking the directory tree
    """
    if find_git_root(directory) is None:
        return None

    args: list[str] = ["ls-files", "-z", "--cached", "--others", "--exclude-standard"]
    if pathspec is not None:
        args += ["--", pathspec]

    process = _run_git(args, directory, LIST_FILES_TIMEOUT_SECONDS)
    if process is None or process.returncode != 0:
        return None

    return _decode_paths(process.stdout, directory)


def filter_git_listed(paths: list[str]) -> Optional[list[str]]:
    """Keeps the files that git lists (tracked, or untracked and not ignored) among individually named files, with one `git ls-files` call

    This is what a pre-commit run needs: many staged files, one question. The files are looked up together from their closest common directory
    (long lists are split into a few calls, see `MAX_PATHSPEC_CHARS`), instead of asking once per file. Paths are matched literally, so names with
    glob characters work.

    Args:
        paths (list[str]): Absolute paths of existing files

    Returns:
        list[str] | None: The files of `paths` that git lists, in the order given, or None if their common directory is not in a repository, git is
            not installed, or a command failed or timed out. In that case callers should treat every file as listed
    """
    if not paths:
        return []

    try:
        directory: str = os.path.commonpath([os.path.dirname(path) for path in paths])
    except ValueError:  # Paths on different drives
        return None

    if find_git_root(directory) is None:
        return None

    pathspecs: list[str] = [":(literal)" + os.path.relpath(path, directory) for path in paths]
    chunks: list[list[str]] = [[]]
    size: int = 0
    for pathspec in pathspecs:
        if chunks[-1] and size + len(pathspec) > MAX_PATHSPEC_CHARS:
            chunks.append([])
            size = 0
        chunks[-1].append(pathspec)
        size += len(pathspec) + 1

    listed: set[str] = set()
    for chunk in chunks:
        process = _run_git(["ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *chunk], directory, LIST_FILES_TIMEOUT_SECONDS)
        if process is None or process.returncode != 0:
            return None
        listed.update(_decode_paths(process.stdout, directory))

    return [path for path in paths if path in listed]


def is_shallow_repository(root: str) -> bool:
    """Tells whether the repository is a shallow clone (history cut off), as is the default for `actions/checkout`

    Args:
        root (str): Repository root

    Returns:
        bool: True if `git rev-parse --is-shallow-repository` says "true". False otherwise, including when git fails
    """
    return _git_output(["rev-parse", "--is-shallow-repository"], root) == "true"


def parse_blame_porcelain(output: str, today: date) -> dict[int, BlameLine]:
    """Parses the output of `git blame --porcelain`

    In porcelain format the full header (author, mail, time and so on) is printed only the first time a commit appears. Later lines of
    the same commit only have the one-line `<sha> <original line> <final line> [<group size>]` header, so commits are remembered by hash.

    Args:
        output (str): Output of `git blame --porcelain`
        today (date): Creation date given to lines that are not committed

    Returns:
        dict[int, BlameLine]: Blame per final (1-indexed) line number
    """
    commits: dict[str, dict[str, str]] = {}
    line_commits: dict[int, str] = {}
    current_sha: Optional[str] = None

    # `split("\n")`, not `splitlines()`: source lines may contain characters that `splitlines` treats as line breaks
    for raw_line in output.split("\n"):
        if raw_line.startswith("\t"):  # The source line itself, checked first so that its content is never mistaken for a header
            continue

        header = _HEADER_PATTERN.match(raw_line)
        if header:
            current_sha = header.group(1)
            line_commits[int(header.group(2))] = current_sha
            commits.setdefault(current_sha, {})
        elif current_sha is not None:
            key, _, value = raw_line.partition(" ")
            if key in ("author", "author-mail", "author-time") and key not in commits[current_sha]:
                commits[current_sha][key] = value

    blame: dict[int, BlameLine] = {}
    parsed: dict[str, BlameLine] = {}
    for line_no, sha in line_commits.items():
        if sha not in parsed:
            parsed[sha] = _to_blame_line(sha, commits[sha], today)
        blame[line_no] = parsed[sha]

    return blame


def _to_blame_line(sha: str, meta: dict[str, str], today: date) -> BlameLine:
    """Converts the raw header fields of one commit to a `BlameLine`

    Args:
        sha (str): Commit hash. All zeros means the line is not committed
        meta (dict[str, str]): Raw values for the keys `author`, `author-mail` and `author-time`
        today (date): Creation date for uncommitted lines or lines whose time cannot be read

    Returns:
        BlameLine: Blame information of the commit
    """
    if _ZERO_SHA_PATTERN.match(sha):
        return BlameLine(author_name=None, author_email=None, created_date=today, committed=False)

    try:
        # UTC, not local time, so that the result does not depend on the timezone of the machine
        created: date = datetime.fromtimestamp(int(meta["author-time"]), tz=timezone.utc).date()
    except (KeyError, ValueError, OverflowError, OSError):
        created = today

    email: str = meta.get("author-mail", "").strip().strip("<>").strip().lower()
    return BlameLine(author_name=meta.get("author") or None, author_email=email or None, created_date=created)


def blame_file(root: str, rel_path: str, lines: Optional[Iterable[int]] = None, today: Optional[date] = None) -> dict[int, BlameLine]:
    """Runs one `git blame --porcelain` for a file

    Args:
        root (str): Repository root
        rel_path (str): Path of the file relative to `root`
        lines (Iterable[int] | None, optional): 1-indexed lines of interest. Blame is then limited to them (`-L`), which is much faster for
            big files with few TODOs. Defaults to None, i.e. the whole file
        today (date | None, optional): Creation date for uncommitted lines. Defaults to the current local date

    Returns:
        dict[int, BlameLine]: Blame per line number. Empty if the file is untracked, git is missing or the call fails or times out, in
            which case every line should be treated as uncommitted
    """
    reference_day: date = today or date.today()
    args: list[str] = ["blame", "--porcelain"]

    wanted: list[int] = sorted(set(lines)) if lines is not None else []
    if 0 < len(wanted) <= MAX_BLAME_RANGES:
        for line_no in wanted:
            args.extend(["-L", f"{line_no},{line_no}"])
    args.extend(["--", rel_path])

    process = _run_git(args, root, timeout=BLAME_TIMEOUT_SECONDS)
    if process is None or process.returncode != 0:
        logger.debug(f"git blame unavailable for {rel_path}, treating its lines as uncommitted")
        return {}

    return parse_blame_porcelain(process.stdout.decode("utf-8", errors="replace"), reference_day)


def blame_files(
    root: str,
    rel_paths: Iterable[str],
    max_workers: int = DEFAULT_BLAME_WORKERS,
    lines_by_file: Optional[dict[str, list[int]]] = None,
    today: Optional[date] = None,
) -> dict[str, dict[int, BlameLine]]:
    """Blames several files in parallel, one git call per file

    Args:
        root (str): Repository root
        rel_paths (Iterable[str]): Paths relative to `root`
        max_workers (int, optional): Maximum number of git processes at a time. Defaults to `DEFAULT_BLAME_WORKERS`
        lines_by_file (dict[str, list[int]] | None, optional): Lines of interest per path, see `blame_file`. Defaults to None
        today (date | None, optional): Creation date for uncommitted lines. Defaults to the current local date

    Returns:
        dict[str, dict[int, BlameLine]]: `blame_file` result per path
    """
    paths: list[str] = list(dict.fromkeys(rel_paths))
    if not paths:
        return {}

    reference_day: date = today or date.today()
    lines_by_file = lines_by_file or {}
    with ThreadPoolExecutor(max_workers=max(1, min(max_workers, len(paths)))) as executor:
        futures = {path: executor.submit(blame_file, root, path, lines_by_file.get(path), reference_day) for path in paths}
        return {path: future.result() for path, future in futures.items()}


def normalize_remote_url(remote_url: str) -> Optional[str]:
    """Turns a git remote URL into the web URL of the repository, dropping any credentials

    `git@host:org/repo.git`, `ssh://git@host/org/repo.git`, `https://user:token@host/org/repo.git` and `git://host/org/repo` all become
    `https://host/org/repo`. SSH ports are dropped, HTTP(S) ports are kept.

    Args:
        remote_url (str): URL as printed by `git remote get-url`

    Returns:
        str | None: Web URL, or None for URLs that are not hosted repositories (local paths, `file://`) or cannot be understood
    """
    remote_url = remote_url.strip()
    host: Optional[str]
    path: str

    if "://" in remote_url:
        try:
            parts = urlsplit(remote_url)
            host = parts.hostname
            port: Optional[int] = parts.port
        except ValueError:
            return None

        if parts.scheme not in ("http", "https", "ssh", "git", "git+ssh", "ssh+git") or not host:
            return None

        if port is not None and parts.scheme in ("http", "https"):
            host = f"{host}:{port}"
        path = parts.path
    else:
        scp_like = _SCP_LIKE_PATTERN.match(remote_url)
        if not scp_like:
            return None

        host, path = scp_like.group(1), scp_like.group(2)

    path = path.strip("/")
    if path.endswith(".git"):
        path = path[: -len(".git")]
    if not path or not host:
        return None

    return f"https://{host}/{path}"


def detect_repo_web_url(root: str) -> Optional[str]:
    """Detects the web URL of the repository, e.g. https://github.com/org/repo

    Prefers the GitHub Actions variables `GITHUB_SERVER_URL` and `GITHUB_REPOSITORY`, then the `origin` remote. Credentials are removed.

    Args:
        root (str): Repository root

    Returns:
        str | None: Web URL, or None if it cannot be determined
    """
    server: str = os.environ.get("GITHUB_SERVER_URL", "").strip()
    repository: str = os.environ.get("GITHUB_REPOSITORY", "").strip().strip("/")
    if server and repository:
        from_env: Optional[str] = normalize_remote_url(f"{server.rstrip('/')}/{repository}")
        if from_env:
            return from_env

    remote: Optional[str] = _git_output(["remote", "get-url", "origin"], root)
    return normalize_remote_url(remote) if remote else None


def detect_commit_sha(root: str) -> Optional[str]:
    """Detects the commit of the scanned tree: `GITHUB_SHA` if set (GitHub Actions), else `git rev-parse HEAD`

    Args:
        root (str): Repository root

    Returns:
        str | None: Full commit hash, or None if it cannot be determined
    """
    from_env: str = os.environ.get("GITHUB_SHA", "").strip().lower()
    if _SHA_PATTERN.match(from_env):
        return from_env

    head: Optional[str] = _git_output(["rev-parse", "HEAD"], root)
    return head.lower() if head and _SHA_PATTERN.match(head.lower()) else None


def _positive_days(days: Optional[int]) -> Optional[int]:
    """Validates `ScanSettings.default_due_days`

    Args:
        days (int | None): Configured number of days

    Returns:
        int | None: `days` if it is a positive integer, else None (default due dates are off)
    """
    return days if isinstance(days, int) and not isinstance(days, bool) and days > 0 else None


def enrich_with_git(items: list[TodoItem], settings: ScanSettings, scan_root: str, today: date) -> list[TodoItem]:
    """Fills ownership, age, default due dates and deep links from git

    - `created_date` is always set when blame is available (today for lines that are not committed).
    - `author` is set from the blame author (through `settings.author_aliases`) unless the item has an `@user` annotation.
    - If `settings.default_due_days` is a positive number and the item has no `{date}`, `due_date = created_date + default_due_days` and
      `due_source = "default"`. The item can then become stale, never overdue. An explicit date always wins.
    - `web_url` is recomputed from the repository relative path. The repository URL and commit come from `settings`, else are detected.

    If git is unavailable or `scan_root` is not in a repository, the items are returned untouched and the reason is logged once at WARNING
    level. The items are modified in place.

    Args:
        items (list[TodoItem]): Items to enrich. `TodoItem.file` is relative to `scan_root`
        settings (ScanSettings): Scan settings
        scan_root (str): Absolute path the item paths are relative to
        today (date): Reference day of the scan

    Returns:
        list[TodoItem]: The same items
    """
    if not items:
        return items

    root, reason = _locate_git_root(scan_root)
    if root is None:
        logger.warning(reason)
        return items

    if is_shallow_repository(root):
        logger.warning(WARNING_SHALLOW_CLONE)

    real_scan_root: str = os.path.realpath(scan_root)
    repo_paths: dict[int, str] = {}  # id(item) -> POSIX path relative to the repository root
    lines_by_file: dict[str, list[int]] = {}
    for item in items:
        repo_path: str = to_repo_path(item.file, real_scan_root, root)
        repo_paths[id(item)] = repo_path
        lines_by_file.setdefault(repo_path, []).append(item.line)

    blames: dict[str, dict[int, BlameLine]] = blame_files(root, lines_by_file, lines_by_file=lines_by_file, today=today)

    aliases: dict[str, str] = {email.lower(): handle for email, handle in settings.author_aliases.items()}
    default_days: Optional[int] = _positive_days(settings.default_due_days)
    uncommitted: int = 0

    for item in items:
        blame_line: Optional[BlameLine] = blames[repo_paths[id(item)]].get(item.line)
        if blame_line is None:
            blame_line = BlameLine(author_name=None, author_email=None, created_date=today, committed=False)

        if not blame_line.committed:
            uncommitted += 1
        elif item.author_source != AUTHOR_SOURCE_ANNOTATION:
            handle: Optional[str] = aliases.get(blame_line.author_email) if blame_line.author_email else None
            item.author = handle or blame_line.author_name or blame_line.author_email
            if item.author:
                item.author_source = AUTHOR_SOURCE_GIT_BLAME

        item.created_date = blame_line.created_date
        if default_days is not None and item.due_source == DUE_SOURCE_NONE:
            item.due_date = item.created_date + timedelta(days=default_days)
            item.due_source = DUE_SOURCE_DEFAULT
            item.refresh_status(today)

    if uncommitted:
        logger.info(INFO_UNCOMMITTED.format(count=uncommitted))

    repo_web_url: Optional[str] = settings.repo_web_url or detect_repo_web_url(root)
    commit_sha: Optional[str] = settings.commit_sha or detect_commit_sha(root)
    if repo_web_url and commit_sha:
        for item in items:
            item.web_url = build_web_url(repo_web_url, commit_sha, repo_paths[id(item)], item.line)

    return items


def to_repo_path(file: str, scan_root: str, repo_root: str) -> str:
    """Converts the path of a `TodoItem` to a path relative to the repository root

    Args:
        file (str): POSIX path relative to `scan_root` (`TodoItem.file`)
        scan_root (str): Directory the item paths are relative to (`ScanResult.root`). Symbolic links are resolved
        repo_root (str): Repository root, as printed by `git rev-parse --show-toplevel` (so with symbolic links resolved)

    Returns:
        str: POSIX path relative to `repo_root`. It starts with `..` for a file outside the repository
    """
    absolute: str = os.path.join(os.path.realpath(scan_root), *file.split("/"))
    return os.path.relpath(absolute, os.path.realpath(repo_root)).replace(os.sep, "/")


def _unquote_diff_path(raw: str) -> str:
    """Decodes a path from a `+++` line of `git diff`: git quotes names with special characters in C style (`"a\\tb"`, `"caf\\303\\251"`)

    Args:
        raw (str): The text after `+++ `, with or without the surrounding double quotes

    Returns:
        str: The plain path
    """
    if not (len(raw) >= 2 and raw.startswith('"') and raw.endswith('"')):
        return raw

    simple: dict[str, str] = {"a": "\a", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v", '"': '"', "\\": "\\"}
    data: bytearray = bytearray()
    body: str = raw[1:-1]
    index: int = 0
    while index < len(body):
        char: str = body[index]
        if char != "\\" or index + 1 >= len(body):
            data.extend(char.encode("utf-8"))
            index += 1
        elif body[index + 1] in simple:
            data.extend(simple[body[index + 1]].encode("utf-8"))
            index += 2
        else:  # Octal byte, always three digits
            start: int = index + 1
            end: int = index + 4
            digits: str = body[start:end]
            try:
                data.append(int(digits, 8))
                index += 4
            except ValueError:
                data.extend(char.encode("utf-8"))
                index += 1

    return data.decode("utf-8", errors="replace")


def parse_changed_lines(diff: str) -> dict[str, set[int]]:
    """Parses the output of `git diff --unified=0` into the added or changed lines of each file

    The paths come from the `+++ b/<path>` lines, so renamed files are reported under their new name. Deleted files and pure deletions have no
    changed lines. The hunk header says how many lines the hunk has, which is used to tell the lines of a hunk from file headers (an added line
    that reads `++ b/x` looks like a header otherwise).

    Args:
        diff (str): Output of `git diff --unified=0 --src-prefix=a/ --dst-prefix=b/`

    Returns:
        dict[str, set[int]]: 1-indexed line numbers in the new version of each file that has any, by POSIX path relative to the repository root
    """
    changed: dict[str, set[int]] = {}
    current: Optional[str] = None
    remaining_old: int = 0
    remaining_new: int = 0
    next_line: int = 0

    for line in diff.split("\n"):
        if remaining_old > 0 or remaining_new > 0:
            if line.startswith("-"):
                remaining_old -= 1
            elif line.startswith("+"):
                remaining_new -= 1
                if current is not None:
                    changed.setdefault(current, set()).add(next_line)
                next_line += 1
            continue

        if line.startswith("+++ "):
            raw: str = line[4:]
            raw = raw[:-1] if raw.endswith("\t") else raw  # git ends the name with a tab if it contains a space
            path: str = _unquote_diff_path(raw)
            current = path[2:] if path.startswith("b/") else None  # Anything else is /dev/null (deleted file)
            continue

        hunk = _HUNK_PATTERN.match(line)
        if hunk:
            remaining_old = int(hunk.group(1)) if hunk.group(1) is not None else 1
            remaining_new = int(hunk.group(3)) if hunk.group(3) is not None else 1
            next_line = int(hunk.group(2))

    return changed


def _count_lines(path: str) -> int:
    """Counts the lines of a file (a last line without a newline counts), reading it in chunks"""
    count: int = 0
    last: bytes = b"\n"
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            count += chunk.count(b"\n")
            last = chunk[-1:]

    return count + (0 if last == b"\n" else 1)


def changed_lines(root: str, ref: str) -> dict[str, set[int]]:
    """Finds the lines that were added or changed in the working tree compared to a git ref

    This is `git diff --unified=0 --no-color --no-ext-diff <ref> --` (working tree against `ref`, so staged and unstaged edits count and renames are
    followed) plus the untracked files that `.gitignore` does not exclude, which count as changed in full.

    Args:
        root (str): Repository root. The paths of the result are relative to it
        ref (str): Any commit-ish git understands, e.g. `HEAD~1`, `origin/main` or a tag

    Returns:
        dict[str, set[int]]: 1-indexed line numbers in the working tree, by POSIX path relative to `root`. Files without changed lines are left out

    Raises:
        GitError: Raised if `ref` is not a valid commit-ish, git is not installed or git fails or times out. The message is meant for the user
    """
    if not ref or ref.startswith("-"):
        raise GitError(f"Invalid git ref {ref!r}. Use a commit, a branch or a tag, e.g. HEAD~1 or origin/main.")

    verified = _run_git(["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], root)
    if verified is None:
        raise GitError("Could not run git. Is the git executable installed?")
    if verified.returncode != 0:
        raise GitError(f"Unknown git ref '{ref}'. Check the name, and fetch the history of a shallow clone (for GitHub Actions: fetch-depth: 0).")

    process = _run_git(
        ["diff", "--unified=0", "--no-color", "--no-ext-diff", "--no-textconv", "-M", "--src-prefix=a/", "--dst-prefix=b/", ref, "--"],
        root,
        DIFF_TIMEOUT_SECONDS,
    )
    if process is None or process.returncode != 0:
        raise GitError(f"git diff against '{ref}' failed.")

    changed: dict[str, set[int]] = parse_changed_lines(process.stdout.decode("utf-8", errors="replace"))

    untracked = _run_git(["ls-files", "-z", "--others", "--exclude-standard"], root, LIST_FILES_TIMEOUT_SECONDS)
    if untracked is None or untracked.returncode != 0:
        raise GitError("git ls-files failed, so new files cannot be told apart from old ones.")

    for entry in untracked.stdout.split(b"\0"):
        if not entry:
            continue
        relative: str = os.fsdecode(entry)
        full_path: str = os.path.join(root, relative)
        if os.path.isfile(full_path):  # Nested repositories are listed as directories
            lines: int = _count_lines(full_path)
            if lines:
                changed[relative.replace(os.sep, "/")] = set(range(1, lines + 1))

    return changed
