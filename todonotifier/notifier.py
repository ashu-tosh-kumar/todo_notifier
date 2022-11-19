""" This module is used to send todo notifications to users
"""
import smtplib
import ssl
from abc import ABC, abstractmethod
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Tuple, Union


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

    @abstractmethod
    def notify(self, summary: List[Tuple[str, str]]) -> None:
        """Abstract method to send notification to users via method setup by users

        Args:
            summary (List[Tuple[str, str]]): List of tuples where each tuple consists of summary name and generated summary html
        """
        pass


class EmailNotifier(BaseNotifier):
    def __init__(self, sender_email: str, password: str, host: str, port: int, receivers: Union[List[str], None] = None) -> None:
        """Initializer for `EmailNotifier` class

        Args:
            sender_email (str): Email id from which email needs to be sent
            password (str): Password for email id `sender_email`
            host (str): Host for sending email for e.g. `smtp.gmail.com` for Gmail
            port (int): Port for sending email for e.g. `465` for Gmail
            receivers (Union[List[str], None], optional): List of receivers. Defaults to None.
        """
        self._sender_email = sender_email
        self._receivers = receivers or []
        self._password = password
        self._host = host
        self._port = port
        super().__init__()

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
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self._host, self._port, context=context) as server:
            server.login(self._sender_email, self._password)
            server.sendmail(self._sender_email, self._receivers, message.as_string())
