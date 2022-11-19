from typing import Dict, List, TypeVar, Union

from todonotifier.config import BaseConfig
from todonotifier.notifier import BaseNotifier
from todonotifier.summary_generators import BaseSummaryGenerator

P = TypeVar("P")


class MockTestConfig(BaseConfig):
    """Config for unittest cases"""

    def __init__(
        self,
        exclude_dirs: Dict[str, List[str]] = None,
        exclude_files: Dict[str, List[str]] = None,
        summary_generators: List[BaseSummaryGenerator] = None,
        generate_html: bool = True,
        save_html_reports: bool = True,
        ignore_todo_case: bool = False,
        notifier: Union[BaseNotifier, None] = None,
    ) -> None:
        """Initializer for `TestConfig` class

        Args:
            exclude_dirs (Dict[str, List[str]], optional): Dictionary containing details about directories to be ignored
            exclude_files (Dict[str, List[str]], optional): Dictionary containing details about files to be ignored
            summary_generators (List[BaseSummaryGenerator], optional): List of summary generator instance to generate various kind of summary of todo items
            generate_html (bool, optional): Boolean controlling whether to generate HTML report for each summary generator. Defaults to True
            save_html_reports (bool, optional): Boolean controlling whether to store the generated HTML reports by each summary generator. Defaults to True
            ignore_todo_case (bool, optional): Boolean controlling whether to skip considering the case of todo like whether to consider Todo, todo etc.
        """
        super().__init__(exclude_dirs or {}, exclude_files or {}, summary_generators or [], generate_html, save_html_reports, ignore_todo_case, notifier)


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


class FakeContextManager:
    return_value: P = None

    def __init__(self, *args, **kwargs) -> None:
        """Initializer for `FakeContextManager`

        Args:
            return_value (P): Whatever return value we want to hard code to be returned by the context manager
        """

    def __enter__(self) -> P:
        """Fakes the `__enter__` method of the context manager

        Returns:
            P: returns whatever `return_value` is set in class variable
        """
        return self.return_value

    def __exit__(self, *args, **kargs) -> None:
        """Fakes the `__exit__` method of the context manager"""
        pass
