"""This module aims to allow connection to the respective repository to allow fetching the repository"""
from enum import Enum


class CONNECT_METHOD(Enum):
    """Enum values defining the connection method to pull a repository"""

    HTTPS = "HTTPS"


class Connect:
    def __init__(self, connect_method: CONNECT_METHOD):
        self._connect_method = connect_method

    def pull_repository(self, *args, **kwargs):
        if self._connect_method == CONNECT_METHOD.HTTPS:
            return self._pull_using_https(*args, **kwargs)

    def _pull_using_https(self, url: str, target_dir: str) -> None:
        # TODO
        pass
