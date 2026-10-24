"""This module builds a channel-neutral digest of a `ScanResult` and renders it as plain text or Markdown.

The digest has totals and up to three sections, in this order (see "D4 design" in the roadmap):

- "Overdue": the explicit `{date}` of the TODO has passed.
- "Stale": the default due date (creation date plus `default_due_days`) has passed. Stale is never called overdue.
- "Due this week": the due date is today or in the next 7 days.

Each section is grouped by owner (the owner with the most items first, ties by name, unowned last), and the items of an owner are ordered by
days past due, most first. A section shows at most `top_n` items in total; the rest is only counted (`DigestSection.hidden_count`) so that
a channel can say "...and N more". The notifiers in `todonotifier.notifier` turn a `Digest` into Slack, Teams, webhook and email payloads.

The status of an item is computed against `today` with `results.compute_status`, so the digest does not depend on when the stored status
fields were computed.
"""

import re
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any, Optional
from urllib.parse import urlsplit

from todonotifier.results import DUE_SOURCE_NONE, ScanResult, TodoItem, compute_status

SECTION_OVERDUE: str = "overdue"
SECTION_STALE: str = "stale"
SECTION_DUE_SOON: str = "due_soon"

SECTION_TITLES: dict[str, str] = {SECTION_OVERDUE: "Overdue", SECTION_STALE: "Stale", SECTION_DUE_SOON: "Due this week"}
DUE_SOON_DAYS: int = 7
DEFAULT_TOP_N: int = 10
MAX_MESSAGE_LENGTH: int = 200
UNOWNED_LABEL: str = "Unowned"

_MARKDOWN_SPECIAL: re.Pattern = re.compile(r"([\\`*_\[\]<>|~&#])")
# An "@" that starts a name: GitHub turns "@user" and "@org/team" in a comment into a mention that notifies them
_MENTION: re.Pattern = re.compile(r"@(?=[A-Za-z0-9_])")
_UNSAFE_URL_CHARS: re.Pattern = re.compile(r"[\s<>|\"\\]")


@dataclass
class DigestItem:
    """A TODO as shown in a digest

    Attributes:
        file (str): POSIX path of the file, relative to the scan root
        line (int): 1-indexed line number
        tag (str): Tag that was matched, e.g. "TODO"
        message (str): Message on a single line, truncated to `MAX_MESSAGE_LENGTH` characters
        days_past_due (int): Days since the due date (0 if it is not past due)
        due_date (date | None): Due date
        web_url (str | None): Deep link to the line, if known
    """

    file: str
    line: int
    tag: str
    message: str
    days_past_due: int = 0
    due_date: Optional[date] = None
    web_url: Optional[str] = None

    @property
    def location(self) -> str:
        """Text such as `src/app.py:42`"""
        return f"{self.file}:{self.line}"


@dataclass
class OwnerGroup:
    """The items of one owner in a section

    Attributes:
        owner (str | None): Owner, or None for TODOs without an author
        count (int): Number of items of this owner in the section, including the ones that are not shown
        items (list[DigestItem]): The items that are shown
    """

    owner: Optional[str]
    count: int
    items: list[DigestItem] = field(default_factory=list)

    @property
    def label(self) -> str:
        """Owner to display, `UNOWNED_LABEL` if there is none"""
        return self.owner or UNOWNED_LABEL


@dataclass
class DigestSection:
    """One section of a digest

    Attributes:
        key (str): One of `SECTION_OVERDUE`, `SECTION_STALE` and `SECTION_DUE_SOON`
        title (str): Title to display
        total (int): Number of items in the section, including the ones that are not shown
        groups (list[OwnerGroup]): The items that are shown, grouped by owner
        hidden_count (int): Number of items that are not shown because of `top_n`
    """

    key: str
    title: str
    total: int = 0
    groups: list[OwnerGroup] = field(default_factory=list)
    hidden_count: int = 0


