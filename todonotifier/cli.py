"""This module is the command line interface of TODO Notifier: `todonotifier scan | report | notify | init` (also `python -m todonotifier`).

`main(argv)` returns the exit code and never calls `sys.exit` itself, so it can be tested without a subprocess. The commands share the scan options
of the config file (`todonotifier.settings_file`): flags map to command line overrides, `None` meaning "not given", so the precedence is flags,
config file, built-in command line defaults.

Exit codes:

    0  OK
    1  the `--fail-on` condition was met (for `notify`: it wins over a failed notification)
    2  usage or config error: bad flags, a bad config file, a path that does not exist, an unknown `--since` ref, no notifier configured
    3  unexpected runtime error, or a notifier could not deliver its message (the traceback is shown with `-v`)

Results go to stdout (or to `--output`). Logs and errors go to stderr: warnings by default, errors only with `-q`, debug with `-v`. Only the
`todonotifier` logger is configured, and it is restored when `main` returns.
"""

import argparse
import logging
import os
import sys
import traceback
from contextlib import contextmanager
from datetime import date
from importlib import metadata
from typing import Any, Callable, Iterator, Optional

from todonotifier.formatters import (
    DEFAULT_REPORTS_DIR,
    FORMATS,
    build_reports,
    format_result,
    write_reports,
)
from todonotifier.git_meta import GitError, changed_lines, find_git_root, to_repo_path
from todonotifier.log import PACKAGE_LOGGER_NAME
from todonotifier.notifier import (
    BaseNotifier,
    DigestNotifier,
    NotificationError,
    NotifierConfigError,
    build_notifiers,
)
from todonotifier.results import ScanResult
from todonotifier.scanner import ScanException, scan
from todonotifier.settings_file import (
    DOT_FILE_NAME,
    FAIL_ON_CHOICES,
    PYPROJECT_FILE_NAME,
    ConfigError,
    ProjectConfig,
    has_pyproject_table,
    resolve_project_config,
)

EXIT_OK: int = 0
EXIT_FAIL_ON: int = 1
EXIT_USAGE: int = 2
EXIT_ERROR: int = 3

README_URL: str = "https://github.com/ashu-tosh-kumar/todo_notifier#readme"
NOTIFICATIONS_URL: str = "https://github.com/ashu-tosh-kumar/todo_notifier#notifications"

EXIT_CODES_HELP: str = """\
exit codes:
  0  OK
  1  the --fail-on condition was met
  2  usage or config error (bad flag, bad config file, missing path, unknown --since ref, no notifier configured)
  3  unexpected runtime error, or a notification could not be delivered (add -v for the traceback)

Results go to stdout (or --output), logs and errors to stderr. Docs: """ + README_URL

_STARTER_HEADER: str = """\
# TODO Notifier configuration. Docs: {url}
# Every key is optional. The values shown are the defaults of the command line, so `todonotifier scan .` works without any of this.
# Uncomment a line to change it.
"""

_STARTER_BODY: str = """\
# Files and directories to scan, relative to this file.
# paths = ["."]
# File extensions without the dot. "common" covers py, js, ts, java, go, rb, rs, c, cpp, sh, sql, yaml, md and more.
# extensions = "common"
# Tags to look for.
# tags = ["TODO", "FIXME", "HACK", "XXX"]
# Match tags case insensitively.
# ignore_case = false
# Count a tag only inside a comment, and skip the files that .gitignore excludes.
# require_comment = true
# respect_gitignore = true
# Fill authors and ages from git blame. An undated TODO turns "stale" this many days after it was added (0 turns this off).
# use_git_blame = true
# default_due_days = 90
# When `todonotifier scan` exits with 1: "none", "expired" (a {{date}} has passed), "stale" (also default due dates) or "any".
# fail_on = "none"

# Exclusions are added to the built-in ones.
# [{prefix}exclude_dirs]
# name = ["generated", "vendor"]

# Maps git author emails to the handle shown in reports.
# [{prefix}authors]
# "jane@example.com" = "jane"

# Notifications for `todonotifier notify`. A config file never holds a secret: each *_env key is the NAME of an environment variable that does.
# [{prefix}notify.slack]
# webhook_env = "TODO_SLACK_WEBHOOK"
# max_items = 10

# [{prefix}notify.teams]
# webhook_env = "TODO_TEAMS_WEBHOOK"

# [{prefix}notify.webhook]
# url_env = "TODO_WEBHOOK_URL"

# [{prefix}notify.email]
# smtp_host = "smtp.example.com"
# sender = "todo@example.com"
# recipients = ["team@example.com"]
# password_env = "TODO_SMTP_PASSWORD"
# starttls = true
"""


