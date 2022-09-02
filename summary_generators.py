from abc import ABC, abstractmethod
from datetime import datetime
from typing import TypeVar

from constants import UNKNOWN_USER_NAME
from models import TODO

T = TypeVar("T")


class BaseSummaryGenerator(ABC):
    def __init__(self, name: str, container: T) -> None:
        """Initializer for `BaseSummaryGenerator`

        Args:
            name (str): Name of the respective Summary Generator
            container (T): A container in which `generate_summary` would add info of the current todo object, It could be a list or dict or sth else
        """
        self._name = name
        self._container = container

    @property
    def name(self) -> str:
        """Getter for `name`

        Returns:
            str: Name of the respective summary generator
        """
        return self._name

    @abstractmethod
    def generate_summary(self, todo_obj: TODO) -> None:
        """Abstract function to generate_summary summary

        Args:
            todo_obj (TODO): todo object
        """
        pass

    @abstractmethod
    def generate_html(self) -> str:
        """Generates the html representation of the respective summary to be sent as notifications to users

        Returns:
            str: String showing HTMl representation of the respective summary
        """
        pass


class ByModuleSummaryGenerator(BaseSummaryGenerator):
    def generate_summary(self, todo_obj: TODO) -> None:
        """Generates summary for each module

        Args:
            todo_obj (TODO): todo object
        """
        self._container: dict

        user_name = todo_obj.user.user_name if todo_obj.user.user_name else UNKNOWN_USER_NAME

        if todo_obj.module not in self._container:
            self._container[todo_obj.module] = [
                [
                    user_name,
                    todo_obj.user.user_email_id,
                    todo_obj.msg,
                    todo_obj.position.line_no,
                    str(todo_obj.completion_date),
                ]
            ]
        else:
            self._container[todo_obj.module].append(
                [
                    user_name,
                    todo_obj.user.user_email_id,
                    todo_obj.msg,
                    todo_obj.position.line_no,
                    str(todo_obj.completion_date),
                ]
            )

    def generate_html(self) -> str:
        """Generates the html representation showing module wise summary of todo items

        Returns:
            str: String showing HTMl representation of the respective summary
        """
        tables = ""
        for module in self._container:
            table = """
            <table>
            <tr>
                <th>User Name</th>
                <th>User Email ID</th>
                <th>Message</th>
                <th>Line No.</th>
                <th>Completion Date</th>
            </tr>
            """
            for todo_item in self._container[module]:
                table += f"""
                <tr>
                    <td>{todo_item[0]}</td>
                    <td>{todo_item[1]}</td>
                    <td>{todo_item[2]}</td>
                    <td>{todo_item[3]}</td>
                    <td>{todo_item[4]}</td>
                </tr>
                """
            table += """
            </table>
            """

            tables += f"""
            <h2>{module}</h2>
            <p>
                {table}
            </p><br>
            """

        return tables


class ExpiredTodosByUserSummaryGenerator(BaseSummaryGenerator):
    def generate_summary(self, todo_obj: TODO) -> None:
        """Generates summary for all expired todo items by user

        Args:
            todo_obj (TODO): todo object
            expired_todos_by_user_list (dict): Dictionary with user_name as key and corresponding expired todo items as value
        """
        self._container: list

        curr_date = datetime.today().date()
        user_name = todo_obj.user.user_name if todo_obj.user.user_name else UNKNOWN_USER_NAME

        if curr_date > todo_obj.completion_date:
            if user_name not in self._container:
                self._container[user_name] = [
                    [
                        todo_obj.user.user_email_id,
                        todo_obj.msg,
                        todo_obj.module,
                        todo_obj.position.line_no,
                        str(todo_obj.completion_date),
                    ]
                ]
            else:
                self._container[user_name].append(
                    [
                        todo_obj.msg,
                        todo_obj.module,
                        todo_obj.position.line_no,
                        str(todo_obj.completion_date),
                    ]
                )

    def generate_html(self, user_name: str) -> str:
        """Generates the html representation of the user-wise summary of expired todo items

        Args:
            user_name (str): User name for whom html representation needs to be generated

        Returns:
            str: String showing HTMl representation of the respective summary
        """
        table = """
            <table>
            <tr>
                <th>User Name</th>
                <th>User Email ID</th>
                <th>Message</th>
                <th>Line No.</th>
                <th>Completion Date</th>
            </tr>
            """
        for todo_item in self._container.get(user_name):
            table += f"""
                <tr>
                    <td>{todo_item[0]}</td>
                    <td>{todo_item[1]}</td>
                    <td>{todo_item[2]}</td>
                    <td>{todo_item[3]}</td>
                    <td>{todo_item[4]}</td>
                </tr>
                """
            table += """
            </table>
            """

        tables = f"""
            <h2>Expired TODOs for {user_name}</h2>
            <p>
                {table}
            </p>
            """
        return tables


class UpcomingWeekTodosByUserSummaryGenerator(BaseSummaryGenerator):
    def generate_summary(self, todo_obj: TODO) -> None:
        """Generates summary for all upcoming todo items by user

        Args:
            todo_obj (TODO): todo object
        """
        self._container: list

        curr_date = datetime.today().date()
        user_name = todo_obj.user.user_name if todo_obj.user.user_name else UNKNOWN_USER_NAME

        if curr_date < todo_obj.completion_date and (todo_obj.completion_date - curr_date).days <= 7:
            if user_name not in self._container:
                self._container[user_name] = [
                    [
                        todo_obj.user.user_email_id,
                        todo_obj.msg,
                        todo_obj.module,
                        todo_obj.position.line_no,
                        str(todo_obj.completion_date),
                    ]
                ]
            else:
                self._container[user_name].append(
                    [
                        todo_obj.msg,
                        todo_obj.module,
                        todo_obj.position.line_no,
                        str(todo_obj.completion_date),
                    ]
                )

    def generate_html(self, user_name: str) -> str:
        """Generates the html representation of the user-wise summary of the upcoming (within a week) todo items

        Args:
            user_name (str): User name for whom html representation needs to be generated

        Returns:
            str: String showing HTMl representation of the respective summary
        """
        table = """
            <table>
            <tr>
                <th>User Name</th>
                <th>User Email ID</th>
                <th>Message</th>
                <th>Line No.</th>
                <th>Completion Date</th>
            </tr>
            """
        for todo_item in self._container.get(user_name):
            table += f"""
                <tr>
                    <td>{todo_item[0]}</td>
                    <td>{todo_item[1]}</td>
                    <td>{todo_item[2]}</td>
                    <td>{todo_item[3]}</td>
                    <td>{todo_item[4]}</td>
                </tr>
                """
            table += """
            </table>
            """

        tables = f"""
            <h2>Upcoming TODOs for {user_name}</h2>
            <p>
                {table}
            </p>
            """
        return tables
