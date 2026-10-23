import email
import http.client
import json
import os
import tempfile
import traceback
import unittest
import urllib.error
from email.message import Message
from io import BytesIO
from typing import List
from unittest.mock import MagicMock, Mock, patch

from tests.mocks import FakeContextManager
from tests.sample_results import (
    TODAY,
    assert_matches_snapshot,
    make_item,
    make_scan_result,
)
from todonotifier.notifier import (
    BaseNotifier,
    DigestNotifier,
    EmailNotifier,
    NotificationError,
    NotifierConfigError,
    SlackWebhookNotifier,
    TeamsWebhookNotifier,
    WebhookNotifier,
    _retry_delay,
    build_notifiers,
)
from todonotifier.results import ScanResult
from todonotifier.settings_file import resolve_project_config
from todonotifier.summary_generators import BaseSummaryGenerator


class MockBaseNotifier(BaseNotifier):
    """Mock class inheriting from `BaseNotifier` to allow testing"""

    def notify(self, summary_generators: List[BaseSummaryGenerator]) -> None:
        return None


class TestBaseNotifier(unittest.TestCase):
    def test__aggregate_all_summaries_should_aggregate_all_summaries(self):
        mock_summary_generator_1 = Mock()
        mock_summary_generator_1.name = "mock-summary-generator-1"
        mock_summary_generator_1.generate_html.return_value = "unittest-html-1"
        mock_summary_generator_2 = Mock()
        mock_summary_generator_2.name = "mock-summary-generator-2"
        mock_summary_generator_2.generate_html.return_value = "unittest-html-2"

        expected_value = """\
        <html>
        <body>
        
            <h1>mock-summary-generator-1</h1>
            <p>
                unittest-html-1
            </p><br>
            
            <h1>mock-summary-generator-2</h1>
            <p>
                unittest-html-2
            </p><br>
            
        </body>
        </html>
        """  # noqa: W293
        base_notifier = MockBaseNotifier()

        actual_value = base_notifier._aggregate_all_summaries(
            [("mock-summary-generator-1", "unittest-html-1"), ("mock-summary-generator-2", "unittest-html-2")]
        )
        self.assertEqual(expected_value, actual_value)


class TestEmailNotifier(unittest.TestCase):
    @patch("todonotifier.notifier.smtplib")
    @patch("todonotifier.notifier.ssl", Mock())
    @patch("todonotifier.notifier.MIMEText", Mock())
    @patch("todonotifier.notifier.datetime", Mock())
    @patch("todonotifier.notifier.MIMEMultipart")
    @patch("todonotifier.notifier.EmailNotifier._aggregate_all_summaries", Mock())
    def test_notify_should_notify(self, stub_mime_multipart, stub_smtplib):
        dummy_sender_email = "unittest-sender-email"
        dummy_password = "unittest-password"
        dummy_receivers = ["unittest-receiver-1", "unittest-receiver-2"]
        spy_server = Mock()
        stub_smtplib.SMTP_SSL = FakeContextManager
        FakeContextManager.return_value = spy_server
        stub_mime_multipart.return_value = MagicMock()

        email_notifier = EmailNotifier(dummy_sender_email, dummy_password, None, None, dummy_receivers)
        email_notifier.notify([])

        spy_server.login.assert_called_once_with(dummy_sender_email, dummy_password)
        spy_server.sendmail.assert_called_once_with(dummy_sender_email, dummy_receivers, stub_mime_multipart.return_value.as_string.return_value)


SECRET_URL = "https://hooks.example.com/services/T000/B000/SECRETTOKEN"
SECRET_HEADER = "Bearer SUPERSECRETHEADER"
SECRET_BODY = b"SECRETBODY from the server"
SECRET_PASSWORD = "SUPERSECRETPASSWORD"
REPORTS = [("Report A", "<table><tr><td>a</td></tr></table>"), ("Report B", "<p>b</p>")]


def _response() -> MagicMock:
    """A successful response, usable as a context manager"""
    response = MagicMock()
    response.__enter__.return_value = response
    return response


def _http_error(code: int, retry_after: str = None) -> urllib.error.HTTPError:
    headers = Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return urllib.error.HTTPError(SECRET_URL, code, "Server said no", headers, BytesIO(SECRET_BODY))


def _sent_json(urlopen: Mock, call: int = -1) -> dict:
    return json.loads(urlopen.call_args_list[call][0][0].data.decode("utf-8"))


class OldStyleNotifier(BaseNotifier):
    """A notifier written against the original API: it only knows `notify`"""

    def __init__(self) -> None:
        super().__init__()
        self.received = None

    def notify(self, summary: List) -> None:
        self.received = summary


