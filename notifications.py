""" This module is used to send todo notifications to users
"""
import smtplib
import ssl
from abc import ABC, abstractmethod
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from constants import DEFAULT_SUMMARY_GENERATORS_ENUM
from summary_generators import BaseSummaryGenerator


class BaseNotifier(ABC):
    def __init__(self) -> None:
        """ Initializer for `BaseNotifier`
        """
        pass

    @abstractmethod
    def notify(self, summary_generators: List[BaseSummaryGenerator]) -> None:
        """ Abstract method allowing sending automated notifications of summary of todo items

        Args:
            summary_generators (List[BaseSummaryGenerator]): List of summary generators to generate various kind of summary of todo items
        """
        pass


class EmailNotifier(BaseNotifier):
    def __init__(self, sender_email: str, password: str, receivers: List[str] = None) -> None:
        """ Initializer for `EmailNotifier` class

        Args:
            sender_email (str): Email id from which email needs to be sent
            password (str): Password for email id `sender_email`
            receivers (List[str], optional): List of receivers. Defaults to None.
        """
        self._sender_email = sender_email
        self._receivers = receivers or []
        self._password = password
        super().__init__()

    def _send_email(self, receivers_str: str, html: str, receivers_list: List[str]) -> None:
        """ Sends email to `receivers_list` with `html` content

        Args:
            receivers_str (str): String containing list of receivers separated by comma (,)
            html (str): HTML representation of the email content that needs to be sent
            receivers_list (List[str]): List of email ids to which email needs to be sent
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = f"TODO Summary - {datetime.today().date()}"
        message["From"] = self._sender_email
        message["To"] = receivers_str

        html = MIMEText(html, "html")
        message.attach(html)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(self._sender_email, self._password)
            server.sendmail(
                self._sender_email, receivers_list, message.as_string()
            )

    def notify(self, summary_generators: List[BaseSummaryGenerator]) -> None:
        """ Allows sending automated notifications of summary of todo items

        Args:
            summary_generators (List[BaseSummaryGenerator]): List of summary generators to generate various kind of summary of todo items
        """
        user_summary_generator_expired = None
        user_summary_generator_upcoming = None

        html = """\
        <html>
        <body>
        """

        for summary_generator in summary_generators:
            if summary_generator.name == DEFAULT_SUMMARY_GENERATORS_ENUM.EXPIRED_TODO_BY_USER:
                user_summary_generator_expired = summary_generator
            elif summary_generator.name == DEFAULT_SUMMARY_GENERATORS_ENUM.UPCOMING_TODO_BY_USER:
                user_summary_generator_upcoming = summary_generator
            else:
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

        if user_summary_generator_expired is not None:
            for user in user_summary_generator_expired._container:
                user_html = f"""\
                <html>
                <body>
                <p>
                    {user_summary_generator_expired.generate_html()}
                </p>
                """
                if user_summary_generator_upcoming is not None:
                    user_html += f"""
                    <br><p>
                        {user_summary_generator_upcoming.generate_html()}
                    </p>
                    """
                user_html += """
                </body>
                </html>
                """

            user_email_id = user_summary_generator_expired._container[user][1]
            self._send_email(user_email_id, user_html, [user_email_id])

        self._send_email(", ".join(self._receivers), html, self._receivers)
