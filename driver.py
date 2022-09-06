import logging
import os
import tempfile
from typing import Dict, TypeVar

from config import BaseConfig, default_config
from connect import Connect
from todo_notifier import parse_files_for_todo_items
from utils import generate_summary, get_files_in_dir, store_html

P = TypeVar("P")

# logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class TODOException(Exception):
    """Exception raised if any issue in `driver` module"""

    pass


def run(connect_kwargs: Dict[str, P], config: BaseConfig = default_config) -> None:
    """Main run method that would get triggered to generate summary and alerts

    This method can be imported and run accordingly on demand or as a scheduled task etc.

    Args:
        connect_kwargs (Dict[str, P]): Dictionary of key-word arguments to be passed to `Connect` to pull the repository
        config (BaseConfig, optional): Configuration to be used. Defaults to `default_config`
    """
    try:
        project_dir_name = connect_kwargs["project_dir_name"]  # Mandatory parameter
    except KeyError:
        logger.exception("project_dir_name needs to be passed in argument: connect_kwargs")
        raise TODOException("project_dir_name needs to be passed in argument: connect_kwargs")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Pull the respective repository into a temporary directory
            logger.info(f"Pulling the repository: {connect_kwargs} into temporary directory: {temp_dir}")
            Connect(config.connect_method).pull_repository(**connect_kwargs, target_dir=temp_dir)

            project_dir = os.path.join(temp_dir, project_dir_name)

            all_files_in_project_dir = get_files_in_dir(
                dir_path=project_dir, extension="py", exclude_subdirs=config.exclude_dirs, exclude_files=config.exclude_files
            )

            all_todos_items = parse_files_for_todo_items(temp_dir, all_files_in_project_dir)

            summary_generators = config.summary_generators

        generate_summary(all_todos_items, summary_generators, config.generate_html)

        if config.generate_html and config.save_html_reports:
            [store_html(summary_generator.html, summary_generator.name) for summary_generator in summary_generators]

    except Exception:
        logger.exception("Error in TODO application")
        raise TODOException("Error in TODO application")