class TestBackwardsCompatibility(unittest.TestCase):
    def test_notify_result_calls_notify_for_old_style_subclasses(self):
        notifier = OldStyleNotifier()

        notifier.notify_result(make_scan_result(), REPORTS)

        self.assertEqual(REPORTS, notifier.received)

    def test_old_style_email_notifier_uses_ssl_and_logs_in_as_the_sender(self):
        with patch("todonotifier.notifier.smtplib") as stub_smtplib:
            stub_smtplib.SMTP_SSL = FakeContextManager
            FakeContextManager.return_value = server = Mock()

            EmailNotifier("me@example.com", SECRET_PASSWORD, "smtp.example.com", 465, ["you@example.com"]).notify(REPORTS)

        server.login.assert_called_once_with("me@example.com", SECRET_PASSWORD)
        server.starttls.assert_not_called()
        message = email.message_from_string(server.sendmail.call_args[0][2])
        self.assertEqual("me@example.com", message["From"])
        self.assertEqual(["text/html"], [part.get_content_type() for part in message.get_payload()])
        self.assertIn("Report A", message.get_payload(0).get_payload(decode=True).decode())

    def test_abstract_notify_can_be_called_through_super(self):
        self.assertIsNone(BaseNotifier.notify(OldStyleNotifier(), REPORTS))

    def test_email_notifier_without_receivers_still_constructs(self):
        self.assertEqual([], EmailNotifier("a", "b", "c", 1)._receivers)

    def test_max_items_must_be_positive(self):
        with self.assertRaises(ValueError):
            SlackWebhookNotifier(SECRET_URL, max_items=0)


class HttpNotifierTestCase(unittest.TestCase):
    def setUp(self):
        patcher = patch("todonotifier.notifier.urllib.request.urlopen")
        self.urlopen = patcher.start()
        self.addCleanup(patcher.stop)
        self.urlopen.return_value = _response()
        self.sleep = Mock()

    def _prepare(self, notifier):
        notifier._sleep = self.sleep
        return notifier


class TestSnapshots(HttpNotifierTestCase):
    def test_slack_payload(self):
        notifier = self._prepare(SlackWebhookNotifier(SECRET_URL, max_items=3))
        notifier.new_count = 2

        notifier.notify_result(make_scan_result(), REPORTS)

        assert_matches_snapshot(self, "slack.json", _sent_json(self.urlopen))

    def test_teams_payload(self):
        notifier = self._prepare(TeamsWebhookNotifier(SECRET_URL, max_items=3))
        notifier.new_count = 2

        notifier.notify_result(make_scan_result(), REPORTS)

        assert_matches_snapshot(self, "teams.json", _sent_json(self.urlopen))

    def test_webhook_payload(self):
        notifier = self._prepare(WebhookNotifier(SECRET_URL))
        notifier.new_count = 2

        notifier.notify_result(make_scan_result(), REPORTS)

        assert_matches_snapshot(self, "webhook.json", _sent_json(self.urlopen))

    def test_webhook_payload_round_trips_to_the_scan_result(self):
        result = make_scan_result()

        self._prepare(WebhookNotifier(SECRET_URL)).notify_result(result, [])

        self.assertEqual(result.to_dict(), ScanResult.from_dict(_sent_json(self.urlopen)["result"]).to_dict())

    def test_request_is_a_json_post_with_a_timeout(self):
        self._prepare(SlackWebhookNotifier(SECRET_URL)).notify_result(make_scan_result(), [])

        request = self.urlopen.call_args[0][0]
        self.assertEqual("POST", request.get_method())
        self.assertEqual(SECRET_URL, request.full_url)
        self.assertEqual("application/json; charset=utf-8", request.get_header("Content-type"))
        self.assertEqual("todonotifier", request.get_header("User-agent"))
        self.assertEqual(10, self.urlopen.call_args[1]["timeout"])

    def test_old_api_posts_the_report_names(self):
        for notifier, expected in (
            (SlackWebhookNotifier(SECRET_URL), {"text": "TODO Notifier generated reports: Report A, Report B"}),
            (
                WebhookNotifier(SECRET_URL),
                {"event": "todonotifier.reports", "text": "TODO Notifier generated reports: Report A, Report B", "reports": ["Report A", "Report B"]},
            ),
        ):
            with self.subTest(type(notifier).__name__):
                self._prepare(notifier).notify(REPORTS)

                self.assertEqual(expected, _sent_json(self.urlopen))

        self._prepare(TeamsWebhookNotifier(SECRET_URL)).notify([])
        card = _sent_json(self.urlopen)["attachments"][0]["content"]
        self.assertEqual("TODO Notifier generated reports: none", card["body"][0]["text"])
        self.assertEqual("1.4", card["version"])


