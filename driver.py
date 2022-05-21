import os

from config import BaseConfig, default_config
from notifications import send_notifications
from todo_notifier import parse_files_for_todo_items
from utils import get_files_in_dir


def run(parent_dir_name: str, config: BaseConfig = default_config) -> None:
    """ Main run method that would get triggered to generate summary and alerts

    Args:
        parent_dir_name (str): Parent directory of the project
        config (BaseConfig, optional): Configuration to be used. Defaults to `default_config`
    """
    curr_dir = os.getcwd()
    parent_dir = os.path.join(parent_dir_name, curr_dir)

    all_files_in_parent_dir = get_files_in_dir(
        parent_dir, "py", config.EXCLUDE_DIRS, config.EXCLUDE_FILES)

    todo_items = parse_files_for_todo_items(
        parent_dir_name, all_files_in_parent_dir)

    send_notifications(todo_items)
