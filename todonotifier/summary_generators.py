"""This module provides the base summary generator that can be inherited to define a new
summary generator. It also provides three default summary generators.
"""

import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, TypeVar

from jinja2 import Environment, FileSystemLoader, select_autoescape

from todonotifier.constants import DEFAULT_SUMMARY_GENERATORS_ENUM, UNKNOWN_USER_NAME
from todonotifier.models import TODO

T = TypeVar("T")

# logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Setup Jinja2 environment
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


class BaseSummaryGenerator(ABC):
    def __init__(self, name: str, container: T, html: str = "") -> None:
        """Initializer for `BaseSummaryGenerator`

        Args:
            name (str): Name of the respective Summary Generator
            container (T): A container in which `generate_summary` would add info of the current todo object, It could be a list or dict or sth else
            html (str, optional): A placeholder for html report contained in `container`. defaults to ""
        """
        self._name = name
        self._container = container
        self._html = html

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

    @property
    def html(self) -> str:
        """Getter for `html`

        Returns:
            str: html of the respective summary generator
        """
        return self._html

    @abstractmethod
    def generate_summary(self, all_todos_objs: Dict[str, List[TODO]]) -> None:
        """Abstract function to generate_summary summary

        Args:
            all_todos_objs (Dict[str, List[TODO]]):  Key-value pair where key is relative path of file parsed and value is list of todo objects in that file
        """
        pass

    @abstractmethod
    def generate_html(self) -> None:
        """Generates the html representation of the respective summary to be sent as notifications to users"""
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
                            todo_obj.msg,
                            todo_obj.position.line_no,
                            str(todo_obj.completion_date),
                        ]
                    ]
                else:
                    self._container[todo_obj.module].append(
                        [
                            user_name,
                            todo_obj.msg,
                            todo_obj.position.line_no,
                            str(todo_obj.completion_date),
                        ]
                    )

        logger.info(f"Summary generated: {self.container}")

    def generate_html(self) -> None:
        """Generates the html representation showing module wise summary of todo items"""
        logger.info(f"Generating html for: {self.name}")

        template = jinja_env.get_template("by_module_summary.html")
        self._html = template.render(container=self._container)

        logger.info(f"HTML generated: {self._html}")


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

        curr_date = datetime.today().date()

        for module in all_todos_objs:
            logger.info(f"Generating summary: {self.name} for module: {module}")
            for todo_obj in all_todos_objs[module]:
                user_name = todo_obj.user.user_name

                if curr_date > todo_obj.completion_date:
                    if user_name not in self._container:
                        self._container[user_name] = [
                            [
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

    def generate_html(self) -> None:
        """Generates the html representation of the user-wise summary of expired todo items for all users"""
        logger.info(f"Generating html for: {self.name}")

        template = jinja_env.get_template("expired_todos_by_user.html")
        self._html = template.render(container=self._container)

        logger.info(f"HTML generated: {self._html}")


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

        curr_date = datetime.today().date()

        for module in all_todos_objs:
            logger.info(f"Generating summary: {self.name} for module: {module}")
            for todo_obj in all_todos_objs[module]:
                user_name = todo_obj.user.user_name if todo_obj.user.user_name else UNKNOWN_USER_NAME

                if curr_date <= todo_obj.completion_date and (todo_obj.completion_date - curr_date).days <= 7:
                    if user_name not in self._container:
                        self._container[user_name] = [
                            [
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

    def generate_html(self) -> None:
        """Generates the html representation of the user-wise summary of the upcoming (within a week) todo items for all users"""
        logger.info(f"Generating html for: {self.name}")

        template = jinja_env.get_template("upcoming_todos_by_user.html")
        self._html = template.render(container=self._container)

        logger.info(f"HTML generated: {self._html}")