@dataclass
class DigestTotals:
    """Counts of a digest

    Attributes:
        open (int): All TODOs found
        overdue (int): TODOs whose explicit due date has passed
        stale (int): TODOs whose default due date has passed
        due_soon (int): TODOs due today or in the next 7 days
        unowned (int): TODOs without an author
        new (int | None): TODOs that are new (e.g. in a `--since` run), None if not known
    """

    open: int = 0
    overdue: int = 0
    stale: int = 0
    due_soon: int = 0
    unowned: int = 0
    new: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        """Converts the totals to a JSON friendly dictionary. `new` is left out when it is not known

        Returns:
            dict[str, Any]: The counts by name
        """
        data: dict[str, Any] = asdict(self)
        if self.new is None:
            del data["new"]
        return data


@dataclass
class Digest:
    """A channel-neutral summary of a scan

    Attributes:
        totals (DigestTotals): The counts
        sections (list[DigestSection]): Overdue, stale and due this week, in that order. Sections without items are present but empty
        generated_on (date): The reference day
        top_n (int): Maximum number of items per section
    """

    totals: DigestTotals
    sections: list[DigestSection] = field(default_factory=list)
    generated_on: date = field(default_factory=date.today)
    top_n: int = DEFAULT_TOP_N

    @property
    def headline(self) -> str:
        """The totals in one line, such as `12 open, 3 overdue, 4 stale, 2 due this week, 5 unowned, 1 new`"""
        parts: list[str] = [
            f"{self.totals.open} open",
            f"{self.totals.overdue} overdue",
            f"{self.totals.stale} stale",
            f"{self.totals.due_soon} due this week",
            f"{self.totals.unowned} unowned",
        ]
        if self.totals.new is not None:
            parts.append(f"{self.totals.new} new")
        return ", ".join(parts)

    @property
    def is_empty(self) -> bool:
        """Whether no section has an item"""
        return all(section.total == 0 for section in self.sections)

    def to_dict(self) -> dict[str, Any]:
        """Converts the digest to a JSON friendly dictionary

        Returns:
            dict[str, Any]: Totals, and the sections with their shown items
        """
        return {
            "generated_on": self.generated_on.isoformat(),
            "top_n": self.top_n,
            "totals": self.totals.to_dict(),
            "sections": [
                {
                    "key": section.key,
                    "title": section.title,
                    "total": section.total,
                    "hidden_count": section.hidden_count,
                    "groups": [
                        {
                            "owner": group.owner,
                            "count": group.count,
                            "items": [
                                {
                                    "file": item.file,
                                    "line": item.line,
                                    "tag": item.tag,
                                    "message": item.message,
                                    "days_past_due": item.days_past_due,
                                    "due_date": item.due_date.isoformat() if item.due_date else None,
                                    "web_url": item.web_url,
                                }
                                for item in group.items
                            ],
                        }
                        for group in section.groups
                    ],
                }
                for section in self.sections
            ],
        }


def shorten_message(message: str, limit: int = MAX_MESSAGE_LENGTH) -> str:
    """Puts a message on one line and truncates it

    Args:
        message (str): Message of a TODO
        limit (int, optional): Maximum length of the result, including the ellipsis. Defaults to `MAX_MESSAGE_LENGTH`

    Returns:
        str: The message with whitespace collapsed, ending in an ellipsis if it was cut
    """
    text: str = " ".join(message.split())
    if len(text) <= limit:
        return text

    return text[: limit - 1].rstrip() + "…"


def safe_url(url: Optional[str]) -> Optional[str]:
    """Returns `url` if it is safe to put in a link of a chat message or Markdown, else None

    Only http and https links are kept, and links with whitespace or characters that end a Slack or Markdown link are dropped.
    Parentheses are percent-encoded.

    Args:
        url (str | None): Link, such as `TodoItem.web_url`

    Returns:
        str | None: The link, or None
    """
    if not url or _UNSAFE_URL_CHARS.search(url):
        return None

    try:
        parts = urlsplit(url)
    except ValueError:  # e.g. an unclosed IPv6 bracket in a mistyped repository URL
        return None

    if parts.scheme not in ("http", "https") or not parts.netloc:
        return None

    return url.replace("(", "%28").replace(")", "%29")