class TestSlackPayload(HttpNotifierTestCase):
    def _send(self, result, **kwargs) -> dict:
        self._prepare(SlackWebhookNotifier(SECRET_URL, **kwargs)).notify_result(result, [])
        return _sent_json(self.urlopen)

    def test_has_fallback_text_header_totals_and_section_blocks(self):
        payload = self._send(make_scan_result())

        self.assertEqual("TODO digest: 10 open, 4 overdue, 3 stale, 2 due this week, 4 unowned", payload["text"])
        self.assertEqual(["header", "section", "section", "section", "section"], [block["type"] for block in payload["blocks"]])

    def test_truncation_keeps_to_slack_limits_and_says_how_many_are_missing(self):
        items = [
            make_item(f"src/file{index}.py", index + 1, "x" * 150, f"user{index % 7}", date_) for index, date_ in enumerate([TODAY.replace(year=2025)] * 800)
        ]
        result = ScanResult(items=items, generated_at=make_scan_result().generated_at)

        payload = self._send(result, max_items=800)

        blocks = payload["blocks"]
        self.assertEqual(50, len(blocks))
        self.assertTrue(all(len(block["text"]["text"]) <= 3000 for block in blocks if block["type"] == "section"))
        shown = sum(block["text"]["text"].count("\n\u2022 ") + block["text"]["text"].startswith("\u2022 ") for block in blocks[2:-1])
        last = blocks[-1]["text"]["text"]
        self.assertTrue(last.startswith("_...and ") and last.endswith(" more_"))
        missing = int(last.split()[1])
        self.assertGreater(missing, 0)
        self.assertEqual(800, shown + missing)

    def test_lists_are_cut_to_max_items_with_a_more_line(self):
        payload = self._send(make_scan_result(), max_items=1)

        texts = [block["text"]["text"] for block in payload["blocks"][2:]]
        self.assertIn("_...and 3 more_", texts[0])
        self.assertIn("_...and 2 more_", texts[1])

    def test_a_single_overlong_line_is_cut_to_the_section_limit(self):
        item = make_item("x" * 3500, 1, "m", "amy", TODAY.replace(year=2025), linked=False)

        payload = self._send(ScanResult(items=[item], generated_at=make_scan_result().generated_at))

        texts = [block["text"]["text"] for block in payload["blocks"]]
        self.assertTrue(all(len(text) <= 3000 for text in texts if text))
        self.assertTrue(any(text.endswith("\u2026") for text in texts))

    def test_special_characters_are_escaped_and_unsafe_links_dropped(self):
        item = make_item("a|b.py", 1, "<!channel> & <https://evil|click>", "amy", TODAY.replace(year=2025))
        item.web_url = "https://x.test/a|b"

        text = self._send(ScanResult(items=[item], generated_at=make_scan_result().generated_at))["blocks"][2]["text"]["text"]

        self.assertIn("&lt;!channel&gt; &amp; &lt;https://evil|click&gt;", text)
        self.assertIn("`a|b.py:1`", text)
        self.assertNotIn("<!channel>", text)

    def test_link_label_has_no_pipe(self):
        item = make_item("a|b.py", 1, "m", "amy", TODAY.replace(year=2025))
        item.web_url = "https://x.test/a%7Cb.py"

        text = self._send(ScanResult(items=[item], generated_at=make_scan_result().generated_at))["blocks"][2]["text"]["text"]

        self.assertIn("|a\u00a6b.py:1>", text)

    def test_empty_result_says_so(self):
        payload = self._send(ScanResult(generated_at=make_scan_result().generated_at))

        self.assertEqual("Nothing is overdue, stale or due this week.", payload["blocks"][2]["text"]["text"])


class TestTeamsPayload(HttpNotifierTestCase):
    def _body(self, result, **kwargs) -> list:
        self._prepare(TeamsWebhookNotifier(SECRET_URL, **kwargs)).notify_result(result, [])
        payload = _sent_json(self.urlopen)
        self.assertEqual("message", payload["type"])
        self.assertEqual("application/vnd.microsoft.card.adaptive", payload["attachments"][0]["contentType"])
        self.assertIsNone(payload["attachments"][0]["contentUrl"])
        return payload["attachments"][0]["content"]["body"]

    def test_card_has_title_facts_and_a_text_block_per_item(self):
        body = self._body(make_scan_result(), max_items=1)

        self.assertEqual("FactSet", body[1]["type"])
        self.assertEqual({"title": "Open", "value": "10"}, body[1]["facts"][0])
        texts = [block.get("text", "") for block in body]
        self.assertIn("...and 3 more", texts)
        self.assertTrue(any(text.startswith("[src/app.py:10](https://github.com/") for text in texts))

    def test_messages_cannot_inject_markdown_links(self):
        item = make_item("a.py", 1, "[click](https://evil.test)", "amy", TODAY.replace(year=2025), linked=False)

        body = self._body(ScanResult(items=[item], generated_at=make_scan_result().generated_at))

        self.assertEqual("a.py:1 \uff3bclick\uff3d(https://evil.test) (365 days overdue)", body[-1]["text"])
        self.assertNotIn("[", body[-1]["text"])
        self.assertNotIn("\\", body[-1]["text"])  # A backslash escape would be shown as it is

    def test_markdown_in_untrusted_text_is_neutralised_not_backslash_escaped(self):
        item = make_item("pkg/__init__.py", 4, "**bold** _italic_ `code` my_var_name", "ev*il_", TODAY.replace(year=2025), linked=False)

        body = self._body(ScanResult(items=[item], generated_at=make_scan_result().generated_at))
        texts = [block["text"] for block in body if "text" in block]

        self.assertIn("**ev\u2217il\uff3f** (1)", texts)  # Our own bold markers stay, the author's characters do not act as Markdown
        item_text = next(text for text in texts if "init" in text)
        self.assertEqual(
            "pkg/\uff3f\uff3finit\uff3f\uff3f.py:4 \u2217\u2217bold\u2217\u2217 \uff3fitalic\uff3f \u02cbcode\u02cb my_var_name (365 days overdue)", item_text
        )

    def test_links_to_the_line_keep_working(self):
        item = make_item("src/my_module[1].py", 7, "x", "amy", TODAY.replace(year=2025))
        item.web_url = "https://github.com/acme/widgets/blob/abc/src/my_module%5B1%5D.py#L7"

        body = self._body(ScanResult(items=[item], generated_at=make_scan_result().generated_at))

        self.assertIn("[src/my_module\uff3b1\uff3d.py:7](https://github.com/acme/widgets/blob/abc/src/my_module%5B1%5D.py#L7) x", body[-1]["text"])

    def test_the_names_of_the_reports_are_neutralised_too(self):
        notifier = self._prepare(TeamsWebhookNotifier(SECRET_URL))

        notifier.notify([("A_*[b]*_", "<p>x</p>")])

        text = _sent_json(self.urlopen)["attachments"][0]["content"]["body"][0]["text"]
        self.assertEqual("TODO Notifier generated reports: A\uff3f\u2217\uff3bb\uff3d\u2217\uff3f", text)

    def test_new_fact_and_empty_result(self):
        notifier = self._prepare(TeamsWebhookNotifier(SECRET_URL))
        notifier.new_count = 0

        notifier.notify_result(ScanResult(generated_at=make_scan_result().generated_at), [])

        body = _sent_json(self.urlopen)["attachments"][0]["content"]["body"]
        self.assertEqual({"title": "New", "value": "0"}, body[1]["facts"][-1])
        self.assertEqual("Nothing is overdue, stale or due this week.", body[2]["text"])


