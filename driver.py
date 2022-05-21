import os
from typing import List

from config import BaseConfig, default_config
from models import SUMMARY_GENERATOR
from notifications import send_notifications
from summary_generators import default_summary_generators
from todo_notifier import parse_files_for_todo_items
from utils import generate_summary, get_files_in_dir


def run(parent_dir_name: str, summary_generators: List[SUMMARY_GENERATOR] = None, skip_default_summary_generators: bool = False, config: BaseConfig = default_config) -> None:
    """ Main run method that would get triggered to generate summary and alerts

    Args:
        parent_dir_name (str): Parent directory of the project
        config (BaseConfig, optional): Configuration to be used. Defaults to `default_config`
    """
    curr_dir = os.getcwd()
    parent_dir = os.path.join(parent_dir_name, curr_dir)

    all_files_in_parent_dir = get_files_in_dir(
        parent_dir, "py", config.EXCLUDE_DIRS, config.EXCLUDE_FILES)

    all_todos_objs = parse_files_for_todo_items(
        parent_dir_name, all_files_in_parent_dir)

    summary_generators = summary_generators or []
    if not skip_default_summary_generators:
        summary_generators.extend(default_summary_generators)
    generate_summary(all_todos_objs, summary_generators)

    # send_notifications(all_todos_objs)
