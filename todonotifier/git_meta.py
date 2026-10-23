"""This module provides git metadata for scans: who introduced a line and when (`git blame`), and where the repository lives on the web.

`enrich_with_git` is what `scanner.scan` calls when `ScanSettings.use_git_blame` is on. It fills `TodoItem.author`, `created_date`,
default due dates (decision D4) and deep links. Everything degrades gracefully: if `git` is missing, the path is not a repository or a
blame call fails, the items are left as they are and the reason is logged once per scan, never raised.

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

_ZERO_SHA_PATTERN = re.compile(r"^0+$")
_HEADER_PATTERN = re.compile(r"^([0-9a-f]{40}|[0-9a-f]{64}) \d+ (\d+)(?: \d+)?$")
_SCP_LIKE_PATTERN = re.compile(r"^(?:[^@/\s]+@)?([^:/\s]+):(?!//)(.+)$")
_SHA_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


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
        repo_path: str = os.path.relpath(os.path.join(real_scan_root, *item.file.split("/")), root).replace(os.sep, "/")
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
