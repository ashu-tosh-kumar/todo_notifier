"""This module defines the structured, serializable result of a scan: `TodoItem` and `ScanResult`.

Unlike the legacy `models.TODO`, these classes carry everything a consumer needs (author, due date and where it came from,
status, deep link), convert to and from plain dictionaries (`to_dict` / `from_dict`, dates as ISO strings) and therefore
survive a JSON round trip unchanged. `TodoItem.from_legacy` and `TodoItem.to_legacy` bridge to `models.TODO`, so the existing
summary generators keep working.
"""

import os
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Optional
from urllib.parse import quote

from dateutil import parser

from todonotifier.constants import DEFAULT_COMPLETION_DATE, UNKNOWN_USER_NAME
from todonotifier.models import POSITION, TODO, USER

SCHEMA_VERSION = 1

AUTHOR_SOURCE_ANNOTATION = "annotation"
AUTHOR_SOURCE_GIT_BLAME = "git_blame"
AUTHOR_SOURCE_UNKNOWN = "unknown"

DUE_SOURCE_EXPLICIT = "explicit"
DUE_SOURCE_DEFAULT = "default"
DUE_SOURCE_NONE = "none"

DEFAULT_TAG = "TODO"

_LEGACY_NO_DATE: date = parser.parse(DEFAULT_COMPLETION_DATE).date()


def build_web_url(repo_web_url: Optional[str], commit_sha: Optional[str], file: str, line: int) -> Optional[str]:
    """Builds a deep link to a line of a file at a commit, in the GitHub style `{repo_web_url}/blob/{commit_sha}/{file}#L{line}`

    Args:
        repo_web_url (str | None): Web URL of the repository, e.g. https://github.com/org/repo
        commit_sha (str | None): Commit the file is at
        file (str): POSIX path of the file relative to the repository root
        line (int): 1-indexed line number

    Returns:
        str | None: The deep link, or None if `repo_web_url` or `commit_sha` is not set
    """
    if not repo_web_url or not commit_sha:
        return None

    return f"{repo_web_url.rstrip('/')}/blob/{commit_sha}/{quote(file)}#L{line}"


def compute_status(due_date: Optional[date], due_source: str, today: date) -> tuple[bool, bool, int]:
    """Computes the status of an item against a reference day

    An item is "overdue" if its explicit due date has passed and "stale" if its default (computed) due date has passed.

    Args:
        due_date (date | None): Due date of the item
        due_source (str): One of "explicit", "default" or "none"
        today (date): Reference day

    Returns:
        tuple[bool, bool, int]: `(is_overdue, is_stale, days_past_due)`. `days_past_due` is 0 unless the item is overdue or stale
    """
    if due_date is None or due_source == DUE_SOURCE_NONE or today <= due_date:
        return False, False, 0

    return due_source == DUE_SOURCE_EXPLICIT, due_source == DUE_SOURCE_DEFAULT, (today - due_date).days


def _parse_date(value: Optional[str]) -> Optional[date]:
    """Parses an ISO date string

    Args:
        value (str | None): String in the format YYYY-MM-DD or None

    Returns:
        date | None: Parsed date, or None if `value` is None
    """
    return date.fromisoformat(value) if value else None