class TestRetries(HttpNotifierTestCase):
    def _notify(self, notifier=None):
        notifier = notifier or SlackWebhookNotifier(SECRET_URL)
        self._prepare(notifier).notify_result(make_scan_result(), [])

    def test_retries_on_500_and_429_then_succeeds(self):
        self.urlopen.side_effect = [_http_error(500), _http_error(429, "3"), _response()]

        self._notify()

        self.assertEqual(3, self.urlopen.call_count)
        self.assertEqual([1, 3], [call[0][0] for call in self.sleep.call_args_list])

    def test_gives_up_after_two_retries_and_raises_notification_error_without_secrets(self):
        self.urlopen.side_effect = [_http_error(500), _http_error(502), _http_error(503)]

        with self.assertRaises(NotificationError) as raised:
            self._notify()

        self.assertEqual(3, self.urlopen.call_count)
        self.assertEqual([1, 2], [call[0][0] for call in self.sleep.call_args_list])
        self.assertEqual("Slack webhook POST failed with HTTP 503 after 3 attempt(s)", str(raised.exception))
        self.assertIsNone(raised.exception.__cause__)
        self.assertIsNone(raised.exception.__context__)

    def test_does_not_retry_other_4xx(self):
        for code in (400, 401, 403, 404, 410):
            with self.subTest(code=code):
                self.urlopen.reset_mock()
                self.sleep.reset_mock()
                self.urlopen.side_effect = [_http_error(code)]

                with self.assertRaises(NotificationError) as raised:
                    self._notify()

                self.assertEqual(1, self.urlopen.call_count)
                self.sleep.assert_not_called()
                self.assertIn(f"HTTP {code}", str(raised.exception))

    def test_retries_network_errors(self):
        for error in (
            urllib.error.URLError(OSError("no route to " + SECRET_URL)),
            TimeoutError("timed out " + SECRET_URL),
            http.client.BadStatusLine(SECRET_URL),
            ConnectionResetError(SECRET_URL),
        ):
            with self.subTest(type(error).__name__):
                self.urlopen.reset_mock()
                self.urlopen.side_effect = [error, _response()]

                self._notify()

                self.assertEqual(2, self.urlopen.call_count)

    def test_network_error_that_never_recovers_raises_with_the_error_type_only(self):
        self.urlopen.side_effect = urllib.error.URLError(OSError("no route to " + SECRET_URL))

        with self.assertRaises(NotificationError) as raised:
            self._notify()

        self.assertEqual("Slack webhook POST failed with URLError (OSError) after 3 attempt(s)", str(raised.exception))

    def test_unexpected_errors_are_not_retried_and_their_message_is_dropped(self):
        self.urlopen.side_effect = ValueError("bad header " + SECRET_HEADER)

        with self.assertRaises(NotificationError) as raised:
            self._notify()

        self.assertEqual(1, self.urlopen.call_count)
        self.assertEqual("Slack webhook POST failed with unexpected ValueError after 1 attempt(s)", str(raised.exception))
        self.assertNotIn(SECRET_HEADER, "".join(traceback.format_exception(raised.exception)))

    def test_retry_delay(self):
        self.assertEqual(1, _retry_delay(None, 1))
        self.assertEqual(2, _retry_delay(None, 2))
        self.assertEqual(4, _retry_delay("Wed, 21 Oct 2026 07:28:00 GMT", 3))
        self.assertEqual(7.5, _retry_delay("7.5", 1))
        self.assertEqual(30, _retry_delay("86400", 1))
        self.assertEqual(0, _retry_delay("-5", 1))

    def test_retry_after_is_honoured_for_5xx_too(self):
        self.urlopen.side_effect = [_http_error(503, "5"), _response()]

        self._notify()

        self.sleep.assert_called_once_with(5)

    def test_default_sleep_is_time_sleep(self):
        with patch("todonotifier.notifier.time.sleep") as stub_sleep:
            notifier = SlackWebhookNotifier(SECRET_URL)
            self.urlopen.side_effect = [_http_error(500), _response()]

            notifier.notify_result(make_scan_result(), [])

        stub_sleep.assert_called_once_with(1)