class CliError(Exception):
    """Raised for a problem the user can fix, such as an unwritable output file. `main` shows the message and returns exit code 2"""


class _StderrHandler(logging.Handler):
    """Writes log records to whatever `sys.stderr` is at the time, so the handler survives stream redirection"""

    def emit(self, record: logging.LogRecord) -> None:
        """Writes the formatted record to stderr"""
        try:
            sys.stderr.write(self.format(record) + "\n")
        except Exception:  # pragma: no cover - only if stderr itself is broken, as logging.Handler.handleError expects
            self.handleError(record)


@contextmanager
def _logging_configured(quiet: bool, verbose: bool) -> Iterator[None]:
    """Sets up the `todonotifier` logger for the command line (stderr, WARNING; ERROR with `quiet`, DEBUG with `verbose`) and restores it afterwards"""
    logger: logging.Logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    previous_handlers: list[logging.Handler] = list(logger.handlers)
    previous_level: int = logger.level
    handler: _StderrHandler = _StderrHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s" if verbose else "%(levelname)s: %(message)s"),
    )
    logger.handlers = [handler]
    logger.setLevel(logging.ERROR if quiet else logging.DEBUG if verbose else logging.WARNING)
    try:
        yield
    finally:
        logger.handlers = previous_handlers
        logger.setLevel(previous_level)


def get_version() -> str:
    """Version of the installed package, or "unknown" if it is not installed (for example when run from a source checkout)"""
    try:
        return metadata.version("todonotifier")
    except metadata.PackageNotFoundError:
        return "unknown"


def _today() -> date:
    """The current local date, a function so tests can fix the day"""
    return date.today()


def _comma_list(value: str) -> list[str]:
    """Argument type: a comma separated list such as `TODO,FIXME` (blanks around the items are dropped)"""
    items: list[str] = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("expected a comma separated list such as TODO,FIXME")
    return items


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    """Adds the options that scan, report and notify have in common"""
    scanning = parser.add_argument_group("what to scan")
    scanning.add_argument("paths", nargs="*", metavar="PATH", help="files and directories to scan (default: the 'paths' of the config file, else .)")
    scanning.add_argument("--config", metavar="PATH", help="config file to use instead of looking for .todonotifier.toml or pyproject.toml")
    scanning.add_argument("--tags", type=_comma_list, metavar="TODO,FIXME", help="comma separated tags to look for (default: TODO,FIXME,HACK,XXX)")
    scanning.add_argument(
        "--ext", type=_comma_list, metavar="py,js", help="comma separated file extensions; 'common' is the preset of common languages (default)"
    )
    scanning.add_argument("--ignore-case", action="store_const", const=True, default=None, help="match tags case insensitively (todo, Todo)")
    scanning.add_argument("--no-require-comment", action="store_const", const=False, default=None, help="also report tags that are not in a comment")
    scanning.add_argument("--no-gitignore", action="store_const", const=False, default=None, help="also scan files that .gitignore excludes")
    scanning.add_argument("--no-blame", action="store_const", const=False, default=None, help="do not run git blame (no authors, ages or default due dates)")
    scanning.add_argument("--default-due-days", type=int, metavar="N", help="an undated TODO turns stale N days after it was added; 0 disables (default: 90)")
    scanning.add_argument("--since", metavar="GIT_REF", help="only report TODOs on lines added or changed since GIT_REF, e.g. HEAD~1 or origin/main")
    scanning.add_argument(
        "--fail-on", choices=FAIL_ON_CHOICES, help="exit with 1 if such a TODO exists: expired (explicit date passed), stale (also default dates), any"
    )

    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument("-q", "--quiet", action="store_true", help="show errors only")
    verbosity.add_argument("-v", "--verbose", action="store_true", help="show debug logs, and the traceback of unexpected errors")


