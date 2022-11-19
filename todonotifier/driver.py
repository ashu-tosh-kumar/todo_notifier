import logging
import os
import tempfile
from typing import TypeVar

from todonotifier.config import BaseConfig, default_config
from todonotifier.connect import Connect
from todonotifier.todo_notifier import parse_files_for_todo_items
from todonotifier.utils import generate_summary, get_files_in_dir, store_html

P = TypeVar("P")

# logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class TODOException(Exception):
    """Exception raised if any issue in `driver` module"""

    pass


def run(connect: Connect, config: BaseConfig = default_config) -> None:
    """Main run method that would get triggered to generate summary and alerts

    This method can be imported and run accordingly on demand or as a scheduled task etc.

    Args:
        connect (Connect): Object of type `Connect` to allow pulling the repository
        config (BaseConfig, optional): Configuration to be used. Defaults to `default_config`
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir_name = connect.project_dir_name
            project_dir = os.path.join(temp_dir, project_dir_name)

            # Pull the respective repository into a temporary directory
            logger.info(f"Pulling the repository into temporary directory: {project_dir} using connect instance: {connect}")
            connect.pull_repository(target_dir=project_dir)

            all_files_in_project_dir = get_files_in_dir(
                dir_path=project_dir, extension="py", exclude_subdirs=config.exclude_dirs, exclude_files=config.exclude_files
            )

            ignore_todo_case = config.ignore_todo_case
            all_todos_items = parse_files_for_todo_items(temp_dir, all_files_in_project_dir, ignore_todo_case)

            summary_generators = config.summary_generators

        # Generate summaries
        generate_summary(all_todos_items, summary_generators, config.generate_html)

        # Store generated summaries
        if config.generate_html and config.save_html_reports:
            [store_html(summary_generator.html, summary_generator.name) for summary_generator in summary_generators]

        if config.notifier:
            config.notifier.notify([(summary_generator.name, summary_generator.html) for summary_generator in summary_generators])

    except Exception:
        logger.exception("Error in TODO application")
        raise TODOException("Error in TODO application")
