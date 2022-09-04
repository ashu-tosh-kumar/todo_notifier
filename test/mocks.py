from typing import Dict, List

from config import BaseConfig
from connect import CONNECT_METHOD
from summary_generators import BaseSummaryGenerator


class MockTestConfig(BaseConfig):
    """Config for unittest cases"""

    def __init__(
        self,
        exclude_dirs: Dict[str, List[str]] = None,
        exclude_files: Dict[str, List[str]] = None,
        summary_generators: List[BaseSummaryGenerator] = None,
        connect_method: CONNECT_METHOD = CONNECT_METHOD.DRY_RUN,
    ) -> None:
        """Initializer for `TestConfig` class

        Args:
            exclude_dirs (Dict[str, List[str]], optional): Dictionary containing details about directories to be ignored
            exclude_files (Dict[str, List[str]], optional): Dictionary containing details about files to be ignored
            summary_generators (List[BaseSummaryGenerator], optional): List of summary generator instance to generate various kind of summary of todo items
            connect_method (CONNECT_METHOD, optional): Method that should be used to pull the repository
        """
        super().__init__(exclude_dirs or {}, exclude_files or {}, summary_generators or [], connect_method)
