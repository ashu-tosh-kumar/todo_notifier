# Configuration for custom application of todo_notifier
from typing import List

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
        exclude_dirs: dict,
        exclude_files: dict,
        summary_generators: List[BaseSummaryGenerator],
    ) -> None:
        """Initializer for `BaseConfig` class

        Args:
            exclude_dirs (dict): Dictionary containing details about directories to be ignored
            exclude_files (dict): Dictionary containing details about files to be ignored
            summary_generators (List[BaseSummaryGenerator]): List of summary generators to generate various kind of summary of todo items
        """
        self._exclude_dirs = exclude_dirs
        self._exclude_files = exclude_files
        self._summary_generators = summary_generators

    @property
    def EXCLUDE_DIRS(self) -> dict:
        """Getter for `exclude_dirs`

        Returns:
            dict: Dictionary containing details about directories to be ignored
        """
        return self._exclude_dirs

    @property
    def EXCLUDE_FILES(self) -> dict:
        """Getter for `exclude_files`

        Returns:
            dict: Dictionary containing details about files to be ignored
        """
        return self._exclude_files

    @property
    def SUMMARY_GENERATORS(self) -> List[BaseSummaryGenerator]:
        """Getter for `summary_generators`

        Returns:
            List[BaseSummaryGenerator]: List of summary generators to generate various kind of summary of todo items
        """
        return self._summary_generators


class DefaultConfig:
    """Allows easy way to setup config by allowing to pass new dirs/files to exclude along with default ones

    It by default adds `DEFAULT_EXCLUDE_DIRS` and `DEFAULT_EXCLUDE_FILES` to list of dirs and files to be ignored respectively
    """

    def __init__(
        self,
        exclude_dirs: dict = {},
        exclude_files: dict = {},
        summary_generators: List[BaseSummaryGenerator] = [],
    ) -> None:
        """Initializer for `DefaultConfig` class

        Args:
            exclude_dirs (dict): Dictionary containing details about directories to be ignored
            exclude_files (dict): Dictionary containing details about files to be ignored
            summary_generators (List[BaseSummaryGenerator]): List of summary generators objects
        """
        exclude_dirs = recursive_update(DEFAULT_EXCLUDE_DIRS, exclude_dirs)
        exclude_files = recursive_update(DEFAULT_EXCLUDE_FILES, exclude_files)
        summary_generators = DEFAULT_SUMMARY_GENERATORS.extend(summary_generators)

        super().__init__(
            DEFAULT_EXCLUDE_DIRS, DEFAULT_EXCLUDE_FILES, summary_generators
        )


default_config = DefaultConfig()