def escape_markdown(text: str) -> str:
    """Escapes the characters of `text` that Markdown would interpret, so that untrusted text cannot inject links or formatting

    An "@" that starts a name gets an invisible zero width space after it (`&#8203;`), because a backslash does not stop GitHub from turning `@user` or
    `@org/team` into a mention, and a pull request comment that mentions people notifies them.

    Args:
        text (str): Text such as the message of a TODO

    Returns:
        str: Text for use in Markdown
    """
    return _MENTION.sub("@&#8203;", _MARKDOWN_SPECIAL.sub(r"\\\1", text))


def describe_item(section_key: str, item: DigestItem) -> str:
    """Describes the due status of an item, such as `12 days overdue`

    Args:
        section_key: One of `SECTION_OVERDUE`, `SECTION_STALE` and `SECTION_DUE_SOON`
        item (DigestItem): Item of that section

    Returns:
        str: `N days overdue`, `N days stale` or `due YYYY-MM-DD`
    """
    if section_key == SECTION_DUE_SOON:
        return f"due {item.due_date.isoformat()}" if item.due_date else "due soon"

    noun: str = "day" if item.days_past_due == 1 else "days"
    word: str = "overdue" if section_key == SECTION_OVERDUE else "stale"
    return f"{item.days_past_due} {noun} {word}"


def _to_digest_item(item: TodoItem, days_past_due: int) -> DigestItem:
    """Converts a `TodoItem` for display"""
    return DigestItem(
        file=item.file,
        line=item.line,
        tag=item.tag,
        message=shorten_message(item.message),
        days_past_due=days_past_due,
        due_date=item.due_date,
        web_url=item.web_url,
    )


def _build_section(key: str, entries: list[tuple[TodoItem, int]], top_n: int) -> DigestSection:
    """Groups items by owner and keeps the first `top_n`

    Args:
        key (str): Section key
        entries (list[tuple[TodoItem, int]]): Items of the section with their days past due
        top_n (int): Maximum number of items to keep in total

    Returns:
        DigestSection: The section
    """
    by_owner: dict[Optional[str], list[tuple[TodoItem, int]]] = {}
    for item, days_past_due in entries:
        by_owner.setdefault(item.author or None, []).append((item, days_past_due))

    owners: list[Optional[str]] = sorted(by_owner, key=lambda owner: (owner is None, -len(by_owner[owner]), (owner or "").casefold(), owner or ""))

    groups: list[OwnerGroup] = []
    remaining: int = top_n
    for owner in owners:
        ordered: list[tuple[TodoItem, int]] = sorted(
            by_owner[owner], key=lambda entry: (-entry[1], entry[0].due_date or date.max, entry[0].file, entry[0].line)
        )
        shown: list[tuple[TodoItem, int]] = ordered[:remaining]
        if shown:
            groups.append(OwnerGroup(owner=owner, count=len(ordered), items=[_to_digest_item(item, days) for item, days in shown]))
            remaining -= len(shown)

    shown_count: int = top_n - remaining
    return DigestSection(key=key, title=SECTION_TITLES[key], total=len(entries), groups=groups, hidden_count=len(entries) - shown_count)


