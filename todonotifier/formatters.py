"""This module turns a `ScanResult` into the output formats of the command line: a table, JSON, GitHub workflow commands, Markdown, SARIF and HTML.

`format_result` is pure: it reads the result and returns text, so it is easy to test and to reuse (for example from the GitHub Action). Statuses
(overdue, stale, due in N days) are recomputed against a reference day, which is the date of `ScanResult.generated_at` unless `today` is given. The
HTML format is the exception, because it produces files: `build_reports` renders the existing summary generators and `write_reports` stores them.

Formats:

- `table`: aligned columns (location, tag, owner, due, message) and a summary line. ANSI colors only if `color=True`.
- `json`: `ScanResult.to_dict()`. It follows `scan_result.schema.json` (`SCHEMA_PATH`), a JSON Schema (draft 2020-12) that ships with the package.
- `github`: one workflow command per TODO (`::error`, `::warning` or `::notice`) so that TODOs show up as annotations on a pull request.
- `markdown`: the digest of `todonotifier.digest`, for a GitHub job summary.
- `sarif`: SARIF 2.1.0 for GitHub code scanning (one rule per tag, one result per TODO).
- `html`: the three built-in reports, see `build_reports`.

Severity, used by `github` and `sarif`: overdue (an explicit date has passed) is an error; stale (a default due date has passed) and due within
7 days are warnings; everything else is a notice. Paths in `github` and `sarif` are relative to the repository root (`repo_root`), because that is
what GitHub resolves them against, even if the scan started in a subdirectory.

TODO messages come from the scanned files, so they are untrusted: control characters (such as terminal escape sequences) are replaced in the table,
and the `github` format escapes every character that could end or start a workflow command.
"""

import json
import os
import re
from datetime import date
from typing import Optional
from urllib.parse import quote

from todonotifier.digest import build_digest, render_markdown, shorten_message
from todonotifier.git_meta import to_repo_path
from todonotifier.results import ScanResult, TodoItem, compute_status
from todonotifier.summary_generators import (
    BaseSummaryGenerator,
    ByModuleSummaryGenerator,
    ExpiredTodosByUserSummaryGenerator,
    UpcomingWeekTodosByUserSummaryGenerator,
)
from todonotifier.utils import store_html

TEXT_FORMATS: tuple[str, ...] = ("table", "json", "github", "markdown", "sarif")
FORMATS: tuple[str, ...] = (*TEXT_FORMATS, "html")
DEFAULT_REPORTS_DIR: str = ".report"
SCHEMA_PATH: str = os.path.join(os.path.dirname(__file__), "schemas", "scan_result.schema.json")
SARIF_SCHEMA_URI: str = "https://json.schemastore.org/sarif-2.1.0.json"
INFORMATION_URI: str = "https://github.com/ashu-tosh-kumar/todo_notifier"

DUE_SOON_DAYS: int = 7
MAX_TABLE_MESSAGE_LENGTH: int = 80
MAX_ANNOTATION_MESSAGE_LENGTH: int = 300
MARKDOWN_TOP_N: int = 25

SEVERITY_ERROR: str = "error"
SEVERITY_WARNING: str = "warning"
SEVERITY_NOTICE: str = "notice"
_SARIF_LEVELS: dict[str, str] = {SEVERITY_ERROR: "error", SEVERITY_WARNING: "warning", SEVERITY_NOTICE: "note"}

_CONTROL_CHARACTERS: re.Pattern = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_TABLE_HEADERS: tuple[str, ...] = ("LOCATION", "TAG", "OWNER", "DUE", "MESSAGE")
_BOLD: str = "1"
_DIM: str = "2"
_RED: str = "31"
_YELLOW: str = "33"


def _clean(text: str) -> str:
    """Replaces control characters (including ESC, which starts terminal escape sequences) with spaces"""
    return _CONTROL_CHARACTERS.sub(" ", text)


def _paint(text: str, code: str, color: bool) -> str:
    """Wraps `text` in an ANSI color sequence if `color` is on"""
    return f"\x1b[{code}m{text}\x1b[0m" if color else text


def _reference_day(result: ScanResult, today: Optional[date]) -> date:
    """The day statuses are computed against: `today`, else the date of `ScanResult.generated_at`"""
    return today or result.generated_at.date()


