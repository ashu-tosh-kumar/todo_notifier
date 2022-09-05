# Configuration for custom application of todo_notifier
from copy import deepcopy
from typing import Dict, List

from connect import CONNECT_METHOD
from constants import DEFAULT_EXCLUDE_DIRS, DEFAULT_EXCLUDE_FILES
from summary_generators import (
    BaseSummaryGenerator,
    ByModuleSummaryGenerator,
    ExpiredTodosByUserSummaryGenerator,
    UpcomingWeekTodosByUserSummaryGenerator,
)
from utils import recursive_update


class BaseConfig:
    """Base Config class that can be inherited to spawn any new config class"""

    def __init__(
        self,
        exclude_dirs: Dict[str, List[str]],
        exclude_files: Dict[str, List[str]],
        summary_generators: List[BaseSummaryGenerator],
        connect_method: CONNECT_METHOD,
        generate_html: bool,
        save_html_reports: bool,
    ) -> None:
        """Initializer for `BaseConfig` class

        Args:
            exclude_dirs (Dict[str, List[str]]): Dictionary containing details about directories to be ignored
            exclude_files (Dict[str, List[str]]): Dictionary containing details about files to be ignored
            summary_generators (List[BaseSummaryGenerator]): List of summary generator instance to generate various kind of summary of todo items
            connect_method (CONNECT_METHOD): Method that should be used to pull the repository
            generate_html (bool): Boolean to control whether to generate the html reports
            save_html_reports (bool): Boolean to control whether to save html reports. Works only if `generate_html` is `True`
        """
        self._exclude_dirs = exclude_dirs
        self._exclude_files = exclude_files
        self._summary_generators = summary_generators
        self._connect_method = connect_method
        self._generate_html = generate_html
        self._save_html_reports = save_html_reports

    @property
    def exclude_dirs(self) -> Dict[str, List[str]]:
        """Getter for `exclude_dirs`

        Returns:
            Dict[str, List[str]]: Dictionary containing details about directories to be ignored
        """
        return self._exclude_dirs

    @property
    def exclude_files(self) -> Dict[str, List[str]]:
        """Getter for `exclude_files`

        Returns:
            Dict[str, List[str]]: Dictionary containing details about files to be ignored
        """
        return self._exclude_files

    @property
    def summary_generators(self) -> List[BaseSummaryGenerator]:
        """Getter for `summary_generators`

        Returns:
            List[BaseSummaryGenerator]: List of summary generators to generate various kind of summary of todo items
        """
        return self._summary_generators

    @property
    def connect_method(self) -> CONNECT_METHOD:
        """Getter for `connect_method`

        Returns:
            CONNECT_METHOD: Method that should be used to pull repository
        """
        return self._connect_method

    @property
    def generate_html(self) -> bool:
        """Getter for `generate_html`

        Returns:
            bool: Boolean whether to generate HTML summary for each summary generator
        """
        return self._generate_html

    @property
    def save_html_reports(self) -> bool:
        """Getter for `save_html_reports`

        Returns:
            bool: Boolean whether to save generated HTML summary for each summary generator
        """
        return self._save_html_reports


class DefaultConfig(BaseConfig):
    """Allows easy way to setup config by allowing to pass new dirs/files to exclude along with default ones

    It by default adds `DEFAULT_EXCLUDE_DIRS` and `DEFAULT_EXCLUDE_FILES` to list of dirs and files to be ignored respectively
    """

    def __init__(
        self,
        exclude_dirs: Dict[str, List[str]] = None,
        flag_default_exclude_dirs: bool = True,
        exclude_files: Dict[str, List[str]] = None,
        flag_default_exclude_files: bool = True,
        summary_generators: List[BaseSummaryGenerator] = None,
        flag_default_summary_generators: bool = True,
        connect_method: CONNECT_METHOD = CONNECT_METHOD.HTTPS,
        generate_html: bool = True,
        save_html_reports: bool = False,
    ) -> None:
        """Initializer for `DefaultConfig` class

        Args:
            exclude_dirs (Dict[str, List[str]], optional): Dictionary containing details about directories to be ignored. Defaults to {}
            flag_default_exclude_dirs (bool, optional): Flag to control whether to use `DEFAULT_EXCLUDE_DIRS` to exclude default directories. Defaults to True.
            exclude_files (Dict[str, List[str]], optional): Dictionary containing details about files to be ignored. Defaults to {}
            flag_default_exclude_files (bool, optional): Flag to control whether to use `DEFAULT_EXCLUDE_FILES` to exclude default files. Defaults to True.
            summary_generators (List[BaseSummaryGenerator], optional): List of summary generator instances. Defaults to []
            flag_default_summary_generators (bool, optional): Flag to control whether to use default summary generators viz. `ByModuleSummaryGenerator`,
                                                            `ExpiredTodosByUserSummaryGenerator`, `UpcomingWeekTodosByUserSummaryGenerator`
            connect_method (CONNECT_METHOD, optional):  Method that should be used to pull the repository. Defaults to CONNECT_METHOD.HTTPS
            generate_html (bool, optional): Boolean controlling whether to generate HTML report for each summary generator. Defaults to True
            save_html_reports (bool, optional): Boolean controlling whether to store the generated HTML reports by each summary generator. Defaults to False
        """
        exclude_dirs = exclude_dirs or {}
        exclude_files = exclude_files or {}
        summary_generators = summary_generators or []

        if flag_default_exclude_dirs:
            # Means include the default exclude list of directories
            default_exclude_dirs = deepcopy(DEFAULT_EXCLUDE_DIRS)
            recursive_update(default_exclude_dirs, exclude_dirs)
            exclude_dirs = default_exclude_dirs

        if flag_default_exclude_files:
            # Means include the default exclude list of files
            default_exclude_files = deepcopy(DEFAULT_EXCLUDE_FILES)
            recursive_update(default_exclude_files, exclude_files)
            exclude_files = default_exclude_files

        if flag_default_summary_generators:
            # Means include the default summary generator list of files
            # Instantiate the summary generators
            default_summary_generators = [
                ByModuleSummaryGenerator(),
                ExpiredTodosByUserSummaryGenerator(),
                UpcomingWeekTodosByUserSummaryGenerator(),
            ]

            default_summary_generators.extend(summary_generators)
            summary_generators = default_summary_generators

        super().__init__(exclude_dirs, exclude_files, summary_generators, connect_method, generate_html, save_html_reports)


default_config = DefaultConfig()
