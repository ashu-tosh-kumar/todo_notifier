"""Turns the JSON of one `todonotifier scan` into everything the GitHub Action shows, so the repository is scanned only once.

Run with `python -I render.py render ...` after the scan, and with `python -I render.py check ...` as the last step of the action.

`render` reads the JSON written by `todonotifier scan --format json`, then
    - prints the annotations (`--format github`) to stdout, where GitHub picks up the workflow commands,
    - appends the Markdown digest to the job summary (`$GITHUB_STEP_SUMMARY`),
    - writes the outputs of the action to `$GITHUB_OUTPUT`,
    - with `--comment-file`, writes the body of the sticky pull request comment,
    - with `--report-dir`, writes the HTML reports there.
`check` decides whether the action fails: when the scan or the notification failed, or the `--fail-on` condition is met. It uses
`todonotifier.cli.fail_on_message`, the rule of the command line, so the action and `todonotifier scan --fail-on` never disagree.

It needs the `todonotifier` package (the action installs it) and nothing else. It never prints a webhook URL or a token.
"""

import argparse
import json
import logging
import os
import sys
from typing import Mapping, Optional, Sequence

from todonotifier.cli import fail_on_message
from todonotifier.digest import Digest, build_digest, render_markdown
from todonotifier.formatters import (
    MARKDOWN_TOP_N,
    build_reports,
    format_result,
    write_reports,
)
from todonotifier.git_meta import find_git_root
from todonotifier.log import PACKAGE_LOGGER_NAME
from todonotifier.results import ScanResult
from todonotifier.settings_file import FAIL_ON_CHOICES

MODES: tuple[str, ...] = ("pr", "digest")
# Hidden in the comment: the action finds its own comment again by this text and updates it, so a pull request has one comment, not one per push
COMMENT_MARKER: str = "<!-- todonotifier-action -->"
# GitHub rejects comments of more than 65,536 characters; stay well below it
MAX_COMMENT_CHARS: int = 60000
TRUNCATED_NOTICE: str = "\n\n_The list is cut here because GitHub limits the size of a comment. The full list is in the summary of the workflow run._"
SCAN_EXIT_MEANINGS: dict[int, str] = {
    2: "usage or configuration error (the message is in the log of the scan step)",
    3: "unexpected error (the message is in the log of the scan step)",
}
NOTIFY_EXIT_MEANINGS: dict[int, str] = {
    2: "usage or configuration error, for example a webhook variable that is empty",
    3: "a notification could not be delivered (the notifier is named in the log)",
}


def load_result(path: str) -> ScanResult:
    """Reads the JSON that `todonotifier scan --format json` wrote

    Args:
        path (str): Path of the JSON file

    Returns:
        ScanResult: The scan result
    """
    with open(path, encoding="utf-8") as file:
        return ScanResult.from_dict(json.load(file))


def plural(count: int, singular: str, many: str) -> str:
    """`singular` for 1, else `many`"""
    return singular if count == 1 else many


def build_comment(digest: Digest, markdown: str) -> str:
    """The body of the sticky pull request comment: a headline, the Markdown digest, and the hidden marker that identifies the comment

    Args:
        digest (Digest): The digest of the TODOs on the changed lines
        markdown (str): The Markdown rendering of `digest`

    Returns:
        str: The body, at most `MAX_COMMENT_CHARS` characters (the digest is cut at a line end if it is longer)
    """
    totals = digest.totals
    if totals.open:
        headline: str = (
            f"This PR adds {totals.open} {plural(totals.open, 'TODO', 'TODOs')}: "
            f"{totals.unowned} without an owner, {totals.overdue} overdue, {totals.stale} stale."
        )
    else:
        headline = "This PR adds no TODOs."

    head: str = f"{COMMENT_MARKER}\n{headline}\n\n"
    body: str = head + markdown
    if len(body) <= MAX_COMMENT_CHARS:
        return body

    kept: str = body[: MAX_COMMENT_CHARS - len(TRUNCATED_NOTICE)]
    return kept[: kept.rfind("\n")] + TRUNCATED_NOTICE if "\n" in kept else kept + TRUNCATED_NOTICE


def write_outputs(path: Optional[str], values: Mapping[str, str]) -> None:
    """Appends `name=value` lines to the file `$GITHUB_OUTPUT` (the values are numbers and paths, never free text)

    Args:
        path (str | None): The file, or None to write nothing (run outside of GitHub Actions)
        values (Mapping[str, str]): Output names and values
    """
    if not path:
        return

    with open(path, "a", encoding="utf-8") as file:
        for name, value in values.items():
            file.write(f"{name}={value}\n")


def append_summary(path: Optional[str], text: str) -> None:
    """Appends Markdown to the job summary file `$GITHUB_STEP_SUMMARY`

    Args:
        path (str | None): The file, or None to write nothing (run outside of GitHub Actions)
        text (str): Markdown
    """
    if not path:
        return

    with open(path, "a", encoding="utf-8") as file:
        file.write(text + "\n")


