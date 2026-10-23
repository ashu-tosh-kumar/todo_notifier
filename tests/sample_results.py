"""Fixed `ScanResult` used by the digest and notifier tests. The TODO contents are asserted on by snapshots in `tests/snapshots/`"""

import json
import os
from datetime import date, datetime, timezone
from typing import Any

from todonotifier.results import ScanResult, TodoItem

TODAY: date = date(2026, 5, 1)
REPO: str = "https://github.com/acme/widgets"
SHA: str = "0123456789abcdef0123456789abcdef01234567"


def _link(file: str, line: int) -> str:
    return f"{REPO}/blob/{SHA}/{file}#L{line}"


def make_item(
    file: str,
    line: int,
    message: str,
    author: "str | None" = None,
    due: "date | None" = None,
    explicit: bool = True,
    linked: bool = True,
) -> TodoItem:
    """Builds an item whose status is computed against `TODAY`"""
    item = TodoItem(
        file=file,
        line=line,
        tag="TODO",
        message=message,
        author=author,
        author_source="annotation" if author else "unknown",
        due_date=due,
        due_source=("explicit" if explicit else "default") if due else "none",
        web_url=_link(file, line) if linked else None,
    )
    item.refresh_status(TODAY)
    return item


def make_scan_result() -> ScanResult:
    """Builds a result of 10 items: 4 overdue, 3 stale, 2 due this week and 1 without a date; 4 of them have no author"""
    items = [
        make_item("src/app.py", 10, "Remove the legacy path", "alice", date(2026, 4, 1)),
        make_item("src/app.py", 99, "Handle <None> & empty input", "alice", date(2026, 4, 21)),
        make_item("src/db.py", 5, "Add an index", "bob", date(2026, 3, 2)),
        make_item("src/util.py", 7, "Delete after the migration", None, date(2026, 4, 30), linked=False),
        make_item("src/old.py", 3, "Rewrite this module", "alice", date(2026, 1, 1), explicit=False),
        make_item("src/old.py", 40, "Split into two functions", None, date(2026, 4, 11), explicit=False),
        make_item("src/api.py", 12, "Paginate the list endpoint", "bob", date(2026, 4, 20), explicit=False),
        make_item("src/api.py", 80, "Cache the lookup", "carol", date(2026, 5, 3)),
        make_item("docs/guide.md", 4, "Document the new flags", None, date(2026, 5, 8)),
        make_item("src/misc.py", 1, "Think about naming"),
    ]
    return ScanResult(
        items=items,
        scanned_files=sorted({item.file for item in items}),
        root="/work/widgets",
        generated_at=datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc),
    )


SNAPSHOT_DIR: str = os.path.join(os.path.dirname(__file__), "snapshots")


def assert_matches_snapshot(test_case: Any, name: str, actual: Any) -> None:
    """Compares `actual` with the file `tests/snapshots/<name>`. Run with UPDATE_SNAPSHOTS=1 to (re)write the file, then review the diff

    Args:
        test_case (unittest.TestCase): Test that reports the failure
        name (str): File name inside `tests/snapshots/`. `.json` files hold `actual` (a JSON structure) with 2-space indentation
        actual (Any): JSON structure for `.json` snapshots, else text
    """
    text: str = json.dumps(actual, indent=2, ensure_ascii=False) + "\n" if name.endswith(".json") else str(actual) + "\n"
    path: str = os.path.join(SNAPSHOT_DIR, name)
    if os.environ.get("UPDATE_SNAPSHOTS"):
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as snapshot_file:
            snapshot_file.write(text)

    with open(path, encoding="utf-8") as snapshot_file:
        test_case.assertEqual(snapshot_file.read(), text)