def _sarif_uri(path: str) -> str:
    """Percent-encodes a path for a SARIF `uri`, which is a URI reference: a `#` or a space in a file name would otherwise end or break it"""
    return quote(path, safe="/")


def _display_path(item: TodoItem, result: ScanResult, repo_root: Optional[str]) -> str:
    """Path of an item relative to the repository root if it is known, else relative to the scan root (as in `TodoItem.file`)"""
    return to_repo_path(item.file, result.root, repo_root) if repo_root else item.file


def _days_until_due(item: TodoItem, today: date) -> Optional[int]:
    """Days from `today` to the due date (negative if it has passed), or None if the item has no due date"""
    return (item.due_date - today).days if item.due_date else None


def _plural(count: int, singular: str, plural: str) -> str:
    """`singular` for 1, else `plural`"""
    return singular if count == 1 else plural


def severity(item: TodoItem, today: date) -> str:
    """Severity of an item: error if overdue, warning if stale or due within 7 days, else notice

    Args:
        item (TodoItem): The item
        today (date): Reference day

    Returns:
        str: "error", "warning" or "notice"
    """
    is_overdue, is_stale, _ = compute_status(item.due_date, item.due_source, today)
    if is_overdue:
        return SEVERITY_ERROR

    days: Optional[int] = _days_until_due(item, today)
    if is_stale or (days is not None and 0 <= days <= DUE_SOON_DAYS):
        return SEVERITY_WARNING

    return SEVERITY_NOTICE


def describe_due(item: TodoItem, today: date) -> str:
    """Describes the due date of an item for a human, e.g. `2026-04-01 overdue 30d`, `2026-04-11 stale 20d`, `2026-05-08 due in 7d` or `-`

    Args:
        item (TodoItem): The item
        today (date): Reference day

    Returns:
        str: The date followed by the state, or "-" if there is no due date
    """
    if item.due_date is None:
        return "-"

    is_overdue, is_stale, days_past_due = compute_status(item.due_date, item.due_source, today)
    if is_overdue:
        state: str = f"overdue {days_past_due}d"
    elif is_stale:
        state = f"stale {days_past_due}d"
    elif item.due_date == today:
        state = "due today"
    elif item.due_date > today:
        state = f"due in {(item.due_date - today).days}d"
    else:  # A passed due date with no source (hand-made items): nothing to compare it with
        state = f"{(today - item.due_date).days}d ago"

    return f"{item.due_date.isoformat()} {state}"


def _count_summary(result: ScanResult, today: date) -> tuple[int, int, int, int]:
    """Counts `(total, overdue, stale, unowned)` of a result against `today`"""
    statuses: list[tuple[bool, bool, int]] = [compute_status(item.due_date, item.due_source, today) for item in result.items]
    return (
        len(result.items),
        sum(1 for is_overdue, _, _ in statuses if is_overdue),
        sum(1 for _, is_stale, _ in statuses if is_stale),
        sum(1 for item in result.items if not item.author),
    )


def _format_table(result: ScanResult, color: bool, repo_root: Optional[str], today: date) -> str:
    """Aligned columns with a summary line, or a friendly line if there is nothing to show"""
    if not result.items:
        if not result.scanned_files:
            return "No files were scanned. Check the path and the file extensions (--ext), and whether .gitignore excludes the files."
        scanned: int = len(result.scanned_files)
        return f"No TODOs found ({scanned} {_plural(scanned, 'file', 'files')} scanned). Nice and tidy!"

    rows: list[tuple[str, str, str, str, str]] = [
        (
            f"{_clean(_display_path(item, result, repo_root))}:{item.line}",
            _clean(item.tag),
            _clean(item.author) if item.author else "-",
            describe_due(item, today),
            shorten_message(_clean(item.message), MAX_TABLE_MESSAGE_LENGTH),
        )
        for item in result.items
    ]
    widths: list[int] = [max(len(row[column]) for row in [_TABLE_HEADERS, *rows]) for column in range(4)]

    lines: list[str] = [_paint("  ".join(header.ljust(widths[column]) if column < 4 else header for column, header in enumerate(_TABLE_HEADERS)), _BOLD, color)]
    for item, row in zip(result.items, rows):
        due_code: Optional[str] = {SEVERITY_ERROR: _RED, SEVERITY_WARNING: _YELLOW}.get(severity(item, today))
        owner_code: Optional[str] = None if item.author else _DIM

        cells: list[str] = [row[0].ljust(widths[0]), row[1].ljust(widths[1]), row[2].ljust(widths[2]), row[3].ljust(widths[3]), row[4]]
        if owner_code:
            cells[2] = _paint(cells[2], owner_code, color)
        if due_code:
            cells[3] = _paint(cells[3], due_code, color)
        lines.append("  ".join(cells).rstrip())

    total, overdue, stale, unowned = _count_summary(result, today)
    lines += [
        "",
        " · ".join(
            [
                f"{total} {_plural(total, 'TODO', 'TODOs')}",
                _paint(f"{overdue} overdue", _RED, color and overdue > 0),
                _paint(f"{stale} stale", _YELLOW, color and stale > 0),
                f"{unowned} unowned",
            ]
        ),
    ]
    return "\n".join(lines)


