"""This module provides interface for connecting to the respective repository to allow
cloning the repository to be able to run TODO Notifier.
"""

import os
from enum import Enum
from shutil import copy, copytree, ignore_patterns
from typing import TypeVar, Union

from git.repo import Repo

from todonotifier.constants import DEFAULT_EXCLUDE_DIRS
from todonotifier.log import get_logger

P = TypeVar("P")

logger = get_logger(__name__)


class ConnectException(Exception):
    """Raised if any exception in `connect` module"""

    pass


class ConnectMethod(Enum):
    """Enum values defining the connection method to pull a repository"""

    GIT_CLONE = "GIT_CLONE"
    DRY_RUN_FILE = "DRY_RUN_FILE"
    DRY_RUN_DIR = "DRY_RUN_DIR"
    LOCAL = "LOCAL"


class Connect:
    """Provides a common interface to pull repositories from different sources"""

    def __init__(self, connect_method: ConnectMethod, project_dir_name: str, url: str, branch_name: Union[str, None] = None) -> None:
        """Initializer for `Connect` class

        Args:
            connect_method (ConnectMethod): Method to be used to pull a repository into the target location
            project_dir_name (str): Name of the project. Should match the name of project main directory
            url (str): Url or file address or directory address that needs to be pulled. For `ConnectMethod.LOCAL`, the directory that is scanned in place
            branch_name (optional, Union[str, None]): Branch name is specific branch to be checked out
                                                    after cloning the repository. Useful for `ConnectMethod.GIT_CLONE`. Defaults to None.
        """
        self._connect_method = connect_method
        self._project_dir_name = project_dir_name
        self._file_dir_url = url
        self._branch_name = branch_name

    @property
    def project_dir_name(self) -> str:
        """Getter for project directory name

        Returns:
            str: Returns value of `self._project_dir_name
        """
        return self._project_dir_name

    @property
    def connect_method(self) -> ConnectMethod:
        """Getter for connect method

        Returns:
            ConnectMethod: Returns value of `self._connect_method`
        """
        return self._connect_method

    @property
    def source_path(self) -> str:
        """Absolute path of the source passed as `url`. Meaningful for `ConnectMethod.LOCAL`, where the source is scanned in place

        Returns:
            str: Absolute path of `url`
        """
        return os.path.abspath(self._file_dir_url)

    def __str__(self) -> str:
        """Returns the string representation of the class `Connect`

        Returns:
            str: Returns string representation of the class `Connect`
        """
        return f"{repr(self)} connect_method: {self._connect_method} project_dir_name: {self._project_dir_name} url: {self._file_dir_url}"

    def pull_repository(self, target_dir: str, branch_name: Union[str, None] = None) -> P:
        """Provides a one point access to pull repository into the target location. This method simply relegates
        the call to respective methods set during class initialization

        Args:
            target_dir (str): Directory into which the data from given `url` needs to be copied into. Ignored for `ConnectMethod.LOCAL`
            branch_name (optional, Union[str, None]): Branch name is specific branch to be checked out
                                                    after cloning the repository. Useful for `ConnectMethod.GIT_CLONE`. Defaults to None.

        Returns:
            P: Returns whatever is returned by the respective method to which call is delegated to
        """
        try:
            logger.info(f"Pulling repository: {self._project_dir_name} via {self._connect_method}")
            if self._connect_method == ConnectMethod.GIT_CLONE:
                return self._pull_using_git_clone(target_dir, branch_name=self._branch_name)
            elif self._connect_method == ConnectMethod.DRY_RUN_FILE:
                return self._pull_file_for_dry_run(target_dir)
            elif self._connect_method == ConnectMethod.DRY_RUN_DIR:
                return self._pull_dir_for_dry_run(target_dir)
            elif self._connect_method == ConnectMethod.LOCAL:
                return self._use_local_dir_in_place()
            else:
                raise ConnectException("Unsupported connect method passed")
        except Exception:
            logger.exception(f"Error in pulling repository via {self._connect_method}")
            raise ConnectException(f"Error in pulling repository via {self._connect_method}")

    def _pull_using_git_clone(self, target_dir: str, branch_name: Union[str, None] = None) -> Repo:
        """Pulls the repository using GIT_CLONE method

        NOTE: This method used GitPython library that required Git to be installed on the system

        Args:
            target_dir (str): Directory into which the data from given `url` needs to be copied into
            branch_name (optional, Union[str, None]): Branch name is specific branch to be checked out
                                                    after cloning the repository. Defaults to None.

            Returns:
                Repo: Returns handle to the repository cloned
        """
        return Repo.clone_from(self._file_dir_url, target_dir, branch=branch_name)

    def _pull_file_for_dry_run(self, target_dir: str) -> None:
        """Copies the local file `test_file` into `target_dir` directory

        Args:
            target_dir (str): Directory into which the file from given `url` needs to be copied into
        """
        target_dir = os.path.join(target_dir, self._project_dir_name)
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir)

        copy(self._file_dir_url, target_dir)

    def _pull_dir_for_dry_run(self, target_dir: str) -> None:
        """Copies the local file `test_file` into `target_dir` directory. it automatically ignores the directories in `constants.DEFAULT_EXCLUDE_DIRS`

        Args:
            target_dir (str): Directory into which the folder from given `url` needs to be copied into
        """
        test_dir_base_name = os.path.basename(self._file_dir_url)
        ignore_list = DEFAULT_EXCLUDE_DIRS["PATTERN"] + DEFAULT_EXCLUDE_DIRS["NAME"]
        target_dir = os.path.join(target_dir, test_dir_base_name)
        copytree(self._file_dir_url, target_dir, ignore=ignore_patterns(*ignore_list))

    def _use_local_dir_in_place(self) -> None:
        """Validates that `url` is an existing directory. Nothing is copied: the directory is scanned in place

        Raises:
            ConnectException: Raised if `url` is not an existing directory
        """
        if not os.path.isdir(self._file_dir_url):
            raise ConnectException(f"Not a directory: {self._file_dir_url}")
