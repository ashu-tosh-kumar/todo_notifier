"""This module provides a sample driver method to setup and run TODO Notifier"""

import os
import tempfile
from contextlib import nullcontext
from typing import TypeVar

from todonotifier.config import BaseConfig, default_config
from todonotifier.connect import Connect, ConnectMethod
from todonotifier.log import get_logger
from todonotifier.settings import ScanSettings
from todonotifier.todo_notifier import parse_files_for_todo_items
from todonotifier.utils import generate_summary, get_files_in_dir, store_html

P = TypeVar("P")

logger = get_logger(__name__)


class TODOException(Exception):
    """Exception raised if any issue in `driver` module"""

    pass


def _reset_summary_generators(summary_generators: list) -> None:
    """Resets the state kept by summary generators, so that a config reused across runs does not report TODOs twice

    Args:
        summary_generators (list): Summary generators of the config. Objects without a `reset` method (duck-typed generators that do not
            inherit `BaseSummaryGenerator`) are left untouched
    """
    for summary_generator in summary_generators:
        reset = getattr(summary_generator, "reset", None)
        if callable(reset):
            reset()


def run(connect: Connect, config: BaseConfig = default_config) -> None:
    """Main run method that would get triggered to generate summary and alerts

    This method can be imported and run accordingly on demand or as a scheduled task etc.

    With `ConnectMethod.LOCAL` the directory is scanned in place, without copying it into a temporary directory. Report file paths
    then start with the name of that directory, so it should match `project_dir_name`. For the other methods they start with
    `project_dir_name`.

    Args:
        connect (Connect): Object of type `Connect` to allow pulling the repository
        config (BaseConfig, optional): Configuration to be used. Defaults to `default_config`
    """
    try:
        settings = ScanSettings.from_config(config)
        in_place = getattr(connect, "connect_method", None) == ConnectMethod.LOCAL

        # No temporary directory is needed (or created) when scanning in place
        with nullcontext() if in_place else tempfile.TemporaryDirectory() as temp_dir:
            if in_place:
                project_dir = connect.source_path
                parent_dir = os.path.dirname(project_dir)
            else:
                project_dir = os.path.join(temp_dir, connect.project_dir_name)
                parent_dir = temp_dir

            # Pull the respective repository into a temporary directory
            logger.info(f"Pulling the repository into directory: {project_dir} using connect instance: {connect}")
            connect.pull_repository(target_dir=project_dir)

            all_files_in_project_dir = get_files_in_dir(
                dir_path=project_dir, extensions=settings.extensions, exclude_subdirs=settings.exclude_dirs, exclude_files=settings.exclude_files
            )

            all_todos_items = parse_files_for_todo_items(parent_dir, all_files_in_project_dir, settings.ignore_case)

            summary_generators = config.summary_generators

        # Generate summaries
        _reset_summary_generators(summary_generators)
        generate_summary(all_todos_items, summary_generators, config.generate_html)

        # Store generated summaries
        if config.generate_html and config.save_html_reports:
            [store_html(summary_generator.html, summary_generator.name) for summary_generator in summary_generators]

        if config.notifier:
            config.notifier.notify([(summary_generator.name, summary_generator.html) for summary_generator in summary_generators])

    except Exception:
        logger.exception("Error in TODO application")
        raise TODOException("Error in TODO application")