def command_render(args: argparse.Namespace, environ: Mapping[str, str]) -> int:
    """Prints the annotations, writes the job summary, the outputs, the comment body and the HTML reports

    Args:
        args (argparse.Namespace): The parsed `render` arguments
        environ (Mapping[str, str]): The environment, for `GITHUB_OUTPUT` and `GITHUB_STEP_SUMMARY`

    Returns:
        int: 0
    """
    result: ScanResult = load_result(args.input)
    pr_mode: bool = args.mode == "pr"
    # In pr mode the scan used --since, so everything below is about the lines this pull request added or changed
    new_count: Optional[int] = len(result.items) if pr_mode else None

    annotations: str = format_result(result, "github", repo_root=find_git_root(result.root))
    if annotations:
        print(annotations)

    digest: Digest = build_digest(result, top_n=MARKDOWN_TOP_N, new_count=new_count)
    markdown: str = render_markdown(digest)
    append_summary(environ.get("GITHUB_STEP_SUMMARY"), ("_Only TODOs on lines added or changed in this pull request._\n\n" if pr_mode else "") + markdown)

    outputs: dict[str, str] = {
        "total": str(digest.totals.open),
        "overdue": str(digest.totals.overdue),
        "stale": str(digest.totals.stale),
        "new": str(new_count) if pr_mode else "",
    }
    if args.report_dir:
        # The report generators log every table at INFO level, which would fill the log of the workflow run
        package_logger: logging.Logger = logging.getLogger(PACKAGE_LOGGER_NAME)
        previous_level: int = package_logger.level
        package_logger.setLevel(logging.WARNING)
        try:
            write_reports(build_reports(result), args.report_dir)
        finally:
            package_logger.setLevel(previous_level)
        outputs["report-path"] = args.report_dir

    if args.comment_file:
        with open(args.comment_file, "w", encoding="utf-8") as file:
            file.write(build_comment(digest, markdown))

    write_outputs(environ.get("GITHUB_OUTPUT"), outputs)
    return 0


def command_check(args: argparse.Namespace) -> int:
    """Decides whether the action fails, and says why with `::error::` lines

    Args:
        args (argparse.Namespace): The parsed `check` arguments

    Returns:
        int: 1 if the scan or the notification failed or the `--fail-on` condition is met, else 0
    """
    failed: bool = False
    if args.scan_exit:
        meaning: str = SCAN_EXIT_MEANINGS.get(args.scan_exit, "unexpected exit code")
        print(f"::error title=todonotifier scan failed::todonotifier scan exited with {args.scan_exit}: {meaning}")
        failed = True
    if args.notify_exit:
        meaning = NOTIFY_EXIT_MEANINGS.get(args.notify_exit, "unexpected exit code")
        print(f"::error title=todonotifier notify failed::todonotifier notify exited with {args.notify_exit}: {meaning}")
        failed = True
    if args.scan_exit:  # There is no result to check
        return 1

    message: Optional[str] = fail_on_message(load_result(args.input), args.fail_on)
    if message:
        print(f"::error title=fail-on {args.fail_on}::--fail-on {args.fail_on}: {message}")
        failed = True

    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    """Builds the argument parser with the subcommands `render` and `check`"""
    parser = argparse.ArgumentParser(prog="render.py", description="Renders the scan of the todonotifier GitHub Action.")
    commands = parser.add_subparsers(dest="command", required=True)

    render = commands.add_parser("render", help="annotations, job summary, outputs, comment body and HTML reports")
    render.add_argument("--input", required=True, help="the JSON file written by `todonotifier scan --format json`")
    render.add_argument("--mode", choices=MODES, required=True, help="pr (the scan used --since) or digest (full scan)")
    render.add_argument("--report-dir", help="write the HTML reports to this directory and set the report-path output")
    render.add_argument("--comment-file", help="write the body of the sticky pull request comment to this file")

    check = commands.add_parser("check", help="fail on scan or notify errors, or if the --fail-on condition is met")
    check.add_argument("--input", required=True, help="the JSON file written by `todonotifier scan --format json`")
    check.add_argument("--fail-on", choices=FAIL_ON_CHOICES, required=True)
    check.add_argument("--scan-exit", type=int, default=0, help="exit code of `todonotifier scan`")
    check.add_argument("--notify-exit", type=int, default=0, help="exit code of `todonotifier notify`")
    return parser


def main(argv: Optional[Sequence[str]] = None, environ: Optional[Mapping[str, str]] = None) -> int:
    """Runs the script

    Args:
        argv (Sequence[str] | None, optional): Arguments without the program name. Defaults to `sys.argv[1:]`
        environ (Mapping[str, str] | None, optional): The environment. Defaults to `os.environ`

    Returns:
        int: The exit code
    """
    args: argparse.Namespace = build_parser().parse_args(argv)
    if args.command == "render":
        return command_render(args, os.environ if environ is None else environ)

    return command_check(args)


if __name__ == "__main__":
    sys.exit(main())
