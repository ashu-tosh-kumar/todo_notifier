"""This module aims to allow connection to the respective repository to allow fetching the repository"""
import os
from enum import Enum
from shutil import copy
from typing import TypeVar

P = TypeVar("P")


class CONNECT_METHOD(Enum):
    """Enum values defining the connection method to pull a repository"""

    HTTPS = "HTTPS"
    DRY_RUN = "DRY_RUN"


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
        if self._connect_method == CONNECT_METHOD.HTTPS:
            return self._pull_using_https(*args, **kwargs)
        elif self._connect_method == CONNECT_METHOD.DRY_RUN:
            return self._pull_for_dry_run(*args, **kwargs)

    def _pull_using_https(self, url: str, target_dir: str) -> None:
        # TODO
        pass

    def _pull_for_dry_run(self, test_file: str, project_dir_name: str, target_dir: str) -> None:
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