def _escape_data(text: str) -> str:
    """Escapes the message of a workflow command like GitHub's toolkit does: `%`, carriage return and line feed"""
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _escape_property(text: str) -> str:
    """Escapes a property of a workflow command: like the message, and also `:` and `,` which separate properties"""
    return _escape_data(text).replace(":", "%3A").replace(",", "%2C")


def _item_title(item: TodoItem, today: date) -> str:
    """Short headline of an item, e.g. `TODO overdue by 30d`, `TODO due in 3d` or just `TODO`"""
    is_overdue, is_stale, days_past_due = compute_status(item.due_date, item.due_source, today)
    if is_overdue:
        return f"{item.tag} overdue by {days_past_due}d"
    if is_stale:
        return f"{item.tag} stale by {days_past_due}d"

    days: Optional[int] = _days_until_due(item, today)
    if days is None or days < 0:
        return item.tag
    return f"{item.tag} due today" if days == 0 else f"{item.tag} due in {days}d"


def _item_text(item: TodoItem) -> str:
    """The message of an item with the owner and due date in parentheses, e.g. `Remove the legacy path (@alice, due 2026-04-01)`"""
    details: list[str] = []
    if item.author:
        details.append(f"@{item.author}")
    if item.due_date:
        details.append(f"{'default ' if item.due_source == 'default' else ''}due {item.due_date.isoformat()}")

    text: str = shorten_message(_clean(item.message), MAX_ANNOTATION_MESSAGE_LENGTH) or f"{item.tag} without a description"
    return f"{text} ({_clean(', '.join(details))})" if details else text


def _format_github(result: ScanResult, repo_root: Optional[str], today: date) -> str:
    """One workflow command per item (`::error`, `::warning` or `::notice`) and a summary line"""
    lines: list[str] = []
    for item in result.items:
        properties: str = ",".join(
            [
                f"file={_escape_property(_display_path(item, result, repo_root))}",
                f"line={item.line}",
                f"title={_escape_property(_clean(_item_title(item, today)))}",
            ]
        )
        lines.append(f"::{severity(item, today)} {properties}::{_escape_data(_item_text(item))}")

    total, overdue, stale, unowned = _count_summary(result, today)
    lines.append(f"{total} {_plural(total, 'TODO', 'TODOs')}: {overdue} overdue, {stale} stale, {unowned} unowned")
    return "\n".join(lines)


