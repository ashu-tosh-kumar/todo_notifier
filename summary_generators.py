from datetime import datetime

from constants import UNKNOWN_USER_NAME
from models import SUMMARY_GENERATOR, TODO


def summary_by_user(todo_obj: TODO, summary_by_user_dict: dict) -> None:
    """ Generates summary for each user

    Args:
        todo_obj (TODO): todo object
        summary_by_user_dict (dict): Dictionary with user as key and corresponding todo items as value
    """
    user_name = todo_obj.user.user_name if todo_obj.user.user_name else UNKNOWN_USER_NAME

    if user_name not in summary_by_user_dict:
        summary_by_user_dict[user_name] = [
            [todo_obj.user.user_email_id, todo_obj.msg, todo_obj.module, todo_obj.position.line_no, str(todo_obj.completion_date)]]
    else:
        summary_by_user_dict[user_name].append(
            [todo_obj.msg, todo_obj.module, todo_obj.position.line_no, str(todo_obj.completion_date)])


def summary_by_module(todo_obj: TODO, summary_by_module_dict: dict) -> None:
    """ Generates summary for each module

    Args:
        todo_obj (TODO): todo object
        summary_by_module_dict (dict): Dictionary with module as key and corresponding todo items as value
    """
    user_name = todo_obj.user.user_name if todo_obj.user.user_name else UNKNOWN_USER_NAME

    if todo_obj.module not in summary_by_module_dict:
        summary_by_module_dict[todo_obj.module] = [[user_name, todo_obj.user.user_email_id,
                                                    todo_obj.msg, todo_obj.position.line_no, str(todo_obj.completion_date)]]
    else:
        summary_by_module_dict[todo_obj.module].append(
            [user_name, todo_obj.user.user_email_id, todo_obj.msg, todo_obj.position.line_no, str(todo_obj.completion_date)])


def expired_todos(todo_obj: TODO, expired_todos_list: list) -> None:
    """ Generates summary for all expired todo items

    Args:
        todo_obj (TODO): todo object
        expired_todos_list (list): List with all expired todo items
    """
    curr_date = datetime.today().date()
    user_name = todo_obj.user.user_name if todo_obj.user.user_name else UNKNOWN_USER_NAME

    if curr_date > todo_obj.completion_date:
        expired_todos_list.append([user_name, todo_obj.user.user_email_id, todo_obj.msg,
                                   todo_obj.module, todo_obj.position.line_no, str(todo_obj.completion_date)])


def upcoming_week_todos(todo_obj: TODO, upcoming_week_todos_list: list) -> None:
    """ Generates summary for all upcoming todo items

    Args:
        todo_obj (TODO): todo object
        upcoming_week_todos_list (list): List with all upcoming todo items
    """
    curr_date = datetime.today().date()
    user_name = todo_obj.user.user_name if todo_obj.user.user_name else UNKNOWN_USER_NAME

    if curr_date < todo_obj.completion_date and (todo_obj.completion_date - curr_date).days <= 7:
        upcoming_week_todos_list.append([user_name, todo_obj.user.user_email_id, todo_obj.msg,
                                         todo_obj.module, todo_obj.position.line_no, str(todo_obj.completion_date)])


default_summary_generators = [
    SUMMARY_GENERATOR(summary_by_user, {}),
    SUMMARY_GENERATOR(summary_by_module, {}),
    SUMMARY_GENERATOR(expired_todos, []),
    SUMMARY_GENERATOR(upcoming_week_todos, [])
]
