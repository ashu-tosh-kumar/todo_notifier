"""This module provides interface to define a notifier that notifies the users. It also provides notifiers for email, Slack, Microsoft Teams and
generic webhooks, and `build_notifiers` to create them from the `[notify.<name>]` tables of the config file.

`BaseNotifier.notify(reports)` is the original API: it receives the generated HTML reports. `BaseNotifier.notify_result(result, reports)` additionally
receives the `ScanResult`; by default it calls `notify(reports)`, so custom notifiers keep working. The notifiers of this module override it to send
the digest of `todonotifier.digest`.

Security rules of the HTTP notifiers: only `https://` URLs are accepted (`http://` only for localhost, for tests), requests have a timeout, and
neither the URL, nor the headers, nor a response body ever appear in a log message or an exception message. Webhook URLs are secrets (anyone who
has one can post to the channel), so config files only name the environment variable that holds them.
"""

import http.client
import json
import os
import re
import smtplib
import ssl
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Callable, List, Mapping, Optional, Tuple, Union
from urllib.parse import urlsplit

from todonotifier.digest import (
    Digest,
    DigestItem,
    DigestSection,
    DigestTotals,
    build_digest,
    describe_item,
    render_text,
    safe_url,
)
from todonotifier.log import get_logger
from todonotifier.results import ScanResult
from todonotifier.summary_generators import jinja_env

logger = get_logger(__name__)

HTTP_TIMEOUT_SECONDS: float = 10
HTTP_RETRIES: int = 2
RETRY_BACKOFF_SECONDS: float = 1
RETRY_AFTER_CAP_SECONDS: float = 30
SMTP_TIMEOUT_SECONDS: float = 30
SLACK_MAX_BLOCKS: int = 50
SLACK_MAX_TEXT_LENGTH: int = 3000
USER_AGENT: str = "todonotifier"
WEBHOOK_EVENT: str = "todonotifier.scan"
_LOCAL_HOSTS: tuple[str, ...] = ("localhost", "127.0.0.1")
_TRUE_WORDS: tuple[str, ...] = ("1", "true", "yes", "on")
_FALSE_WORDS: tuple[str, ...] = ("0", "false", "no", "off")


class NotificationError(Exception):
    """Raised when a notification could not be delivered. The message never contains URLs, headers, credentials or response bodies"""


class NotifierConfigError(ValueError):
    """Raised when a notifier cannot be created from its settings, e.g. an environment variable is missing. Messages name the variable, never its value"""


class BaseNotifier(ABC):
    def __init__(self) -> None:
        """Initializer for `BaseNotifier`"""
        pass

    def _aggregate_all_summaries(self, summary: List[Tuple[str, str]]) -> str:
        """Abstract method allowing to aggregate all summaries together to be sent

        Args:
            summary (List[Tuple[str, str]]): List of tuples where each tuple consists of summary name and generated summary html

        Returns:
            str: Returns the string representing aggregation of all summaries in their html format
        """
        html = """\
        <html>
        <body>
        """

        for summary_name, summary_html in summary:
            html += f"""
            <h1>{summary_name}</h1>
            <p>
                {summary_html}
            </p><br>
            """

        html += """
        </body>
        </html>
        """

        return html

    def notify_result(self, result: ScanResult, reports: List[Tuple[str, str]]) -> None:
        """Sends a notification for a scan, with the structured result next to the generated reports

        The default implementation calls `notify(reports)`, so notifiers written before `ScanResult` existed keep working. Override it to use the result.

        Args:
            result (ScanResult): Result of the scan
            reports (List[Tuple[str, str]]): List of tuples where each tuple consists of summary name and generated summary html
        """
        self.notify(reports)

    @abstractmethod
    def notify(self, summary: List[Tuple[str, str]]) -> None:
        """Abstract method to send notification to users via method setup by users

        Args:
            summary (List[Tuple[str, str]]): List of tuples where each tuple consists of summary name and generated summary html
        """
        pass


