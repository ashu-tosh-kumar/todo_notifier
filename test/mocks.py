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
        connect_method: CONNECT_METHOD = CONNECT_METHOD.DRY_RUN_FILE,
        generate_html: bool = True,
        save_html_reports: bool = True,
    ) -> None:
        """Initializer for `TestConfig` class

        Args:
            exclude_dirs (Dict[str, List[str]], optional): Dictionary containing details about directories to be ignored
            exclude_files (Dict[str, List[str]], optional): Dictionary containing details about files to be ignored
            summary_generators (List[BaseSummaryGenerator], optional): List of summary generator instance to generate various kind of summary of todo items
            connect_method (CONNECT_METHOD, optional): Method that should be used to pull the repository
            generate_html (bool, optional): Boolean controlling whether to generate HTML report for each summary generator. Defaults to True
            save_html_reports (bool, optional): Boolean controlling whether to store the generated HTML reports by each summary generator. Defaults to True
        """
        super().__init__(exclude_dirs or {}, exclude_files or {}, summary_generators or [], connect_method, generate_html, save_html_reports)


class MockSummaryGenerator:
    """Class to behave like a summary generator"""

    def __init__(self, name: str = None, html: str = None) -> None:
        self._name = name
        self._html = html

    @property
    def html(self) -> str:
        """Mimics `.html` property of the summary generator

        Returns:
            str: returns `self._html`
        """
        return self._html

    @property
    def name(self) -> str:
        """Mimics `.name` property of the summary generator

        Returns:
            str: returns `self._name`
        """
        return self._name