@dataclass
class TodoItem:
    """A single TODO found by a scan

    Attributes:
        file (str): POSIX path of the file, relative to the scan root
        line (int): 1-indexed line number
        tag (str): Tag that was matched, e.g. "TODO"
        message (str): Text after the tag, date and user
        author (str | None): Person responsible, or None if unknown
        author_source (str): Where `author` came from: "annotation", "git_blame" or "unknown"
        due_date (date | None): Due date, or None if there is none
        due_source (str): Where `due_date` came from: "explicit" (written in the comment), "default" (computed) or "none"
        created_date (date | None): Date the line was introduced (filled from git blame)
        is_overdue (bool): Whether the explicit due date has passed
        is_stale (bool): Whether the default due date has passed
        days_past_due (int): Days since the due date if overdue or stale, else 0
        web_url (str | None): Deep link to the line in the repository's web UI
    """

    file: str
    line: int
    tag: str
    message: str
    author: Optional[str] = None
    author_source: str = AUTHOR_SOURCE_UNKNOWN
    due_date: Optional[date] = None
    due_source: str = DUE_SOURCE_NONE
    created_date: Optional[date] = None
    is_overdue: bool = False
    is_stale: bool = False
    days_past_due: int = 0
    web_url: Optional[str] = None

    def refresh_status(self, today: date) -> None:
        """Recomputes `is_overdue`, `is_stale` and `days_past_due` from the due date. Call it after changing `due_date` or `due_source`

        Args:
            today (date): Reference day
        """
        self.is_overdue, self.is_stale, self.days_past_due = compute_status(self.due_date, self.due_source, today)

    def to_dict(self) -> dict[str, Any]:
        """Converts the item to a JSON friendly dictionary, with dates as ISO strings

        Returns:
            dict[str, Any]: Dictionary representation of the item
        """
        data: dict[str, Any] = asdict(self)
        data["due_date"] = self.due_date.isoformat() if self.due_date else None
        data["created_date"] = self.created_date.isoformat() if self.created_date else None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TodoItem":
        """Builds an item from the dictionary produced by `to_dict`. Optional keys may be missing

        Args:
            data (dict[str, Any]): Dictionary with at least `file`, `line` and `message`

        Returns:
            TodoItem: The item
        """
        return cls(
            file=data["file"],
            line=data["line"],
            tag=data.get("tag", DEFAULT_TAG),
            message=data["message"],
            author=data.get("author"),
            author_source=data.get("author_source", AUTHOR_SOURCE_UNKNOWN),
            due_date=_parse_date(data.get("due_date")),
            due_source=data.get("due_source", DUE_SOURCE_NONE),
            created_date=_parse_date(data.get("created_date")),
            is_overdue=data.get("is_overdue", False),
            is_stale=data.get("is_stale", False),
            days_past_due=data.get("days_past_due", 0),
            web_url=data.get("web_url"),
        )

    @classmethod
    def from_legacy(
        cls,
        todo: TODO,
        today: Optional[date] = None,
        tag: str = DEFAULT_TAG,
        repo_web_url: Optional[str] = None,
        commit_sha: Optional[str] = None,
    ) -> "TodoItem":
        """Converts a legacy `models.TODO`

        The legacy "no date" sentinel (`constants.DEFAULT_COMPLETION_DATE`) becomes `due_date=None` with `due_source="none"`, and the
        legacy unknown user (`constants.UNKNOWN_USER_NAME`) becomes `author=None` with `author_source="unknown"`.

        Args:
            todo (TODO): Legacy object
            today (date | None, optional): Reference day for the status fields. Defaults to the current local date
            tag (str, optional): Tag that was matched. Defaults to "TODO"
            repo_web_url (str | None, optional): Repository web URL, used with `commit_sha` to build `web_url`. Defaults to None
            commit_sha (str | None, optional): Commit of the scanned tree, used with `repo_web_url` to build `web_url`. Defaults to None

        Returns:
            TodoItem: The item, with `file` converted to a POSIX path
        """
        user_name: str = todo.user.user_name
        has_author: bool = bool(user_name) and user_name != UNKNOWN_USER_NAME
        has_due_date: bool = todo.completion_date != _LEGACY_NO_DATE
        file: str = todo.module.replace(os.sep, "/")

        item = cls(
            file=file,
            line=todo.position.line_no,
            tag=tag,
            message=todo.msg,
            author=user_name if has_author else None,
            author_source=AUTHOR_SOURCE_ANNOTATION if has_author else AUTHOR_SOURCE_UNKNOWN,
            due_date=todo.completion_date if has_due_date else None,
            due_source=DUE_SOURCE_EXPLICIT if has_due_date else DUE_SOURCE_NONE,
            web_url=build_web_url(repo_web_url, commit_sha, file, todo.position.line_no),
        )
        item.refresh_status(today or date.today())
        return item

    def to_legacy(self) -> TODO:
        """Converts the item to a legacy `models.TODO`, so the existing summary generators can consume it

        A missing due date becomes the legacy sentinel (`constants.DEFAULT_COMPLETION_DATE`) and a missing author the legacy unknown user.

        Returns:
            TODO: Legacy object
        """
        return TODO(
            msg=self.message,
            user=USER(self.author or UNKNOWN_USER_NAME),
            completion_date_str=self.due_date.isoformat() if self.due_date else "",
            module=self.file,
            position=POSITION(self.line),
        )


