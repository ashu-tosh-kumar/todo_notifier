import os
import tempfile

from config import BaseConfig, default_config
from connect import Connect
from todo_notifier import parse_files_for_todo_items
from utils import generate_summary, get_files_in_dir


def run(git_url: str, project_dir_name: str, config: BaseConfig = default_config) -> None:
    """Main run method that would get triggered to generate summary and alerts

    This method can be imported and run accordingly on demand or as a scheduled task etc.

    Args:
        git_url (str): Git url of the project
        project_dir_name (str): Name of the project on Git
        config (BaseConfig, optional): Configuration to be used. Defaults to `default_config`
    """
    with tempfile.gettempdir() as temp_dir:
        # Pull the respective repository into a temporary directory
        Connect(config.connect_method).pull_repository(git_url=git_url, target_directory=temp_dir)

        project_dir = os.path.join(temp_dir, project_dir_name)

        all_files_in_project_dir = get_files_in_dir(
            dir_path=project_dir, extension="py", exclude_subdirs=config.exclude_dirs, exclude_files=config.exclude_files
        )

        all_todos_items = parse_files_for_todo_items(project_dir_name, all_files_in_project_dir)

        generate_summary(all_todos_items, config.summary_generators)