def _format_sarif(result: ScanResult, repo_root: Optional[str], today: date) -> str:
    """SARIF 2.1.0 with one rule per tag and one result per item"""
    tags: list[str] = sorted({item.tag for item in result.items})
    rules: list[dict] = [
        {
            "id": tag,
            "name": tag,
            "shortDescription": {"text": f"{tag} comment"},
            "fullDescription": {"text": f"A {tag} comment left in the code. Error: its explicit due date has passed. Warning: it is stale or due soon."},
            "helpUri": INFORMATION_URI,
            "defaultConfiguration": {"level": _SARIF_LEVELS[SEVERITY_NOTICE]},
        }
        for tag in tags
    ]

    results: list[dict] = []
    for item in result.items:
        properties: dict = {"dueSource": item.due_source}
        if item.author:
            properties["owner"] = item.author
        if item.due_date:
            properties["dueDate"] = item.due_date.isoformat()
        results.append(
            {
                "ruleId": item.tag,
                "ruleIndex": tags.index(item.tag),
                "level": _SARIF_LEVELS[severity(item, today)],
                "message": {"text": f"{_item_title(item, today)}: {_item_text(item)}"},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": _sarif_uri(_display_path(item, result, repo_root)), "uriBaseId": "%SRCROOT%"},
                            "region": {"startLine": item.line},
                        }
                    }
                ],
                "properties": properties,
            }
        )

    sarif: dict = {
        "$schema": SARIF_SCHEMA_URI,
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "todonotifier", "informationUri": INFORMATION_URI, "rules": rules}}, "results": results}],
    }
    return json.dumps(sarif, indent=2)


def format_result(
    result: ScanResult,
    fmt: str,
    *,
    color: bool = False,
    repo_root: Optional[str] = None,
    today: Optional[date] = None,
    new_count: Optional[int] = None,
) -> str:
    """Formats a scan result as text

    Args:
        result (ScanResult): The result to show
        fmt (str): One of `TEXT_FORMATS`: "table", "json", "github", "markdown" or "sarif". Use `build_reports` for "html"
        color (bool, optional): Whether the table may use ANSI colors. Defaults to False
        repo_root (str | None, optional): Absolute path of the repository root. With it, the paths of the table, `github` and `sarif` are relative to it,
            even if the scan root is a subdirectory. Without it they are relative to the scan root. Defaults to None
        today (date | None, optional): Reference day for the statuses. Defaults to the date of `result.generated_at`
        new_count (int | None, optional): Number of new TODOs (from `--since`), shown in the totals of the Markdown digest. Defaults to None

    Returns:
        str: The formatted result without a trailing newline

    Raises:
        ValueError: Raised if `fmt` is not a text format
    """
    if fmt not in TEXT_FORMATS:
        raise ValueError(f"Cannot format as '{fmt}' text. Text formats: {', '.join(TEXT_FORMATS)} (html output is made of files, see build_reports).")

    reference_day: date = _reference_day(result, today)
    if fmt == "table":
        return _format_table(result, color, repo_root, reference_day)
    if fmt == "json":
        return json.dumps(result.to_dict(), indent=2)
    if fmt == "github":
        return _format_github(result, repo_root, reference_day)
    if fmt == "markdown":
        return render_markdown(build_digest(result, top_n=MARKDOWN_TOP_N, today=reference_day, new_count=new_count))

    return _format_sarif(result, repo_root, reference_day)


def build_reports(result: ScanResult) -> list[tuple[str, str]]:
    """Renders the built-in HTML reports (module-wise, expired by user, upcoming week) of a result

    New generator objects are used on every call, so nothing is carried over between calls. The generators work on the legacy structure
    (`ScanResult.to_legacy()`), where only explicit due dates exist: a TODO with a default due date is shown without a date, so it is never
    "expired" and never "upcoming" (decision D4). The generators compare dates with the real current day, not with `ScanResult.generated_at`.

    Args:
        result (ScanResult): The result to report

    Returns:
        list[tuple[str, str]]: `(report name, html)` pairs, as `BaseNotifier.notify` receives them
    """
    generators: list[BaseSummaryGenerator] = [ByModuleSummaryGenerator(), ExpiredTodosByUserSummaryGenerator(), UpcomingWeekTodosByUserSummaryGenerator()]
    legacy = result.to_legacy()
    for generator in generators:
        generator.generate_summary(legacy)
        generator.generate_html()

    return [(generator.name, generator.html) for generator in generators]


def write_reports(reports: list[tuple[str, str]], directory: str = DEFAULT_REPORTS_DIR) -> list[str]:
    """Writes HTML reports as files, creating the directory if needed

    Args:
        reports (list[tuple[str, str]]): `(report name, html)` pairs, e.g. from `build_reports`
        directory (str, optional): Where to write them. Defaults to ".report"

    Returns:
        list[str]: The paths of the files, in the order of `reports`
    """
    os.makedirs(directory, exist_ok=True)
    return [store_html(html, name, directory) for name, html in reports]
