import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, TypeVar

from constants import DEFAULT_SUMMARY_GENERATORS_ENUM, UNKNOWN_USER_NAME
from models import TODO

T = TypeVar("T")

# logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


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

    @property
    def container(self) -> str:
        """Getter for `container`

        Returns:
            str: container of the respective summary generator
        """
        return self._container

    @abstractmethod
    def generate_summary(self, all_todos_objs: Dict[str, List[TODO]]) -> None:
        """Abstract function to generate_summary summary

        Args:
            all_todos_objs (Dict[str, List[TODO]]):  Key-value pair where key is relative path of file parsed and value is list of todo objects in that file
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
    def __init__(self, name: str = DEFAULT_SUMMARY_GENERATORS_ENUM.TODO_BY_MODULE, container: Dict[str, List[List[str]]] = None) -> None:
        """Initializer for `ByModuleSummaryGenerator`

        Args:
            name (str, optional): Name of the respective Summary Generator. Defaults to DEFAULT_SUMMARY_GENERATORS_ENUM.TODO_BY_MODULE.
            container (Dict[str, List[List[str]], optional): A container in which `generate_summary` would add info of the current todo object. Defaults to {}.
        """
        super().__init__(name=name, container=container or {})

    def generate_summary(self, all_todos_objs: Dict[str, List[TODO]]) -> None:
        """Generates summary for each module

        Args:
            all_todos_objs (Dict[str, List[TODO]]):  Key-value pair where key is relative path of file parsed and value is list of todo objects in that file
        """
        logger.info(f"Generating summary: {self.name}")

        for module in all_todos_objs:
            logger.info(f"Generating summary: {self.name} for module: {module}")
            for todo_obj in all_todos_objs[module]:
                user_name = todo_obj.user.user_name

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

        logger.info(f"Summary generated: {self.container}")

    def generate_html(self) -> str:
        """Generates the html representation showing module wise summary of todo items

        Returns:
            str: String showing HTMl representation of the respective summary
        """
        logger.info(f"Generating html for: {self.name}")

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

        logger.info(f"HTML generated: {tables}")
        return tables


class ExpiredTodosByUserSummaryGenerator(BaseSummaryGenerator):
    def __init__(self, name: str = DEFAULT_SUMMARY_GENERATORS_ENUM.EXPIRED_TODO_BY_USER, container: Dict[str, List[List[str]]] = None) -> None:
        """Initializer for `ByModuleSummaryGenerator`

        Args:
            name (str, optional): Name of the respective Summary Generator. Defaults to DEFAULT_SUMMARY_GENERATORS_ENUM.EXPIRED_TODO_BY_USER.
            container (Dict[str, List[List[str]], optional): A container in which `generate_summary` would add info of the current todo object. Defaults to {}.
        """
        super().__init__(name=name, container=container or {})

    def generate_summary(self, all_todos_objs: Dict[str, List[TODO]]) -> None:
        """Generates summary for all expired todo items by user

        Args:
            all_todos_objs (Dict[str, List[TODO]]):  Key-value pair where key is relative path of file parsed and value is list of todo objects in that file
            expired_todos_by_user_list (dict): Dictionary with user_name as key and corresponding expired todo items as value
        """
        logger.info(f"Generating summary: {self.name}")

        curr_date = datetime.today()

        for module in all_todos_objs:
            logger.info(f"Generating summary: {self.name} for module: {module}")
            for todo_obj in all_todos_objs[module]:
                user_name = todo_obj.user.user_name

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

        logger.info(f"Summary generated: {self.container}")

    def generate_html(self, user_name: str) -> str:
        """Generates the html representation of the user-wise summary of expired todo items

        Args:
            user_name (str): User name for whom html representation needs to be generated

        Returns:
            str: String showing HTMl representation of the respective summary
        """
        logger.info(f"Generating html for: {self.name}")

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

        logger.info(f"HTML generated: {tables}")
        return tables


class UpcomingWeekTodosByUserSummaryGenerator(BaseSummaryGenerator):
    def __init__(self, name: str = DEFAULT_SUMMARY_GENERATORS_ENUM.UPCOMING_TODO_BY_USER, container: Dict[str, List[List[str]]] = None) -> None:
        """Initializer for `ByModuleSummaryGenerator`

        Args:
            name (str, optional): Name of the respective Summary Generator. Defaults to DEFAULT_SUMMARY_GENERATORS_ENUM.UPCOMING_TODO_BY_USER
            container (Dict[str, List[List[str]]], optional): A container in which `generate_summary` would add info of the current todo object. Defaults to {}
        """
        super().__init__(name=name, container=container or {})

    def generate_summary(self, all_todos_objs: Dict[str, List[TODO]]) -> None:
        """Generates summary for all upcoming todo items by user

        Args:
            all_todos_objs (Dict[str, List[TODO]]):  Key-value pair where key is relative path of file parsed and value is list of todo objects in that file
        """
        logger.info(f"Generating summary: {self.name}")

        curr_date = datetime.today()

        for module in all_todos_objs:
            logger.info(f"Generating summary: {self.name} for module: {module}")
            for todo_obj in all_todos_objs[module]:
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

        logger.info(f"Summary generated: {self.container}")

    def generate_html(self, user_name: str) -> str:
        """Generates the html representation of the user-wise summary of the upcoming (within a week) todo items

        Args:
            user_name (str): User name for whom html representation needs to be generated

        Returns:
            str: String showing HTMl representation of the respective summary
        """
        logger.info(f"Generating html for: {self.name}")

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

        logger.info(f"HTML generated: {tables}")
        return tables
