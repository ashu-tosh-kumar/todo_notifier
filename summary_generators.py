from abc import ABC, abstractmethod
from datetime import datetime
from typing import TypeVar

from constants import UNKNOWN_USER_NAME
from models import TODO

T = TypeVar("T")


class BaseSummaryGenerator(ABC):
    def __init__(self, name: str, container: T) -> None:
        """ Initializer for `BaseSummaryGenerator`

        Args:
            name (str): Name of the respective Summary Generator
            container (T): A container in which `generate` would add info of the current todo object, It could be a list or dict or sth else
        """
        self._name = name
        self._container = container

    @abstractmethod
    def generate(self, todo_obj: TODO) -> None:
        """ Abstract function to generate summary

        Args:
            todo_obj (TODO): todo object
        """
        pass

    @abstractmethod
    def generate_html(self) -> str:
        pass


class SummaryByModule(BaseSummaryGenerator):
    def generate(self, todo_obj: TODO) -> None:
        """ Generates summary for each module

        Args:
            todo_obj (TODO): todo object
        """
        self._container: dict

        user_name = todo_obj.user.user_name if todo_obj.user.user_name else UNKNOWN_USER_NAME

        if todo_obj.module not in self._container:
            self._container[todo_obj.module] = [[user_name, todo_obj.user.user_email_id,
                                                 todo_obj.msg, todo_obj.position.line_no, str(todo_obj.completion_date)]]
        else:
            self._container[todo_obj.module].append(
                [user_name, todo_obj.user.user_email_id, todo_obj.msg, todo_obj.position.line_no, str(todo_obj.completion_date)])

    def generate_html(self) -> str:
        pass


class ExpiredTodosByUser(BaseSummaryGenerator):
    def generate(self, todo_obj: TODO) -> None:
        """ Generates summary for all expired todo items by user

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
                    [todo_obj.user.user_email_id, todo_obj.msg, todo_obj.module, todo_obj.position.line_no, str(todo_obj.completion_date)]]
            else:
                self._container[user_name].append(
                    [todo_obj.msg, todo_obj.module, todo_obj.position.line_no, str(todo_obj.completion_date)])

    def generate_html(self) -> str:
        pass


class UpcomingWeekTodosByUser(BaseSummaryGenerator):
    def generate(self, todo_obj: TODO) -> None:
        """ Generates summary for all upcoming todo items by user

        Args:
            todo_obj (TODO): todo object
        """
        self._container: list

        curr_date = datetime.today().date()
        user_name = todo_obj.user.user_name if todo_obj.user.user_name else UNKNOWN_USER_NAME

        if curr_date < todo_obj.completion_date and (todo_obj.completion_date - curr_date).days <= 7:
            if user_name not in self._container:
                self._container[user_name] = [
                    [todo_obj.user.user_email_id, todo_obj.msg, todo_obj.module, todo_obj.position.line_no, str(todo_obj.completion_date)]]
            else:
                self._container[user_name].append(
                    [todo_obj.msg, todo_obj.module, todo_obj.position.line_no, str(todo_obj.completion_date)])

    def generate_html(self) -> str:
        pass
