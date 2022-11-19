import unittest
from typing import List
from unittest.mock import MagicMock, Mock, patch

from tests.mocks import FakeContextManager
from todonotifier.notifier import BaseNotifier, EmailNotifier
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
