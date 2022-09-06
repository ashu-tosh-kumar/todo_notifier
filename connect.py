"""This module aims to allow connection to the respective repository to allow fetching the repository"""
import logging
import os
from enum import Enum
from shutil import copy, copytree, ignore_patterns
from typing import TypeVar

from constants import DEFAULT_EXCLUDE_DIRS

P = TypeVar("P")

# logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ConnectException(Exception):
    """Raised if any exception in `connect` module"""

    pass


class CONNECT_METHOD(Enum):
    """Enum values defining the connection method to pull a repository"""

    HTTPS = "HTTPS"
    DRY_RUN_FILE = "DRY_RUN_FILE"
    DRY_RUN_DIR = "DRY_RUN_DIR"


class Connect:
    """Provides a common interface to pull repositories from different sources"""

    def __init__(self, connect_method: CONNECT_METHOD):
        """Initializer for `Connect` class

        Args:
            connect_method (CONNECT_METHOD): Method to be used to pull a repository into the target location
        """
        self._connect_method = connect_method

    def pull_repository(self, *args, **kwargs) -> P:
        """Provides a one point access to pull repository into the target location. This method simply relegates
        the call to respective methods set during class initialization

        Returns:
            P: Returns whatever is returned by the respective method to which call is delegated to
        """
        try:
            logger.info(f"Pulling repository: {args} {kwargs} via {self._connect_method}")
            if self._connect_method == CONNECT_METHOD.HTTPS:
                return self._pull_using_https(*args, **kwargs)
            elif self._connect_method == CONNECT_METHOD.DRY_RUN_FILE:
                return self._pull_file_for_dry_run(*args, **kwargs)
            elif self._connect_method == CONNECT_METHOD.DRY_RUN_DIR:
                return self._pull_dir_for_dry_run(*args, **kwargs)
            else:
                raise ConnectException("Unsupported connect method passed")
        except Exception:
            logger.exception(f"Error in pulling repository via {self._connect_method}")
            raise ConnectException(f"Error in pulling repository via {self._connect_method}")

    def _pull_using_https(self, url: str, target_dir: str) -> None:
        # TODO
        pass

    def _pull_file_for_dry_run(self, test_file: str, project_dir_name: str, target_dir: str) -> None:
        """Copies the local file `test_file` into `target_dir` directory

        Args:
            test_file (str): Fully qualified file name to be copied
            project_dir_name (str): Project directory name. Since, we only copy a file, this directory will be created
            target_dir (str): Target directory where file needs to be copied to
        """
        target_dir = os.path.join(target_dir, project_dir_name)
        if not os.path.isdir(target_dir):
            os.mkdir(target_dir)

        copy(test_file, target_dir)

    def _pull_dir_for_dry_run(self, test_dir: str, project_dir_name: str, target_dir: str) -> None:
        """Copies the local file `test_file` into `target_dir` directory. it automatically ignores the directories in `constants.DEFAULT_EXCLUDE_DIRS`

        Args:
            test_file (str): Fully qualified directory name to be copied
            project_dir_name (str): Project directory name. Not required but taking to confirm to design of `_pull_file_for_dry_run`
            target_dir (str): Target directory where file needs to be copied to
        """
        test_dir_base_name = os.path.basename(test_dir)
        ignore_list = DEFAULT_EXCLUDE_DIRS["PATTERN"] + DEFAULT_EXCLUDE_DIRS["NAME"]
        target_dir = os.path.join(target_dir, test_dir_base_name)
        copytree(test_dir, target_dir, ignore=ignore_patterns(*ignore_list))
