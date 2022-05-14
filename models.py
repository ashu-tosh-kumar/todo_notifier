# Standard format for todo item is as follows. Note that todo has to be in capital letters
# TODO [YYYY-MM-DD] @user_name inline_msg

from datetime import datetime

from exceptions import InvalidDateFormatException


class USER:
    def __init__(self, user_name: str, user_email_id: str = "") -> None:
        self._user_name = user_name
        self._user_email_id = user_email_id

    @property
    def user_name(self):
        return self._user_name

    @property
    def user_email_id(self):
        return self._user_email_id

    def __str__(self):
        return f"{str(self)}:{self._user_name}"


class TODO:
    def __init__(self, msg: str, user: USER, completion_date_str: str) -> None:
        """ Initializer for `todo.upper()` class

        Args:
            msg (str): Inline message in the todo
            user (USER): User in the todo item
            completion_date_str (str): Date by which the respective `todo` item is supposed to be completed

        Raises:
            InvalidDateFormatException: Raised if the `completion_date_str` is not valid or doesn't conform to expected format of "YYYY-MM-DD"
        """
        self._msg = msg
        self._user = user
        try:
            self._completion_date = datetime.strptime(
                completion_date_str, "%Y-%m-%d")
        except ValueError:
            raise InvalidDateFormatException(
                f"Date: {completion_date_str} is invalid/non-supported format. Expected format: 'YYYY-MM-DD'")

    @property
    def msg(self) -> str:
        return self._msg

    @property
    def user(self) -> str:
        return self._user

    @property
    def completion_date(self) -> datetime:
        return self._completion_date

    def __str__(self):
        return f"TODO: {self.msg} ASSIGNED TO: {self.user.user_name} COMPLETE BY {self.completion_date}"