class DigestNotifier(BaseNotifier):
    """Base class of notifiers that send the digest of a scan (`todonotifier.digest`) in `notify_result`

    Attributes:
        new_count (int | None): Number of new TODOs, shown in the totals of the digest when set. The command line sets it for `--since` runs
    """

    def __init__(self, max_items: int = 10) -> None:
        """Initializer for `DigestNotifier`

        Args:
            max_items (int, optional): Maximum number of items shown in each section of the digest. Defaults to 10

        Raises:
            ValueError: Raised if `max_items` is less than 1
        """
        if max_items < 1:
            raise ValueError("max_items must be at least 1")

        super().__init__()
        self._max_items = max_items
        self.new_count: Optional[int] = None

    def make_digest(self, result: ScanResult) -> Digest:
        """Builds the digest of `result` with this notifier's `max_items` and `new_count`

        Args:
            result (ScanResult): Result of the scan

        Returns:
            Digest: The digest
        """
        return build_digest(result, top_n=self._max_items, new_count=self.new_count)


def _validate_url(url: str, label: str) -> str:
    """Checks that `url` is an https URL (or an http URL for localhost). The URL is never put in the error message

    Args:
        url (str): URL to post to
        label (str): Name of the notifier for the error message

    Returns:
        str: `url`

    Raises:
        ValueError: Raised if the URL is not allowed
    """
    parts = urlsplit(url or "")
    if parts.scheme == "https" and parts.hostname:
        return url

    if parts.scheme == "http" and parts.hostname in _LOCAL_HOSTS:
        return url

    raise ValueError(f"{label} URL must be an https:// URL (http:// is only allowed for localhost)")


def _validate_headers(headers: Mapping[str, str], label: str) -> dict[str, str]:
    """Checks the extra headers of a request. Values are never put in the error message

    Args:
        headers (Mapping[str, str]): Header names and values
        label (str): Name of the notifier for the error message

    Returns:
        dict[str, str]: A copy of `headers`

    Raises:
        ValueError: Raised if a name or a value is not a string, or has a line break (header injection)
    """
    checked: dict[str, str] = {}
    for name, value in headers.items():
        if not isinstance(name, str) or not name or not name.isascii() or any(char in name for char in " \t\r\n:"):
            raise ValueError(f"{label} has an invalid header name")

        if not isinstance(value, str) or "\r" in value or "\n" in value or not value.isascii():
            raise ValueError(f"{label} header '{name}' has an invalid value")

        checked[name] = value

    return checked


def _retry_delay(retry_after: Optional[str], attempt: int) -> float:
    """Seconds to wait before the next attempt: a numeric `Retry-After` (capped), else exponential backoff

    Args:
        retry_after (str | None): Value of the `Retry-After` header, if any (dates are ignored)
        attempt (int): Number of the attempt that just failed, starting at 1

    Returns:
        float: Delay in seconds
    """
    if retry_after is not None:
        try:
            return min(max(float(retry_after), 0.0), RETRY_AFTER_CAP_SECONDS)
        except ValueError:
            pass

    return RETRY_BACKOFF_SECONDS * 2 ** (attempt - 1)