def _add_output_options(
    parser: argparse.ArgumentParser, default_format: Optional[str], output_help: str, output_names: tuple[str, ...] = ("--output",)
) -> None:
    """Adds `--format` and `--output` (and `--out` for report)"""
    default_help: str = f" (default: {default_format})" if default_format else " (default: nothing is printed)"
    group = parser.add_argument_group("output")
    group.add_argument("--format", choices=FORMATS, default=default_format, help="output format: " + ", ".join(FORMATS) + default_help)
    group.add_argument(*output_names, dest="output", metavar="FILE", help=output_help)


def build_parser() -> argparse.ArgumentParser:
    """Builds the argument parser of the command line

    Returns:
        argparse.ArgumentParser: The parser, with the subcommands scan, report, notify and init
    """
    raw = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(
        prog="todonotifier",
        description="Find TODO comments in your code, see who owns them and which are overdue, and get notified.",
        epilog="examples:\n  todonotifier scan .\n  todonotifier scan . --fail-on expired\n  todonotifier scan src/ --format github\n\n" + EXIT_CODES_HELP,
        formatter_class=raw,
    )
    parser.add_argument("--version", action="version", version=f"todonotifier {get_version()}")
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    scan_parser = subparsers.add_parser(
        "scan",
        help="scan and print the TODOs",
        description="Scan files and directories for TODOs and print them. With no config, all common languages are scanned.",
        epilog=EXIT_CODES_HELP,
        formatter_class=raw,
    )
    _add_common_options(scan_parser)
    _add_output_options(scan_parser, "table", "write the result to FILE instead of stdout (for html: the directory for the report files)")
    scan_parser.set_defaults(handler=_command_scan)

    report_parser = subparsers.add_parser(
        "report",
        help="write the HTML reports",
        description="Scan and write the HTML reports (module-wise, expired by user, upcoming week) to a directory. Same as 'scan --format html'.",
        epilog=EXIT_CODES_HELP,
        formatter_class=raw,
    )
    _add_common_options(report_parser)
    _add_output_options(
        report_parser,
        "html",
        f"directory for the report files (default: {DEFAULT_REPORTS_DIR}); with another --format, the file to write",
        ("--out", "--output"),
    )
    report_parser.set_defaults(handler=_command_scan)

    notify_parser = subparsers.add_parser(
        "notify",
        help="send the digest to the notifiers of the config file",
        description="Scan, then send the result to every notifier in the [notify.<name>] tables of the config file (slack, teams, webhook, email). "
        "All notifiers are tried; each failure is printed.",
        epilog=EXIT_CODES_HELP,
        formatter_class=raw,
    )
    _add_common_options(notify_parser)
    _add_output_options(notify_parser, None, "write the result to FILE instead of stdout (only with --format)")
    notify_parser.set_defaults(handler=_command_notify)

    init_parser = subparsers.add_parser(
        "init",
        help="create a starter config",
        description=f"Append a commented [tool.todonotifier] section to {PYPROJECT_FILE_NAME} if it exists, else create {DOT_FILE_NAME}. "
        "Never overwrites anything.",
        epilog=EXIT_CODES_HELP,
        formatter_class=raw,
    )
    where = init_parser.add_mutually_exclusive_group()
    where.add_argument("--pyproject", action="store_true", help=f"add the section to {PYPROJECT_FILE_NAME}")
    where.add_argument("--standalone", action="store_true", help=f"create {DOT_FILE_NAME}")
    verbosity = init_parser.add_mutually_exclusive_group()
    verbosity.add_argument("-q", "--quiet", action="store_true", help="show errors only")
    verbosity.add_argument("-v", "--verbose", action="store_true", help="show debug logs, and the traceback of unexpected errors")
    init_parser.set_defaults(handler=_command_init)

    return parser