class TestUrlAndHeaderRules(HttpNotifierTestCase):
    def test_only_https_urls_and_http_localhost_are_allowed(self):
        for url in ("https://hooks.example.com/x", "http://localhost:8080/x", "http://127.0.0.1/x", "https://127.0.0.1:9/x"):
            with self.subTest(url):
                SlackWebhookNotifier(url)

        for url in (
            "http://hooks.example.com/SECRET",
            "ftp://hooks.example.com/SECRET",
            "file:///etc/passwd",
            "https://",
            "SECRET",
            "",
            "http://localhost.evil.com/SECRET",
        ):
            with self.subTest(url):
                with self.assertRaises(ValueError) as raised:
                    TeamsWebhookNotifier(url)
                self.assertNotIn("SECRET", str(raised.exception))
                self.assertIn("https://", str(raised.exception))

    def test_custom_headers_are_sent_and_not_forwarded_on_redirects(self):
        notifier = self._prepare(WebhookNotifier(SECRET_URL, {"Authorization": SECRET_HEADER, "User-Agent": "mine"}))

        notifier.notify_result(make_scan_result(), [])

        request = self.urlopen.call_args[0][0]
        self.assertEqual(SECRET_HEADER, request.get_header("Authorization"))
        self.assertEqual("mine", request.get_header("User-agent"))
        self.assertNotIn("Authorization", request.headers)

    def test_a_custom_content_type_replaces_the_default(self):
        notifier = self._prepare(WebhookNotifier(SECRET_URL, {"content-type": "application/vnd.x+json"}))

        notifier.notify_result(make_scan_result(), [])

        self.assertEqual("application/vnd.x+json", self.urlopen.call_args[0][0].get_header("Content-type"))

    def test_invalid_headers_are_rejected_without_echoing_values(self):
        for headers, expected in (
            ({"Authorization": "Bearer x\r\nX-Evil: " + SECRET_HEADER}, "'Authorization' has an invalid value"),
            ({"X-Non-Ascii": "caf\u00e9"}, "'X-Non-Ascii' has an invalid value"),
            ({"X-Number": 5}, "'X-Number' has an invalid value"),
            ({"Bad Name": "x"}, "invalid header name"),
            ({"": "x"}, "invalid header name"),
            ({5: "x"}, "invalid header name"),
        ):
            with self.subTest(headers):
                with self.assertRaises(ValueError) as raised:
                    WebhookNotifier(SECRET_URL, headers)
                self.assertIn(expected, str(raised.exception))
                self.assertNotIn("SUPERSECRET", str(raised.exception))

    def test_repr_has_no_secrets(self):
        for notifier in (SlackWebhookNotifier(SECRET_URL, 5), TeamsWebhookNotifier(SECRET_URL), WebhookNotifier(SECRET_URL, {"Authorization": SECRET_HEADER})):
            self.assertNotIn("SECRET", repr(notifier))
            self.assertNotIn("SECRET", str(notifier))
        self.assertEqual("SlackWebhookNotifier(max_items=5)", repr(SlackWebhookNotifier(SECRET_URL, 5)))


class TestNoSecretsInLogsOrErrors(HttpNotifierTestCase):
    def _assert_clean(self, text: str) -> None:
        for secret in ("SECRETTOKEN", "hooks.example.com", "SUPERSECRETHEADER", "SECRETBODY", "Server said no"):
            self.assertNotIn(secret, text)

    def test_failing_notifiers_never_log_or_raise_urls_headers_or_bodies(self):
        for notifier in (
            SlackWebhookNotifier(SECRET_URL),
            TeamsWebhookNotifier(SECRET_URL),
            WebhookNotifier(SECRET_URL, {"Authorization": SECRET_HEADER}),
        ):
            for errors in (
                [_http_error(500), _http_error(500), _http_error(500)],
                [_http_error(404)],
                [urllib.error.URLError(OSError(SECRET_URL))] * 3,
                [ValueError(SECRET_URL + SECRET_HEADER)],
            ):
                with self.subTest(type(notifier).__name__, error=repr(errors[0])[:30]):
                    self.urlopen.side_effect = errors
                    self._prepare(notifier)

                    with self.assertLogs("todonotifier.notifier", level="DEBUG") as logs:
                        with self.assertRaises(NotificationError) as raised:
                            notifier.notify_result(make_scan_result(), REPORTS)

                    self._assert_clean("\n".join(logs.output))
                    self._assert_clean(str(raised.exception) + repr(raised.exception) + "".join(traceback.format_exception(raised.exception)))

    def test_failure_log_names_the_notifier_status_and_attempt(self):
        self.urlopen.side_effect = [_http_error(500), _http_error(500), _http_error(500)]
        notifier = self._prepare(SlackWebhookNotifier(SECRET_URL))

        with self.assertLogs("todonotifier.notifier", level="WARNING") as logs:
            with self.assertRaises(NotificationError):
                notifier.notify_result(make_scan_result(), [])

        self.assertEqual([f"WARNING:todonotifier.notifier:Slack webhook POST failed with HTTP 500 (attempt {attempt}/3)" for attempt in (1, 2, 3)], logs.output)

    def test_success_log_has_no_secrets(self):
        notifier = self._prepare(WebhookNotifier(SECRET_URL, {"Authorization": SECRET_HEADER}))

        with self.assertLogs("todonotifier.notifier", level="DEBUG") as logs:
            notifier.notify_result(make_scan_result(), [])

        self.assertEqual(["INFO:todonotifier.notifier:Webhook notification sent"], logs.output)