def _post_json(url: str, payload: Any, headers: Mapping[str, str], label: str, sleep: Callable[[float], None], timeout: float = HTTP_TIMEOUT_SECONDS) -> None:
    """Posts `payload` as JSON, retrying on HTTP 5xx, HTTP 429 and network errors

    There are `HTTP_RETRIES` retries with exponential backoff (1 s, 2 s); a numeric `Retry-After` header is honoured up to `RETRY_AFTER_CAP_SECONDS`.
    Other HTTP errors (4xx) are not retried. Custom headers are not forwarded if the server redirects. Neither the URL, nor the headers, nor the
    response is ever logged or put in an exception.

    Args:
        url (str): URL, already validated with `_validate_url`
        payload (Any): JSON serializable body
        headers (Mapping[str, str]): Extra headers (e.g. authorization)
        label (str): Name of the notifier for messages, e.g. "Slack webhook"
        sleep (Callable[[float], None]): Called with the number of seconds to wait between attempts
        timeout (float, optional): Timeout of each request in seconds. Defaults to `HTTP_TIMEOUT_SECONDS`

    Raises:
        NotificationError: Raised if the request still fails after the last attempt, or fails in a way that is not worth retrying
    """
    body: bytes = json.dumps(payload).encode("utf-8")
    attempts: int = HTTP_RETRIES + 1
    failure: str = ""
    attempt: int = 0
    while attempt < attempts:
        attempt += 1
        request = urllib.request.Request(url, data=body, method="POST")
        known: set[str] = {name.lower() for name in headers}
        if "content-type" not in known:
            request.add_header("Content-Type", "application/json; charset=utf-8")
        if "user-agent" not in known:
            request.add_header("User-Agent", USER_AGENT)
        for name, value in headers.items():
            request.add_unredirected_header(name, value)  # unlike normal headers, these are dropped when a redirect points somewhere else

        retry_after: Optional[str] = None
        retryable: bool = True
        try:
            with urllib.request.urlopen(request, timeout=timeout):
                pass
            logger.info("%s notification sent", label)
            return
        except urllib.error.HTTPError as exc:
            failure = f"HTTP {exc.code}"
            retryable = exc.code >= 500 or exc.code == 429
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            exc.close()
        except urllib.error.URLError as exc:
            failure = f"{type(exc).__name__} ({type(exc.reason).__name__})"
        except (OSError, http.client.HTTPException) as exc:
            failure = type(exc).__name__
        except Exception as exc:  # The message of an unexpected error may contain the URL or a header value, so only its type is kept
            failure = f"unexpected {type(exc).__name__}"
            retryable = False

        logger.warning("%s POST failed with %s (attempt %d/%d)", label, failure, attempt, attempts)
        if not retryable:
            break

        if attempt < attempts:
            sleep(_retry_delay(retry_after, attempt))

    raise NotificationError(f"{label} POST failed with {failure} after {attempt} attempt(s)")


class _HttpNotifier(DigestNotifier):
    """Base class of the notifiers that POST JSON to a URL. Subclasses build the payloads

    The URL is a secret, so it is not kept in `repr()`.
    """

    label: str = "Webhook"

    def __init__(self, url: str, headers: Optional[Mapping[str, str]] = None, max_items: int = 10) -> None:
        """Initializer for `_HttpNotifier`

        Args:
            url (str): URL to POST to. Must be https (http is allowed for localhost only)
            headers (Mapping[str, str] | None, optional): Extra request headers, e.g. an authorization header. Defaults to None
            max_items (int, optional): Maximum number of items shown in each section of the digest. Defaults to 10

        Raises:
            ValueError: Raised if the URL or a header is not allowed
        """
        super().__init__(max_items)
        self._url = _validate_url(url, self.label)
        self._headers = _validate_headers(headers or {}, self.label)
        self._sleep: Callable[[float], None] = time.sleep

    def __repr__(self) -> str:
        return f"{type(self).__name__}(max_items={self._max_items})"

    def _post(self, payload: Any) -> None:
        """Posts `payload` with the retry rules of `_post_json`"""
        _post_json(self._url, payload, self._headers, self.label, self._sleep)

    def _result_payload(self, result: ScanResult, digest: Digest) -> Any:
        """Payload for a scan result"""
        raise NotImplementedError  # pragma: no cover - always overridden

    def _reports_payload(self, text: str, names: list[str]) -> Any:
        """Payload for the old API, which only knows the names of the reports"""
        raise NotImplementedError  # pragma: no cover - always overridden

    def notify_result(self, result: ScanResult, reports: List[Tuple[str, str]]) -> None:
        """Posts the digest of `result`

        Args:
            result (ScanResult): Result of the scan
            reports (List[Tuple[str, str]]): Generated reports (not sent, they are HTML)

        Raises:
            NotificationError: Raised if the message could not be delivered
        """
        self._post(self._result_payload(result, self.make_digest(result)))

    def notify(self, summary: List[Tuple[str, str]]) -> None:
        """Posts a short message that lists the names of the reports

        Args:
            summary (List[Tuple[str, str]]): List of tuples where each tuple consists of summary name and generated summary html

        Raises:
            NotificationError: Raised if the message could not be delivered
        """
        names: list[str] = [name for name, _ in summary]
        text: str = "TODO Notifier generated reports: " + (", ".join(names) if names else "none")
        self._post(self._reports_payload(text, names))