def _error(message: str) -> None:
    """Prints a one-line error to stderr"""
    print(f"todonotifier: error: {message}", file=sys.stderr)


def _write_stdout(text: str) -> None:
    """Prints text to stdout. Characters that the terminal cannot show are replaced instead of crashing"""
    try:
        print(text)
    except UnicodeEncodeError:
        encoding: str = sys.stdout.encoding or "ascii"
        print(text.encode(encoding, errors="replace").decode(encoding))


def _use_color(output: Optional[str]) -> bool:
    """Whether to color the table: stdout is a terminal, NO_COLOR is not set (https://no-color.org), TERM is not "dumb" and there is no `--output`"""
    return output is None and sys.stdout.isatty() and not os.environ.get("NO_COLOR") and os.environ.get("TERM") != "dumb"


def _plural(count: int, singular: str, plural: str) -> str:
    """`singular` for 1, else `plural`"""
    return singular if count == 1 else plural


def _load_project(args: argparse.Namespace) -> ProjectConfig:
    """Merges the flags with the config file and the defaults"""
    overrides: dict[str, Any] = {
        "tags": args.tags,
        "extensions": args.ext,
        "ignore_case": args.ignore_case,
        "require_comment": args.no_require_comment,
        "respect_gitignore": args.no_gitignore,
        "use_git_blame": args.no_blame,
        "default_due_days": args.default_due_days,
        "fail_on": args.fail_on,
        "paths": args.paths or None,
    }
    return resolve_project_config(overrides, args.config, start=args.paths[0] if args.paths else ".")


def _only_changed_lines(result: ScanResult, ref: str) -> ScanResult:
    """Keeps the items on lines that were added or changed since `ref`

    Raises:
        CliError: If the scan root is not in a git repository, or git cannot compare with `ref`
    """
    repo_root: Optional[str] = find_git_root(result.root)
    if repo_root is None:
        raise CliError(f"--since needs a git repository, but {result.root} is not inside one (or the git executable is missing).")

    try:
        changed: dict[str, set[int]] = changed_lines(repo_root, ref)
    except GitError as error:
        raise CliError(f"--since {ref}: {error}") from None

    kept = [item for item in result.items if item.line in changed.get(to_repo_path(item.file, result.root, repo_root), ())]
    return ScanResult(items=kept, scanned_files=result.scanned_files, root=result.root, generated_at=result.generated_at, schema_version=result.schema_version)


def _scan_project(args: argparse.Namespace, project: ProjectConfig, today: date) -> ScanResult:
    """Scans, and applies `--since`"""
    result: ScanResult = scan(project.settings, today=today)
    return _only_changed_lines(result, args.since) if args.since else result


