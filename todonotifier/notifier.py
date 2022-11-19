""" This module is used to send todo notifications to users
"""
import smtplib
import ssl
from abc import ABC, abstractmethod
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Union

from todonotifier.summary_generators import BaseSummaryGenerator


class BaseNotifier(ABC):
    def __init__(self) -> None:
        """Initializer for `BaseNotifier`"""
        pass

    def _aggregate_all_summaries(self, summary_generators: List[BaseSummaryGenerator]) -> str:
        """Abstract method allowing to aggregate all summaries together to be sent

        Args:
            summary_generators (List[BaseSummaryGenerator]): List of summary generators to generate various kind of summary of todo items

        Returns:
            str: Returns the string representing aggregation of all summaries in their html format
        """
        html = """\
        <html>
        <body>
        """

        for summary_generator in summary_generators:
            html += f"""
            <h1>{summary_generator.name}</h1>
            <p>
                {summary_generator.generate_html()}
            </p><br>
            """

        html += """
        </body>
        </html>
        """

        return html

    @abstractmethod
    def notify(self, summary_generators: List[BaseSummaryGenerator]) -> None:
        """Abstract method to send notification to users via method setup by users

        Args:
            summary_generators (List[BaseSummaryGenerator]): List of summary generators to generate various kind of summary of todo items
        """
        pass


class EmailNotifier(BaseNotifier):
    def __init__(self, sender_email: str, password: str, receivers: Union[List[str], None] = None) -> None:
        """Initializer for `EmailNotifier` class

        Args:
            sender_email (str): Email id from which email needs to be sent
            password (str): Password for email id `sender_email`
            receivers (Union[List[str], None], optional): List of receivers. Defaults to None.
        """
        self._sender_email = sender_email
        self._receivers = receivers or []
        self._password = password
        super().__init__()

    def notify(self, summary_generators: List[BaseSummaryGenerator]) -> None:
        """Sends email to `receivers_list` with `html` content

        Args:
            summary_generators (List[BaseSummaryGenerator]): List of summary generators to generate various kind of summary of todo items
        """
        html = self._aggregate_all_summaries(summary_generators)
        receivers_str = ", ".join(self._receivers)

        message = MIMEMultipart("alternative")
        message["Subject"] = f"TODO Summary - {datetime.today().date()}"
        message["From"] = self._sender_email
        message["To"] = receivers_str

        html = MIMEText(html, "html")
        message.attach(html)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(self._sender_email, self._password)
            server.sendmail(self._sender_email, self._receivers, message.as_string())