def _slack_escape(text: str) -> str:
    """Escapes the three characters that Slack treats as control characters"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _slack_item_line(section_key: str, item: DigestItem) -> str:
    """One bullet of a Slack message: a link to the line, the message and the status"""
    url: Optional[str] = safe_url(item.web_url)
    if url:
        where: str = f"<{url}|{_slack_escape(item.location).replace('|', chr(0xA6))}>"
    else:
        where = "`" + _slack_escape(item.location).replace("`", "'") + "`"
    return f"• {where} {_slack_escape(item.message)} ({describe_item(section_key, item)})"


def _slack_units(section: DigestSection) -> list[tuple[str, int]]:
    """Lines of a section with the number of TODOs each one stands for (titles and owners count 0)"""
    units: list[tuple[str, int]] = [(f"*{section.title} ({section.total})*", 0)]
    for group in section.groups:
        units.append((f"*{_slack_escape(group.label)}* ({group.count})", 0))
        units.extend((_slack_item_line(section.key, item), 1) for item in group.items)
    if section.hidden_count:
        units.append((f"_...and {section.hidden_count} more_", section.hidden_count))
    return units


def _slack_pack(units: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """Packs lines into texts of at most `SLACK_MAX_TEXT_LENGTH` characters (the limit of a section block), as (text, number of TODOs)"""
    packed: list[tuple[str, int]] = []
    text: str = ""
    count: int = 0
    for line, weight in units:
        if len(line) > SLACK_MAX_TEXT_LENGTH:
            line = line[: SLACK_MAX_TEXT_LENGTH - 1] + "…"

        if text and len(text) + 1 + len(line) > SLACK_MAX_TEXT_LENGTH:
            packed.append((text, count))
            text, count = "", 0

        text = f"{text}\n{line}" if text else line
        count += weight

    if text:
        packed.append((text, count))
    return packed


class SlackWebhookNotifier(_HttpNotifier):
    """Posts the digest to a Slack channel through an incoming webhook (Block Kit)

    The message has a header, a section with the totals and one section per group of the digest, within Slack's limits of 3000 characters per
    section and 50 blocks per message. Lists are cut with "...and N more". Create the webhook at https://api.slack.com/messaging/webhooks and
    keep its URL in an environment variable.
    """

    label: str = "Slack webhook"

    def __init__(self, webhook_url: str, max_items: int = 10) -> None:
        """Initializer for `SlackWebhookNotifier`

        Args:
            webhook_url (str): Incoming webhook URL (https)
            max_items (int, optional): Maximum number of items shown in each section of the digest. Defaults to 10
        """
        super().__init__(webhook_url, None, max_items)

    def _result_payload(self, result: ScanResult, digest: Digest) -> dict[str, Any]:
        """Builds the Slack message: `text` (fallback for notifications) and `blocks`"""
        totals: DigestTotals = digest.totals
        parts: list[str] = [
            f"*{totals.open}* open",
            f"*{totals.overdue}* overdue",
            f"*{totals.stale}* stale",
            f"*{totals.due_soon}* due this week",
            f"*{totals.unowned}* unowned",
        ]
        if totals.new is not None:
            parts.append(f"*{totals.new}* new")

        blocks: list[dict[str, Any]] = [
            {"type": "header", "text": {"type": "plain_text", "text": f"TODO digest {digest.generated_on.isoformat()}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": "  |  ".join(parts)}},
        ]
        if digest.is_empty:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "Nothing is overdue, stale or due this week."}})

        body: list[tuple[str, int]] = []
        for section in digest.sections:
            if section.total:
                body.extend(_slack_pack(_slack_units(section)))

        room: int = SLACK_MAX_BLOCKS - len(blocks)
        if len(body) > room:
            kept: int = room - 1  # The last block says how many TODOs did not fit
            dropped: int = sum(count for _, count in body[kept:])
            body = body[:kept] + [(f"_...and {dropped} more_", dropped)]
        blocks.extend({"type": "section", "text": {"type": "mrkdwn", "text": text}} for text, _ in body)

        return {"text": f"TODO digest: {digest.headline}", "blocks": blocks}

    def _reports_payload(self, text: str, names: list[str]) -> dict[str, Any]:
        """Builds a plain Slack message"""
        return {"text": text}


# Characters of the Markdown subset of a Teams TextBlock (bold, italic, links), replaced by look-alikes that Markdown does not know
_TEAMS_LOOKALIKES: dict[str, str] = {"*": "\u2217", "[": "\uff3b", "]": "\uff3d", "`": "\u02cb"}
# An underscore can start or end italics unless it sits between two letters or digits, as in `my_file_name.py`
_TEAMS_UNDERSCORE: "re.Pattern[str]" = re.compile(r"(?<![^\W_])_|_(?![^\W_])")


def _teams_text(text: str) -> str:
    """Makes untrusted text safe for a Teams Adaptive Card `TextBlock` by replacing its Markdown characters with look-alikes

    A TextBlock understands a small subset of Markdown (bold, italic, bullet lists, links). Backslash escapes are not part of that subset (Teams
    shows the backslash), so characters are replaced instead: `*`, `_` (except inside a word, where it is not italics), `[`, `]` and the backtick
    become similar looking characters (for example the full-width square bracket). The text cannot form a link or emphasis, and `my_file_name.py` and
    `__init__.py` stay readable. A link is made only by the code, from a checked URL (`digest.safe_url`).

    Args:
        text (str): Text such as the message of a TODO, a file name or an author

    Returns:
        str: The text for a `TextBlock`
    """
    text = "".join(_TEAMS_LOOKALIKES.get(char, char) for char in text)
    return _TEAMS_UNDERSCORE.sub("\uff3f", text)


class TeamsWebhookNotifier(_HttpNotifier):
    """Posts the digest to a Microsoft Teams channel as an Adaptive Card, through a Workflows webhook

    Create the webhook with the Teams Workflows template "Post to a channel when a webhook request is received" (trigger "When a Teams webhook
    request is received") and keep its URL in an environment variable. The payload is a message with an Adaptive Card attachment
    (`TextBlock`s and a `FactSet`), the format that trigger expects.

    Text in a TextBlock supports only a small Markdown subset and no backslash escapes, so untrusted text is not escaped but neutralised
    (`_teams_text`): its Markdown characters are replaced by look-alikes.

    Note: Microsoft is retiring the Office 365 connectors in favour of Workflows. The payload below follows the documented Workflows format, but verify
    it against the current Microsoft documentation before relying on it. Teams limits the size of a message (about 28 KB), so keep `max_items`
    modest.
    """

    label: str = "Teams webhook"
    CARD_SCHEMA: str = "http://adaptivecards.io/schemas/adaptive-card.json"
    CARD_VERSION: str = "1.4"

    def __init__(self, webhook_url: str, max_items: int = 10) -> None:
        """Initializer for `TeamsWebhookNotifier`

        Args:
            webhook_url (str): Workflows webhook URL (https)
            max_items (int, optional): Maximum number of items shown in each section of the digest. Defaults to 10
        """
        super().__init__(webhook_url, None, max_items)

    def _message(self, body: list[dict[str, Any]]) -> dict[str, Any]:
        """Wraps the body of an Adaptive Card in the message the Workflows trigger expects"""
        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": {"$schema": self.CARD_SCHEMA, "type": "AdaptiveCard", "version": self.CARD_VERSION, "body": body},
                }
            ],
        }

    def _result_payload(self, result: ScanResult, digest: Digest) -> dict[str, Any]:
        """Builds the Teams message"""
        totals: DigestTotals = digest.totals
        facts: list[tuple[str, int]] = [
            ("Open", totals.open),
            ("Overdue", totals.overdue),
            ("Stale", totals.stale),
            ("Due this week", totals.due_soon),
            ("Unowned", totals.unowned),
        ]
        if totals.new is not None:
            facts.append(("New", totals.new))

        body: list[dict[str, Any]] = [
            {"type": "TextBlock", "text": f"TODO digest {digest.generated_on.isoformat()}", "weight": "Bolder", "size": "Large", "wrap": True},
            {"type": "FactSet", "facts": [{"title": title, "value": str(value)} for title, value in facts]},
        ]
        if digest.is_empty:
            body.append({"type": "TextBlock", "text": "Nothing is overdue, stale or due this week.", "wrap": True})

        for section in digest.sections:
            if not section.total:
                continue

            body.append(
                {"type": "TextBlock", "text": f"{section.title} ({section.total})", "weight": "Bolder", "size": "Medium", "spacing": "Medium", "wrap": True}
            )
            for group in section.groups:
                body.append({"type": "TextBlock", "text": f"**{_teams_text(group.label)}** ({group.count})", "spacing": "Small", "wrap": True})
                for item in group.items:
                    url: Optional[str] = safe_url(item.web_url)
                    location: str = _teams_text(item.location)
                    where: str = f"[{location}]({url})" if url else location
                    text: str = f"{where} {_teams_text(item.message)} ({describe_item(section.key, item)})"
                    body.append({"type": "TextBlock", "text": text, "spacing": "None", "wrap": True})
            if section.hidden_count:
                body.append({"type": "TextBlock", "text": f"...and {section.hidden_count} more", "isSubtle": True, "spacing": "None", "wrap": True})

        return self._message(body)

    def _reports_payload(self, text: str, names: list[str]) -> dict[str, Any]:
        """Builds a Teams message with a single line"""
        return self._message([{"type": "TextBlock", "text": _teams_text(text), "wrap": True}])


class WebhookNotifier(_HttpNotifier):
    """POSTs the whole scan result as JSON to any URL (Discord bridges, Zapier, internal tools)

    The body is `{"event": "todonotifier.scan", "result": ScanResult.to_dict(), "digest": {<totals>}}`. The totals are `open`, `overdue`, `stale`,
    `due_soon`, `unowned` and, if known, `new`. Put credentials in `headers` (read them from the environment, not from code).
    """

    label: str = "Webhook"

    def __init__(self, url: str, headers: Optional[Mapping[str, str]] = None) -> None:
        """Initializer for `WebhookNotifier`

        Args:
            url (str): URL to POST to (https)
            headers (Mapping[str, str] | None, optional): Extra request headers, e.g. `{"Authorization": "Bearer ..."}`. Defaults to None
        """
        super().__init__(url, headers)

    def _result_payload(self, result: ScanResult, digest: Digest) -> dict[str, Any]:
        """Builds the JSON body"""
        return {"event": WEBHOOK_EVENT, "result": result.to_dict(), "digest": digest.totals.to_dict()}

    def _reports_payload(self, text: str, names: list[str]) -> dict[str, Any]:
        """Builds a JSON body that lists the reports"""
        return {"event": "todonotifier.reports", "text": text, "reports": names}


def _env_value(environ: Mapping[str, str], name: str, setting: str = "") -> str:
    """Reads a required environment variable

    Args:
        environ (Mapping[str, str]): Environment
        name (str): Variable name
        setting (str, optional): Where the name came from, such as `notify.slack.webhook_env`, for the error message. Defaults to ""

    Returns:
        str: The value (never empty)

    Raises:
        NotifierConfigError: Raised if the variable is not set or empty. The message names the variable only
    """
    value: Optional[str] = environ.get(name)
    if not value:
        origin: str = f" (named by {setting})" if setting else ""
        raise NotifierConfigError(f"Environment variable {name}{origin} is not set or is empty.")

    return value


def _parse_bool(value: str, name: str) -> bool:
    """Parses a boolean environment variable, naming the variable (not the value) if it is invalid"""
    word: str = value.strip().lower()
    if word in _TRUE_WORDS:
        return True

    if word in _FALSE_WORDS:
        return False

    raise NotifierConfigError(f"Environment variable {name} must be one of: 1, 0, true, false, yes, no, on, off.")


def _parse_port(value: str, name: str) -> int:
    """Parses a port number, naming the variable (not the value) if it is invalid"""
    if not value.strip().isdigit() or not 0 < int(value) < 65536:
        raise NotifierConfigError(f"Environment variable {name} must be a port number (1 to 65535).")

    return int(value)


class EmailNotifier(DigestNotifier):
    def __init__(
        self,
        sender_email: str,
        password: str,
        host: str,
        port: int,
        receivers: Union[List[str], None] = None,
        starttls: bool = False,
        username: Optional[str] = None,
        max_items: int = 10,
    ) -> None:
        """Initializer for `EmailNotifier` class

        Args:
            sender_email (str): Email id from which email needs to be sent
            password (str): Password for email id `sender_email`
            host (str): Host for sending email for e.g. `smtp.gmail.com` for Gmail
            port (int): Port for sending email for e.g. `465` for Gmail (implicit SSL) or `587` with `starttls=True`
            receivers (Union[List[str], None], optional): List of receivers. Defaults to None.
            starttls (bool, optional): Connect in plain text and upgrade with STARTTLS (typically port 587) instead of using SSL from the start (port 465).
                Defaults to False.
            username (str | None, optional): Login name, if it is not `sender_email`. Defaults to None.
            max_items (int, optional): Maximum number of items shown in each section of the digest of `notify_result`. Defaults to 10.
        """
        self._sender_email = sender_email
        self._receivers = receivers or []
        self._password = password
        self._host = host
        self._port = port
        self._starttls = starttls
        self._username = username or sender_email
        super().__init__(max_items)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(host={self._host!r}, port={self._port!r}, starttls={self._starttls!r})"

    @classmethod
    def from_env(cls, prefix: str = "TODO_SMTP_", environ: Optional[Mapping[str, str]] = None) -> "EmailNotifier":
        """Creates a notifier from environment variables

        Variables (after `prefix`): `HOST`, `SENDER`, `RECIPIENTS` (comma separated) and `PASSWORD` are required; `PORT` (default 587 with
        `STARTTLS`, else 465), `USERNAME` (default: the sender) and `STARTTLS` (`1`/`true`/`yes`/`on`, default off) are optional.

        Args:
            prefix (str, optional): Prefix of the variable names. Defaults to "TODO_SMTP_"
            environ (Mapping[str, str] | None, optional): Environment to read. Defaults to `os.environ`

        Returns:
            EmailNotifier: The notifier

        Raises:
            NotifierConfigError: Raised if a required variable is missing or a value is invalid. The message names the variable, never its value
        """
        env: Mapping[str, str] = os.environ if environ is None else environ
        host: str = _env_value(env, f"{prefix}HOST")
        sender: str = _env_value(env, f"{prefix}SENDER")
        recipients_name: str = f"{prefix}RECIPIENTS"
        recipients: list[str] = [part.strip() for part in _env_value(env, recipients_name).split(",") if part.strip()]
        if not recipients:
            raise NotifierConfigError(f"Environment variable {recipients_name} must list at least one email address.")

        password: str = _env_value(env, f"{prefix}PASSWORD")
        starttls: bool = _parse_bool(env[f"{prefix}STARTTLS"], f"{prefix}STARTTLS") if env.get(f"{prefix}STARTTLS") else False
        port: int = _parse_port(env[f"{prefix}PORT"], f"{prefix}PORT") if env.get(f"{prefix}PORT") else (587 if starttls else 465)
        return cls(sender, password, host, port, recipients, starttls=starttls, username=env.get(f"{prefix}USERNAME") or None)

    def _send(self, message: MIMEMultipart) -> None:
        """Sends a message to the receivers over SSL, or over STARTTLS if enabled"""
        context = ssl.create_default_context()
        if self._starttls:
            with smtplib.SMTP(self._host, self._port, timeout=SMTP_TIMEOUT_SECONDS) as server:
                server.starttls(context=context)
                server.login(self._username, self._password)
                server.sendmail(self._sender_email, self._receivers, message.as_string())
        else:
            with smtplib.SMTP_SSL(self._host, self._port, context=context, timeout=SMTP_TIMEOUT_SECONDS) as server:
                server.login(self._username, self._password)
                server.sendmail(self._sender_email, self._receivers, message.as_string())

    def notify(self, summary: List[Tuple[str, str]]) -> None:
        """Sends email to `receivers_list` with `html` content

        Args:
            summary (List[Tuple[str, str]]): List of tuples where each tuple consists of summary name and generated summary html
        """
        html = self._aggregate_all_summaries(summary)
        receivers_str = ", ".join(self._receivers)

        message = MIMEMultipart("alternative")
        message["Subject"] = f"TODO Summary - {datetime.today().date()}"
        message["From"] = self._sender_email
        message["To"] = receivers_str

        html = MIMEText(html, "html")
        message.attach(html)
        self._send(message)

    def notify_result(self, result: ScanResult, reports: List[Tuple[str, str]]) -> None:
        """Sends the digest by email: a plain text part and an HTML part, with the generated reports below the digest in the HTML part

        Args:
            result (ScanResult): Result of the scan
            reports (List[Tuple[str, str]]): List of tuples where each tuple consists of summary name and generated summary html
        """
        digest: Digest = self.make_digest(result)
        text: str = render_text(digest)
        if reports:
            text += "\n\nFull reports (" + ", ".join(name for name, _ in reports) + ") are in the HTML version of this email."

        html: str = jinja_env.get_template("digest_email.html").render(digest=digest, reports=reports, describe_item=describe_item, safe_url=safe_url)
        message = MIMEMultipart("alternative")
        message["Subject"] = f"TODO digest {digest.generated_on}: {digest.totals.overdue} overdue, {digest.totals.stale} stale"
        message["From"] = self._sender_email
        message["To"] = ", ".join(self._receivers)
        message.attach(MIMEText(text, "plain"))
        message.attach(MIMEText(html, "html"))  # The last part is the preferred one
        self._send(message)


def _env_notifier_value(environ: Mapping[str, str], table: Mapping[str, Any], key: str, name: str) -> str:
    """Reads the environment variable that the `key` of notifier `name` points to"""
    return _env_value(environ, table[key], f"notify.{name}.{key}")


def _headers_from_env(raw: str, variable: str) -> dict[str, str]:
    """Parses the JSON object of extra headers. The error names the variable, never the content"""
    try:
        headers: Any = json.loads(raw)
    except ValueError:
        headers = None

    if not isinstance(headers, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in headers.items()):
        raise NotifierConfigError(f"Environment variable {variable} must hold a JSON object of header names to string values.")

    return headers


def build_notifiers(notify_config: Mapping[str, Mapping[str, Any]], environ: Mapping[str, str] = os.environ) -> list[BaseNotifier]:
    """Creates the notifiers described by the `[notify.<name>]` tables of the config file

    The tables are the validated ones of `ProjectConfig.notify` (see `todonotifier.settings_file`). Tables with `enabled = false` are skipped. Secrets are
    read from the environment variables named by the `*_env` keys.

    Args:
        notify_config (Mapping[str, Mapping[str, Any]]): Notifier tables by name ("slack", "teams", "webhook" or "email")
        environ (Mapping[str, str], optional): Environment to read the secrets from. Defaults to `os.environ`

    Returns:
        list[BaseNotifier]: One notifier per enabled table, in the order of the tables

    Raises:
        NotifierConfigError: Raised for an unknown notifier, a missing or empty environment variable, or an invalid value. The message names the
            variable, never its value
    """
    notifiers: list[BaseNotifier] = []
    for name, table in notify_config.items():
        if not table.get("enabled", True):
            continue

        try:
            if name in ("slack", "teams"):
                url: str = _env_notifier_value(environ, table, "webhook_env", name)
                notifier_class = SlackWebhookNotifier if name == "slack" else TeamsWebhookNotifier
                notifiers.append(notifier_class(url, max_items=table.get("max_items", 10)))
            elif name == "webhook":
                url = _env_notifier_value(environ, table, "url_env", name)
                headers: dict[str, str] = {}
                if table.get("headers_env"):
                    headers = _headers_from_env(_env_notifier_value(environ, table, "headers_env", name), table["headers_env"])
                notifiers.append(WebhookNotifier(url, headers))
            elif name == "email":
                starttls: bool = bool(table.get("starttls", False))
                username: Optional[str] = _env_notifier_value(environ, table, "username_env", name) if table.get("username_env") else None
                notifiers.append(
                    EmailNotifier(
                        table["sender"],
                        _env_notifier_value(environ, table, "password_env", name),
                        table["smtp_host"],
                        table.get("smtp_port", 587 if starttls else 465),
                        list(table["recipients"]),
                        starttls=starttls,
                        username=username,
                    )
                )
            else:
                raise NotifierConfigError(f"Unknown notifier '{name}'. Supported notifiers: slack, teams, webhook, email.")
        except NotifierConfigError:
            raise
        except ValueError as exc:
            # The messages of the URL and header checks never contain the values, so they are safe to show
            raise NotifierConfigError(f"Invalid settings for notify.{name}: {exc}.") from None

    return notifiers