def build_digest(result: ScanResult, top_n: int = DEFAULT_TOP_N, today: Optional[date] = None, new_count: Optional[int] = None) -> Digest:
    """Builds a digest of a scan

    Args:
        result (ScanResult): The scan result
        top_n (int, optional): Maximum number of items shown per section. Defaults to 10
        today (date | None, optional): Reference day for overdue, stale and due this week. Defaults to the date of `result.generated_at`
        new_count (int | None, optional): Number of new TODOs (e.g. from a `--since` run), shown in the totals when given. Defaults to None

    Returns:
        Digest: The digest

    Raises:
        ValueError: Raised if `top_n` is less than 1
    """
    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    reference_day: date = today or result.generated_at.date()
    overdue: list[tuple[TodoItem, int]] = []
    stale: list[tuple[TodoItem, int]] = []
    for item in result.items:
        is_overdue, is_stale, days_past_due = compute_status(item.due_date, item.due_source, reference_day)
        if is_overdue:
            overdue.append((item, days_past_due))
        elif is_stale:
            stale.append((item, days_past_due))

    due_soon: list[tuple[TodoItem, int]] = [(item, 0) for item in result.due_within(DUE_SOON_DAYS, reference_day) if item.due_source != DUE_SOURCE_NONE]

    totals = DigestTotals(
        open=len(result.items),
        overdue=len(overdue),
        stale=len(stale),
        due_soon=len(due_soon),
        unowned=sum(1 for item in result.items if not item.author),
        new=new_count,
    )
    sections: list[DigestSection] = [
        _build_section(SECTION_OVERDUE, overdue, top_n),
        _build_section(SECTION_STALE, stale, top_n),
        _build_section(SECTION_DUE_SOON, due_soon, top_n),
    ]
    return Digest(totals=totals, sections=sections, generated_on=reference_day, top_n=top_n)


def render_text(digest: Digest) -> str:
    """Renders the digest as plain text, for the plain part of an email and for logs

    Args:
        digest (Digest): The digest

    Returns:
        str: Text without a trailing newline
    """
    lines: list[str] = [f"TODO digest {digest.generated_on.isoformat()}", digest.headline]
    if digest.is_empty:
        lines += ["", "Nothing is overdue, stale or due this week."]

    for section in digest.sections:
        if section.total == 0:
            continue

        lines += ["", f"{section.title} ({section.total})"]
        for group in section.groups:
            lines.append(f"  {group.label} ({group.count})")
            for item in group.items:
                url: Optional[str] = safe_url(item.web_url)
                suffix: str = f"  {url}" if url else ""
                lines.append(f"    {item.location}  {item.message} ({describe_item(section.key, item)}){suffix}")
        if section.hidden_count:
            lines.append(f"  ...and {section.hidden_count} more")

    return "\n".join(lines)


def render_markdown(digest: Digest) -> str:
    """Renders the digest as GitHub flavoured Markdown, e.g. for a GitHub step summary

    Messages are escaped, so text in a scanned file cannot add links or formatting.

    Args:
        digest (Digest): The digest

    Returns:
        str: Markdown without a trailing newline
    """
    totals: DigestTotals = digest.totals
    heads: list[str] = ["Open", "Overdue", "Stale", "Due this week", "Unowned"]
    values: list[str] = [str(totals.open), str(totals.overdue), str(totals.stale), str(totals.due_soon), str(totals.unowned)]
    if totals.new is not None:
        heads.append("New")
        values.append(str(totals.new))

    lines: list[str] = [
        f"## TODO digest {digest.generated_on.isoformat()}",
        "",
        "| " + " | ".join(heads) + " |",
        "|" + "---|" * len(heads),
        "| " + " | ".join(values) + " |",
    ]
    if digest.is_empty:
        lines += ["", "Nothing is overdue, stale or due this week."]

    for section in digest.sections:
        if section.total == 0:
            continue

        lines += ["", f"### {section.title} ({section.total})"]
        for group in section.groups:
            lines += ["", f"**{escape_markdown(group.label)}** ({group.count})", ""]
            for item in group.items:
                code: str = "`" + item.location.replace("`", "'") + "`"
                url: Optional[str] = safe_url(item.web_url)
                where: str = f"[{code}]({url})" if url else code
                lines.append(f"- {where} {escape_markdown(item.message)} ({describe_item(section.key, item)})")
        if section.hidden_count:
            lines += ["", f"_...and {section.hidden_count} more_"]

    return "\n".join(lines)
