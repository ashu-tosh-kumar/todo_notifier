# Configuration for custom application of todo_notifier
from typing import Dict, List

from connect import CONNECT_METHOD
from constants import (
    DEFAULT_EXCLUDE_DIRS,
    DEFAULT_EXCLUDE_FILES,
    DEFAULT_SUMMARY_GENERATORS,
)
from summary_generators import BaseSummaryGenerator
from utils import recursive_update


class BaseConfig:
    """Base Config class that can be inherited to spawn any new config class"""

    def __init__(
        self,
        exclude_dirs: Dict[str, List[str]],
        exclude_files: Dict[str, List[str]],
        summary_generators: List[BaseSummaryGenerator],
        connect_method: CONNECT_METHOD,
    ) -> None:
        """Initializer for `BaseConfig` class

        Args:
            exclude_dirs (Dict[str, List[str]]): Dictionary containing details about directories to be ignored
            exclude_files (Dict[str, List[str]]): Dictionary containing details about files to be ignored
            summary_generators (List[BaseSummaryGenerator]): List of summary generators to generate various kind of summary of todo items
            connect_method (CONNECT_METHOD): Method that should be used to pull the repository
        """
        self._exclude_dirs = exclude_dirs
        self._exclude_files = exclude_files
        self._summary_generators = summary_generators
        self._connect_method = connect_method

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
        summary_generators: List[BaseSummaryGenerator] = [],
        flag_default_summary_generators: bool = True,
        connect_method: CONNECT_METHOD = CONNECT_METHOD.HTTPS,
    ) -> None:
        """Initializer for `DefaultConfig` class

        Args:
            exclude_dirs (Dict[str, List[str]]): Dictionary containing details about directories to be ignored
            flag_default_exclude_dirs ()
            exclude_files (Dict[str, List[str]]): Dictionary containing details about files to be ignored
            summary_generators (List[BaseSummaryGenerator]): List of summary generators objects
        """
        exclude_dirs = exclude_dirs or {}
        exclude_files = exclude_files or {}

        if flag_default_exclude_dirs:
            # Means include the default exclude list of directories
            exclude_dirs = recursive_update(DEFAULT_EXCLUDE_DIRS, exclude_dirs)

        if flag_default_exclude_files:
            # Means include the default exclude list of files
            exclude_files = recursive_update(DEFAULT_EXCLUDE_FILES, exclude_files)

        if flag_default_summary_generators:
            # Means include the default summary generator list of files
            summary_generators = DEFAULT_SUMMARY_GENERATORS.extend(summary_generators)

        super().__init__(exclude_dirs, exclude_files, summary_generators, connect_method)


default_config = DefaultConfig()
