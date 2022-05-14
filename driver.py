import os

from notifications import send_notifications
from todo_notifier import parse_files_for_todo_items
from utils import get_files_in_dir


def run(parent_dir_name: str, exclude_subdirs: list = [], exclude_files: list = []):
    """ Main run method that would get triggered to generate summary and alerts

    Args:
        parent_dir_name (str): Parent directory of the project
        exclude_subdirs (list, optional): Sub directoris of `parent_dir_name` that shouldn't be considered
        exclude_files (list, optional): Files in directory `parent_dir_name` or its sub-directories that shouldn't be considered
    """
    curr_dir = os.getcwd()
    parent_dir = os.path.join(parent_dir_name, curr_dir)

    all_files_in_parent_dir = get_files_in_dir(
        parent_dir, "py", exclude_subdirs, exclude_files)

    todo_items = parse_files_for_todo_items(all_files_in_parent_dir)

    send_notifications(todo_items)
