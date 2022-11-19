# Standard format for todo item is as follows.
# todo has to be in capital letters
# Format: TODO [YYYY-MM-DD] @user_name inline_msg
# Date format must be YYYY-MM-DD
# Only one todo item is allowed per line. If more than one is in one line, the first one is considered as todo item and the rest are considered as message
# No. of spaces between todo, date, user, message is NOT important

from datetime import datetime
from typing import TypeVar

from dateutil import parser

from todonotifier.constants import DEFAULT_COMPLETION_DATE

# from enum import Enum


T = TypeVar("T")


class USER:
    def __init__(self, user_name: str) -> None:
        """Initializer for class `USER`

        Args:
            user_name (str): User name
        """
        self._user_name = user_name

    @property
    def user_name(self) -> str:
        """Getter for `user_name`

        Returns:
            str: Returns username
        """
        return self._user_name

    def __str__(self) -> str:
        """Defines str representation of `USER` class object

        Returns:
            str: Returns string representation of the class object
        """
        return f"User: {repr(self)} user_name: {self.user_name}"


class POSITION:
    def __init__(self, line_no: int) -> None:
        """Initializer for position of a text in file

        Args:
            line_no (int): Shows line_no no. of the text
        """
        self._line_no = line_no

    @property
    def line_no(self) -> int:
        """Getter for `line_no`

        Returns:
            int: Integer representing the line_no no. in respective module
        """
        return self._line_no

    def __str__(self) -> str:
        """Defines str representation of `POSITION` class object

        Returns:
            str: Returns string representation of the class object
        """
        return f"Position: {repr(self)} line_no: {self.line_no}"


class TODO:
    def __init__(
        self,
        msg: str,
        user: USER,
        completion_date_str: str,
        module: str,
        position: POSITION,
    ) -> None:
        """Initializer for `todo.upper()` class

        Args:
            msg (str): Inline message in the todo
            user (USER): User in the todo item
            completion_date_str (str): Date by which the respective `todo` item is supposed to be completed
            module (str): Module in which todo item is present
            position (POSITION): Represents the position of the respective todo

        Raises:
            InvalidDateFormatException: Raised if the `completion_date_str` is not valid or doesn't conform to expected format of "YYYY-MM-DD"
        """
        self._msg = msg
        self._user = user
        try:
            self._completion_date = parser.parse(completion_date_str)
        except Exception:
            self._completion_date = parser.parse(DEFAULT_COMPLETION_DATE)
        self._module = module
        self._position = position

    @property
    def msg(self) -> str:
        """Getter for `msg`

        Returns:
            str: Message of todo item
        """
        return self._msg

    @property
    def user(self) -> USER:
        """Getter for `user`

        Returns:
            USER: user object of the respective todo item
        """
        return self._user

    @property
    def completion_date(self) -> datetime:
        """Getter for `datetime` representation of `completion_date_str`

        Returns:
            datetime: datetime object representing `completion_date_str`
        """
        return self._completion_date

    @property
    def module(self) -> str:
        """Getter for `module`

        Returns:
            str: Module name/address of the respective todo item
        """
        return self._module

    @property
    def position(self) -> POSITION:
        """Getter for `position`

        Returns:
            POSITION: Position of respective todo item in code
        """
        return self._position

    def __str__(self) -> str:
        """str representation of `todo` object

        Returns:
            str: String representation of the respective todo object
        """
        return f"""TODO: {repr(self)} msg: {self.msg} user: {str(self.user)} completion date: {self.completion_date} module: {self.module} position: {str(self.position)}"""  # noqa
