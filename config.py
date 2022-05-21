# Configuration for custom application of todo_notifier
from constants import DEFAULT_EXCLUDE_DIRS, DEFAULT_EXCLUDE_FILES
from utils import recursive_update


class BaseConfig:
    """ Base Config class that can be inherited to spawn any new config class
    """

    def __init__(self, exclude_dirs: dict, exclude_files: dict) -> None:
        """ Initializer for `BaseConfig` class

        Args:
            exclude_dirs (dict): Dictionary containing details about directories to be ignored
            exclude_files (dict): Dictionary containing details about files to be ignored
        """
        self._exclude_dirs = exclude_dirs
        self._exclude_files = exclude_files

    @property
    def EXCLUDE_DIRS(self) -> dict:
        """ Getter for `exclude_dirs`

        Returns:
            dict: Dictionary containing details about directories to be ignored
        """
        return self._exclude_dirs

    @property
    def EXCLUDE_FILES(self) -> dict:
        """ Getter for `exclude_files`

        Returns:
            dict: Dictionary containing details about files to be ignored
        """
        return self._exclude_files


class DefaultConfig:
    """ Allows easy way to setup config by allowing to pass new dirs/files to exclude along with default ones

    It by default adds `DEFAULT_EXCLUDE_DIRS` and `DEFAULT_EXCLUDE_FILES` to list of dirs and files to be ignored respectively
    """

    def __init__(self, exclude_dirs: dict = {}, exclude_files: dict = {}) -> None:
        """ Initializer for `DefaultConfig` class

        Args:
            exclude_dirs (dict): Dictionary containing details about directories to be ignored
            exclude_files (dict): Dictionary containing details about files to be ignored
        """
        exclude_dirs = recursive_update(DEFAULT_EXCLUDE_DIRS, exclude_dirs)
        exclude_files = recursive_update(DEFAULT_EXCLUDE_FILES, exclude_files)

        super().__init__(DEFAULT_EXCLUDE_DIRS, DEFAULT_EXCLUDE_FILES)


default_config = DefaultConfig()