def _show_result(args: argparse.Namespace, result: ScanResult, today: date) -> None:
    """Prints the result in the chosen format to stdout, writes it to `--output`, or writes the HTML reports"""
    fmt: str = args.format
    if fmt == "html":
        directory: str = args.output or DEFAULT_REPORTS_DIR
        try:
            paths: list[str] = write_reports(build_reports(result), directory)
        except OSError as error:
            raise CliError(f"Cannot write the reports to {directory}: {error.strerror or error}") from error
        for path in paths:
            _write_stdout(path)
        return

    repo_root: Optional[str] = find_git_root(result.root) if fmt in ("table", "github", "sarif") else None
    text: str = format_result(
        result,
        fmt,
        color=_use_color(args.output),
        repo_root=repo_root,
        today=today,
        new_count=len(result.items) if args.since else None,
    )
    if not args.output:
        _write_stdout(text)
        return

    try:
        directory = os.path.dirname(os.path.abspath(args.output))
        os.makedirs(directory, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as file:
            file.write(text + "\n")
    except OSError as error:
        raise CliError(f"Cannot write to {args.output}: {error.strerror or error}") from error
    if not args.quiet:
        print(f"Wrote the {fmt} output to {args.output}", file=sys.stderr)


def _fail_on_message(result: ScanResult, fail_on: str) -> Optional[str]:
    """Explains why `--fail-on` is met, or returns None if it is not"""
    overdue: int = len(result.overdue())
    stale: int = len(result.stale())
    total: int = len(result.items)
    if fail_on == "expired" and overdue:
        return f"{overdue} overdue {_plural(overdue, 'TODO', 'TODOs')} (an explicit date has passed)"
    if fail_on == "stale" and overdue + stale:
        return f"{overdue} overdue and {stale} stale {_plural(overdue + stale, 'TODO', 'TODOs')}"
    if fail_on == "any" and total:
        return f"{total} {_plural(total, 'TODO', 'TODOs')} found"

    return None


def _exit_code_for(result: ScanResult, fail_on: str) -> int:
    """`EXIT_FAIL_ON` (with a line on stderr saying why) if the `--fail-on` condition is met, else `EXIT_OK`"""
    message: Optional[str] = _fail_on_message(result, fail_on)
    if message is None:
        return EXIT_OK

    print(f"todonotifier: --fail-on {fail_on}: {message}", file=sys.stderr)
    return EXIT_FAIL_ON


def _command_scan(args: argparse.Namespace) -> int:
    """`scan` and `report`: scan, show the result, and decide the exit code"""
    project: ProjectConfig = _load_project(args)
    today: date = _today()
    result: ScanResult = _scan_project(args, project, today)
    _show_result(args, result, today)

    return _exit_code_for(result, project.fail_on)


def _explain_no_notifiers(project: ProjectConfig) -> None:
    """Prints how to configure a notifier"""
    reason: str = (
        "All notifiers in the config file are disabled (enabled = false)."
        if project.notify
        else f"No notifiers are configured{f' in {project.source}' if project.source else ' (there is no config file)'}."
    )
    print(
        f"todonotifier: {reason}\n"
        f'Add a notifier table to your config, for example [tool.todonotifier.notify.slack] with webhook_env = "TODO_SLACK_WEBHOOK" '
        f"(or teams, webhook, email; in {DOT_FILE_NAME} drop the 'tool.todonotifier.' prefix).\n"
        f"Run 'todonotifier init' for a starter config. See {NOTIFICATIONS_URL}",
        file=sys.stderr,
    )


def _send(notifier: BaseNotifier, result: ScanResult, reports: list[tuple[str, str]], verbose: bool) -> Optional[str]:
    """Sends to one notifier and returns the error text, or None if it worked. Secrets are never in the text: only `NotificationError` messages are shown"""
    try:
        notifier.notify_result(result, reports)
    except NotificationError as error:
        return str(error)
    except Exception as error:  # One broken notifier must not stop the others
        if verbose:
            traceback.print_exc()
        return f"unexpected {type(error).__name__}"

    return None


def _command_notify(args: argparse.Namespace) -> int:
    """`notify`: scan, then try every configured notifier"""
    project: ProjectConfig = _load_project(args)
    notifiers: list[BaseNotifier] = build_notifiers(project.notify)
    if not notifiers:
        _explain_no_notifiers(project)
        return EXIT_USAGE

    today: date = _today()
    result: ScanResult = _scan_project(args, project, today)
    if args.format:
        _show_result(args, result, today)

    if args.since:
        for notifier in notifiers:
            if isinstance(notifier, DigestNotifier):
                notifier.new_count = len(result.items)

    reports: list[tuple[str, str]] = build_reports(result)
    failures: int = 0
    for notifier in notifiers:
        name: str = type(notifier).__name__
        error: Optional[str] = _send(notifier, result, reports, args.verbose)
        if error is None:
            if not args.quiet:
                print(f"Notified {name}", file=sys.stderr)
        else:
            failures += 1
            print(f"todonotifier: {name} failed: {error}", file=sys.stderr)

    exit_code: int = _exit_code_for(result, project.fail_on)
    if exit_code == EXIT_OK and failures:
        return EXIT_ERROR

    return exit_code


def starter_config(pyproject: bool) -> str:
    """The commented starter config written by `todonotifier init`

    Args:
        pyproject (bool): True for the text to append to `pyproject.toml` (a `[tool.todonotifier]` table), False for `.todonotifier.toml` (top level keys)

    Returns:
        str: TOML text that loads cleanly, with every option as a comment
    """
    prefix: str = "tool.todonotifier." if pyproject else ""
    header: str = _STARTER_HEADER.format(url=README_URL) + ("[tool.todonotifier]\n" if pyproject else "")
    return header + _STARTER_BODY.format(prefix=prefix)


def _append_text(path: str, text: str) -> None:
    """Appends `text` to a file, after a blank line, making sure the existing last line ends with a newline"""
    with open(path, "rb") as file:
        content: bytes = file.read()

    separator: str = "" if not content else "\n" if content.endswith(b"\n") else "\n\n"
    with open(path, "a", encoding="utf-8", newline="") as file:
        file.write(separator + text)


def _command_init(args: argparse.Namespace) -> int:
    """`init`: append the starter section to pyproject.toml or create .todonotifier.toml, never overwriting"""
    pyproject_path: str = os.path.join(os.getcwd(), PYPROJECT_FILE_NAME)
    standalone_path: str = os.path.join(os.getcwd(), DOT_FILE_NAME)
    if args.pyproject:
        standalone: bool = False
    elif args.standalone:
        standalone = True
    else:
        standalone = os.path.exists(standalone_path) or not os.path.exists(pyproject_path)

    try:
        if standalone:
            if os.path.exists(standalone_path):
                print(f"{DOT_FILE_NAME} already exists, so nothing was changed.")
                return EXIT_OK
            with open(standalone_path, "x", encoding="utf-8", newline="") as file:
                file.write(starter_config(pyproject=False))
            print(f"Created {DOT_FILE_NAME}. Every option in it is commented out: edit it to change the defaults.")
        else:
            if not os.path.isfile(pyproject_path):
                raise CliError(f"There is no {PYPROJECT_FILE_NAME} in this directory. Run 'todonotifier init --standalone' to create {DOT_FILE_NAME} instead.")
            if has_pyproject_table(pyproject_path):
                print(f"{PYPROJECT_FILE_NAME} already has a [tool.todonotifier] section, so nothing was changed.")
                return EXIT_OK
            _append_text(pyproject_path, starter_config(pyproject=True))
            print(f"Added a commented [tool.todonotifier] section to {PYPROJECT_FILE_NAME}.")
    except OSError as error:
        raise CliError(f"Cannot write the config file: {error.strerror or error}") from error

    print("Next: run 'todonotifier scan .' to see your TODOs, and see the README to set up notifications: " + README_URL)
    return EXIT_OK


def _exit_status(request: SystemExit) -> int:
    """Converts the `SystemExit` that argparse raises (for --help, --version and usage errors) to an exit code"""
    code: Any = request.code
    if code is None:
        return EXIT_OK
    return code if isinstance(code, int) else EXIT_USAGE


def main(argv: Optional[list[str]] = None) -> int:
    """Runs the command line

    Args:
        argv (list[str] | None, optional): Arguments without the program name. Defaults to `sys.argv[1:]`

    Returns:
        int: The exit code: 0 OK, 1 the `--fail-on` condition was met, 2 usage or config error, 3 unexpected runtime error. Never raises and never calls
            `sys.exit`
    """
    parser: argparse.ArgumentParser = build_parser()
    try:
        args: argparse.Namespace = parser.parse_args(argv)
    except SystemExit as request:  # Raised by argparse for --help, --version and usage errors (code 2)
        return _exit_status(request)

    if args.command is None:
        parser.print_help(sys.stderr)
        return EXIT_USAGE

    handler: Callable[[argparse.Namespace], int] = args.handler
    with _logging_configured(args.quiet, args.verbose):
        try:
            return handler(args)
        except (CliError, ConfigError, NotifierConfigError, ScanException) as error:
            _error(str(error))
            return EXIT_USAGE
        except Exception as error:
            first_line: str = (str(error).splitlines() or [""])[0]
            _error(f"unexpected {type(error).__name__}{f': {first_line}' if first_line else ''}")
            if args.verbose:
                traceback.print_exc()
            else:
                print("Run again with -v for the full traceback.", file=sys.stderr)
            return EXIT_ERROR
