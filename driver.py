import os

from config import BaseConfig, default_config
from notifications import send_notifications
from todo_notifier import parse_files_for_todo_items
from utils import generate_summary, get_files_in_dir


def run(parent_dir_name: str, config: BaseConfig = default_config) -> None:
    """Main run method that would get triggered to generate summary and alerts

    This method can be imported and run accordingly on demand or as a scheduled task etc. 

    Args:
        parent_dir_name (str): Parent directory of the project
        config (BaseConfig, optional): Configuration to be used. Defaults to `default_config`
    """
    curr_dir = os.getcwd()
    parent_dir = os.path.join(parent_dir_name, curr_dir)

    all_files_in_parent_dir = get_files_in_dir(
        parent_dir, "py", config.EXCLUDE_DIRS, config.EXCLUDE_FILES
    )

    all_todos_items = parse_files_for_todo_items(
        parent_dir_name, all_files_in_parent_dir
    )

    generate_summary(all_todos_items, config.SUMMARY_GENERATORS)

    send_notifications(config.SUMMARY_GENERATORS)


if __name__ == "__main__":
    pass