class TestEmailNotifier2(unittest.TestCase):
    def _notifier(self, **kwargs) -> EmailNotifier:
        return EmailNotifier("me@example.com", SECRET_PASSWORD, "smtp.example.com", kwargs.pop("port", 465), ["a@example.com", "b@example.com"], **kwargs)

    def test_starttls_connects_in_plain_text_and_upgrades_before_login(self):
        with patch("todonotifier.notifier.smtplib") as stub_smtplib, patch("todonotifier.notifier.ssl") as stub_ssl:
            server = stub_smtplib.SMTP.return_value.__enter__.return_value

            self._notifier(port=587, starttls=True, username="login-name").notify(REPORTS)

        stub_smtplib.SMTP.assert_called_once_with("smtp.example.com", 587, timeout=30)
        stub_smtplib.SMTP_SSL.assert_not_called()
        self.assertEqual(["starttls", "login", "sendmail"], [call[0] for call in server.method_calls if call[0] in ("starttls", "login", "sendmail")])
        server.starttls.assert_called_once_with(context=stub_ssl.create_default_context.return_value)
        server.login.assert_called_once_with("login-name", SECRET_PASSWORD)
        self.assertEqual(["a@example.com", "b@example.com"], server.sendmail.call_args[0][1])

    def test_ssl_is_used_without_starttls(self):
        with patch("todonotifier.notifier.smtplib") as stub_smtplib:
            self._notifier().notify(REPORTS)

        stub_smtplib.SMTP_SSL.assert_called_once()
        self.assertEqual(("smtp.example.com", 465), stub_smtplib.SMTP_SSL.call_args[0])
        self.assertEqual(30, stub_smtplib.SMTP_SSL.call_args[1]["timeout"])
        stub_smtplib.SMTP.assert_not_called()

    def test_notify_result_sends_plain_text_and_html_with_the_reports_below_the_digest(self):
        with patch("todonotifier.notifier.smtplib") as stub_smtplib:
            server = stub_smtplib.SMTP_SSL.return_value.__enter__.return_value
            notifier = self._notifier(max_items=2)
            notifier.new_count = 1

            notifier.notify_result(make_scan_result(), REPORTS)

        message = email.message_from_string(server.sendmail.call_args[0][2])
        self.assertEqual("TODO digest 2026-05-01: 4 overdue, 3 stale", message["Subject"])
        self.assertEqual("a@example.com, b@example.com", message["To"])
        parts = message.get_payload()
        self.assertEqual(["text/plain", "text/html"], [part.get_content_type() for part in parts])
        text = parts[0].get_payload(decode=True).decode()
        html = parts[1].get_payload(decode=True).decode()
        self.assertIn("10 open, 4 overdue, 3 stale, 2 due this week, 4 unowned, 1 new", text)
        self.assertIn("Full reports (Report A, Report B) are in the HTML version", text)
        self.assertIn("Handle &lt;None&gt; &amp; empty input", html)
        self.assertIn('<a href="https://github.com/acme/widgets/blob/', html)
        self.assertIn("...and 2 more", html)
        self.assertLess(html.index("Overdue (4)"), html.index("<table><tr><td>a</td></tr></table>"))
        self.assertIn('<h3 style="font-size: 14px;">Report B</h3>', html)
        self.assertNotIn(SECRET_PASSWORD, server.sendmail.call_args[0][2])

    def test_notify_result_without_reports_and_without_links(self):
        item = make_item("a.py", 1, "<script>alert(1)</script>", "amy", TODAY.replace(year=2025), linked=False)
        result = ScanResult(items=[item], generated_at=make_scan_result().generated_at)
        with patch("todonotifier.notifier.smtplib") as stub_smtplib:
            server = stub_smtplib.SMTP_SSL.return_value.__enter__.return_value

            self._notifier().notify_result(result, [])

        parts = email.message_from_string(server.sendmail.call_args[0][2]).get_payload()
        self.assertNotIn("Full reports", parts[0].get_payload(decode=True).decode())
        html = parts[1].get_payload(decode=True).decode()
        self.assertIn("<code>a.py:1</code> &lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn('<h2 style="font-size: 16px;">Reports</h2>', html)

    def test_notify_result_for_an_empty_scan(self):
        with patch("todonotifier.notifier.smtplib") as stub_smtplib:
            server = stub_smtplib.SMTP_SSL.return_value.__enter__.return_value

            self._notifier().notify_result(ScanResult(generated_at=make_scan_result().generated_at), [])

        html = email.message_from_string(server.sendmail.call_args[0][2]).get_payload(1).get_payload(decode=True).decode()
        self.assertIn("Nothing is overdue, stale or due this week.", html)

    def test_repr_has_no_password(self):
        self.assertNotIn(SECRET_PASSWORD, repr(self._notifier()))
        self.assertIn("smtp.example.com", repr(self._notifier()))


class TestEmailFromEnv(unittest.TestCase):
    ENV = {
        "TODO_SMTP_HOST": "smtp.example.com",
        "TODO_SMTP_PORT": "2525",
        "TODO_SMTP_SENDER": "me@example.com",
        "TODO_SMTP_RECIPIENTS": "a@example.com, b@example.com,,",
        "TODO_SMTP_USERNAME": "login-name",
        "TODO_SMTP_PASSWORD": SECRET_PASSWORD,
        "TODO_SMTP_STARTTLS": "true",
    }

    def test_reads_every_variable(self):
        notifier = EmailNotifier.from_env(environ=self.ENV)

        self.assertEqual(
            ("smtp.example.com", 2525, "me@example.com", ["a@example.com", "b@example.com"], "login-name", SECRET_PASSWORD, True),
            (notifier._host, notifier._port, notifier._sender_email, notifier._receivers, notifier._username, notifier._password, notifier._starttls),
        )

    def test_defaults(self):
        env = {key: value for key, value in self.ENV.items() if key not in ("TODO_SMTP_PORT", "TODO_SMTP_USERNAME", "TODO_SMTP_STARTTLS")}

        plain = EmailNotifier.from_env(environ=env)
        starttls = EmailNotifier.from_env(environ={**env, "TODO_SMTP_STARTTLS": "1"})

        self.assertEqual((465, False, "me@example.com"), (plain._port, plain._starttls, plain._username))
        self.assertEqual((587, True), (starttls._port, starttls._starttls))
        self.assertFalse(EmailNotifier.from_env(environ={**env, "TODO_SMTP_STARTTLS": " No "})._starttls)

    def test_custom_prefix(self):
        env = {key.replace("TODO_SMTP_", "MAIL_"): value for key, value in self.ENV.items()}

        self.assertEqual("smtp.example.com", EmailNotifier.from_env("MAIL_", environ=env)._host)

    def test_defaults_to_os_environ(self):
        with patch.dict(os.environ, self.ENV):
            self.assertEqual("smtp.example.com", EmailNotifier.from_env()._host)

    def test_missing_required_variables_are_named_without_values(self):
        for name in ("HOST", "SENDER", "RECIPIENTS", "PASSWORD"):
            with self.subTest(name):
                env = {key: value for key, value in self.ENV.items() if key != f"TODO_SMTP_{name}"}

                with self.assertRaises(NotifierConfigError) as raised:
                    EmailNotifier.from_env(environ=env)

                self.assertIn(f"TODO_SMTP_{name}", str(raised.exception))
                for value in env.values():
                    self.assertNotIn(value, str(raised.exception))

    def test_empty_variable_counts_as_missing(self):
        with self.assertRaises(NotifierConfigError) as raised:
            EmailNotifier.from_env(environ={**self.ENV, "TODO_SMTP_PASSWORD": ""})

        self.assertIn("TODO_SMTP_PASSWORD", str(raised.exception))

    def test_invalid_values_name_the_variable_only(self):
        for name, value in (("PORT", "abc"), ("PORT", "0"), ("PORT", "70000"), ("STARTTLS", "maybe"), ("RECIPIENTS", " , ")):
            with self.subTest(name=name, value=value):
                with self.assertRaises(NotifierConfigError) as raised:
                    EmailNotifier.from_env(environ={**self.ENV, f"TODO_SMTP_{name}": value})

                self.assertIn(f"TODO_SMTP_{name}", str(raised.exception))
                self.assertNotIn(f"'{value}'", str(raised.exception))
                self.assertNotIn(SECRET_PASSWORD, str(raised.exception))


class TestBuildNotifiers(unittest.TestCase):
    ENV = {
        "SLACK_URL": "https://hooks.slack.com/services/T/B/SECRET1",
        "TEAMS_URL": "https://example.webhook.office.com/SECRET2",
        "HOOK_URL": "https://example.com/hook/SECRET3",
        "HOOK_HEADERS": '{"Authorization": "Bearer SECRET4"}',
        "SMTP_USER": "login-name",
        "SMTP_PASS": SECRET_PASSWORD,
    }

    def _tables(self) -> dict:
        return {
            "slack": {"enabled": True, "webhook_env": "SLACK_URL", "max_items": 5},
            "teams": {"enabled": True, "webhook_env": "TEAMS_URL"},
            "webhook": {"enabled": True, "url_env": "HOOK_URL", "headers_env": "HOOK_HEADERS"},
            "email": {
                "enabled": True,
                "smtp_host": "smtp.example.com",
                "sender": "me@example.com",
                "recipients": ["a@example.com"],
                "password_env": "SMTP_PASS",
            },
        }

    def test_builds_every_notifier_in_order(self):
        notifiers = build_notifiers(self._tables(), self.ENV)

        self.assertEqual([SlackWebhookNotifier, TeamsWebhookNotifier, WebhookNotifier, EmailNotifier], [type(notifier) for notifier in notifiers])
        self.assertTrue(all(isinstance(notifier, DigestNotifier) for notifier in notifiers))
        self.assertEqual((5, "https://hooks.slack.com/services/T/B/SECRET1"), (notifiers[0]._max_items, notifiers[0]._url))
        self.assertEqual(10, notifiers[1]._max_items)
        self.assertEqual({"Authorization": "Bearer SECRET4"}, notifiers[2]._headers)
        self.assertEqual(
            ("smtp.example.com", 465, False, "me@example.com", SECRET_PASSWORD),
            (notifiers[3]._host, notifiers[3]._port, notifiers[3]._starttls, notifiers[3]._username, notifiers[3]._password),
        )

    def test_webhook_without_headers_and_email_with_starttls_and_username(self):
        tables = self._tables()
        del tables["webhook"]["headers_env"]
        tables["email"].update({"starttls": True, "username_env": "SMTP_USER", "smtp_port": 2587})

        notifiers = build_notifiers(tables, self.ENV)

        self.assertEqual({}, notifiers[2]._headers)
        self.assertEqual((2587, True, "login-name"), (notifiers[3]._port, notifiers[3]._starttls, notifiers[3]._username))

    def test_starttls_default_port(self):
        tables = {"email": {**self._tables()["email"], "starttls": True}}

        self.assertEqual(587, build_notifiers(tables, self.ENV)[0]._port)

    def test_disabled_tables_are_skipped_even_when_their_variables_are_missing(self):
        tables = self._tables()
        tables["slack"]["enabled"] = False

        self.assertEqual(3, len(build_notifiers(tables, {key: value for key, value in self.ENV.items() if key != "SLACK_URL"})))
        self.assertEqual([], build_notifiers({}, self.ENV))

    def test_table_without_enabled_key_is_enabled(self):
        self.assertEqual(1, len(build_notifiers({"slack": {"webhook_env": "SLACK_URL"}}, self.ENV)))

    def test_missing_variable_is_named_and_values_are_never_shown(self):
        for table_name, variable in (
            ("slack", "SLACK_URL"),
            ("teams", "TEAMS_URL"),
            ("webhook", "HOOK_URL"),
            ("webhook", "HOOK_HEADERS"),
            ("email", "SMTP_PASS"),
            ("email", "SMTP_USER"),
        ):
            with self.subTest(variable):
                tables = self._tables()
                tables["email"]["username_env"] = "SMTP_USER"
                env = {key: value for key, value in self.ENV.items() if key != variable}

                with self.assertRaises(NotifierConfigError) as raised:
                    build_notifiers({table_name: tables[table_name]}, env)

                message = str(raised.exception)
                self.assertIn(variable, message)
                self.assertIn(f"notify.{table_name}.", message)
                for value in env.values():
                    self.assertNotIn(value, message)

    def test_invalid_url_value_is_reported_without_echoing_it(self):
        for table_name, variable in (("slack", "SLACK_URL"), ("webhook", "HOOK_URL")):
            with self.subTest(table_name):
                tables = self._tables()
                env = {**self.ENV, variable: "http://evil.example.com/SECRET9"}

                with self.assertRaises(NotifierConfigError) as raised:
                    build_notifiers({table_name: tables[table_name]}, env)

                self.assertIn(f"Invalid settings for notify.{table_name}", str(raised.exception))
                self.assertNotIn("SECRET9", str(raised.exception))
                self.assertNotIn("evil", str(raised.exception))

    def test_invalid_header_json_is_reported_without_echoing_it(self):
        for raw in ("not json SECRET5", '["SECRET5"]', '{"a": 5}'):
            with self.subTest(raw):
                with self.assertRaises(NotifierConfigError) as raised:
                    build_notifiers({"webhook": self._tables()["webhook"]}, {**self.ENV, "HOOK_HEADERS": raw})

                self.assertIn("HOOK_HEADERS", str(raised.exception))
                self.assertNotIn("SECRET5", str(raised.exception))

    def test_unknown_notifier(self):
        with self.assertRaises(NotifierConfigError) as raised:
            build_notifiers({"pager": {"enabled": True}}, self.ENV)

        self.assertIn("'pager'", str(raised.exception))

    def test_defaults_to_os_environ(self):
        with patch.dict(os.environ, self.ENV):
            self.assertEqual(1, len(build_notifiers({"slack": {"webhook_env": "SLACK_URL"}})))

    def test_accepts_the_tables_validated_by_the_config_file_loader(self):
        config = (
            "[notify.slack]\nwebhook_env = 'SLACK_URL'\nmax_items = 3\n"
            "[notify.teams]\nwebhook_env = 'TEAMS_URL'\nenabled = false\n"
            "[notify.webhook]\nurl_env = 'HOOK_URL'\nheaders_env = 'HOOK_HEADERS'\n"
            "[notify.email]\nsmtp_host = 'smtp.example.com'\nsmtp_port = 587\nsender = 'me@example.com'\nrecipients = ['a@example.com']\n"
            "username_env = 'SMTP_USER'\npassword_env = 'SMTP_PASS'\nstarttls = true\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, ".todonotifier.toml")
            with open(path, "w") as config_file:
                config_file.write(config)

            project_config = resolve_project_config({}, path)

        notifiers = build_notifiers(project_config.notify, self.ENV)

        self.assertEqual([SlackWebhookNotifier, WebhookNotifier, EmailNotifier], [type(notifier) for notifier in notifiers])
        self.assertEqual(3, notifiers[0]._max_items)
        self.assertEqual((587, True, "login-name"), (notifiers[2]._port, notifiers[2]._starttls, notifiers[2]._username))