@dataclass
class ScanResult:
    """The result of a scan

    Attributes:
        items (list[TodoItem]): TODOs found, ordered by file and line
        scanned_files (list[str]): POSIX paths, relative to `root`, of every file that was scanned (including files without TODOs)
        root (str): Absolute path the item paths are relative to
        generated_at (datetime): When the result was generated (timezone aware). Its date is the reference day of the status fields
        schema_version (int): Version of the serialized format, bumped on incompatible changes
    """

    items: list[TodoItem] = field(default_factory=list)
    scanned_files: list[str] = field(default_factory=list)
    root: str = ""
    generated_at: datetime = field(default_factory=lambda: datetime.now().astimezone())
    schema_version: int = SCHEMA_VERSION

    def overdue(self) -> list[TodoItem]:
        """Items whose explicit due date has passed

        Returns:
            list[TodoItem]: Overdue items
        """
        return [item for item in self.items if item.is_overdue]

    def stale(self) -> list[TodoItem]:
        """Items whose default (computed) due date has passed

        Returns:
            list[TodoItem]: Stale items
        """
        return [item for item in self.items if item.is_stale]

    def due_within(self, days: int, today: Optional[date] = None) -> list[TodoItem]:
        """Items that are not past due and fall due within the next `days` days (inclusive)

        Args:
            days (int): Length of the window in days
            today (date | None, optional): Reference day. Defaults to the date of `generated_at`

        Returns:
            list[TodoItem]: Items with a due date from `today` up to `days` days after it
        """
        reference_day: date = today or self.generated_at.date()
        return [item for item in self.items if item.due_date is not None and 0 <= (item.due_date - reference_day).days <= days]

    def by_author(self) -> dict[str, list[TodoItem]]:
        """Groups items by author. Items without an author are grouped under `constants.UNKNOWN_USER_NAME`

        Returns:
            dict[str, list[TodoItem]]: Items per author
        """
        grouped: dict[str, list[TodoItem]] = defaultdict(list)
        for item in self.items:
            grouped[item.author or UNKNOWN_USER_NAME].append(item)

        return dict(grouped)

    def by_file(self) -> dict[str, list[TodoItem]]:
        """Groups items by file

        Returns:
            dict[str, list[TodoItem]]: Items per file path
        """
        grouped: dict[str, list[TodoItem]] = defaultdict(list)
        for item in self.items:
            grouped[item.file].append(item)

        return dict(grouped)

    def to_legacy(self) -> dict[str, list[TODO]]:
        """Converts the items to the structure the legacy summary generators consume

        Returns:
            dict[str, list[TODO]]: Key-value pair where key is the path of a scanned file and value is the list of TODO objects in that file
        """
        legacy: dict[str, list[TODO]] = {file: [] for file in self.scanned_files}
        for item in self.items:
            legacy.setdefault(item.file, []).append(item.to_legacy())

        return legacy

    def to_dict(self) -> dict[str, Any]:
        """Converts the result to a JSON friendly dictionary, with dates as ISO strings

        Returns:
            dict[str, Any]: Dictionary representation of the result
        """
        return {
            "schema_version": self.schema_version,
            "root": self.root,
            "generated_at": self.generated_at.isoformat(),
            "scanned_files": list(self.scanned_files),
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScanResult":
        """Builds a result from the dictionary produced by `to_dict`. Optional keys may be missing

        Args:
            data (dict[str, Any]): Dictionary representation of a result

        Returns:
            ScanResult: The result

        Raises:
            ValueError: Raised if `data` was written with a newer, unsupported `schema_version`
        """
        schema_version: int = data.get("schema_version", SCHEMA_VERSION)
        if schema_version > SCHEMA_VERSION:
            raise ValueError(f"Unsupported schema_version {schema_version}, this version supports up to {SCHEMA_VERSION}")

        generated_at: datetime = datetime.fromisoformat(data["generated_at"]) if data.get("generated_at") else datetime.now().astimezone()
        return cls(
            items=[TodoItem.from_dict(item) for item in data.get("items", [])],
            scanned_files=list(data.get("scanned_files", [])),
            root=data.get("root", ""),
            generated_at=generated_at,
            schema_version=schema_version,
        )
