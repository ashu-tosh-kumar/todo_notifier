"""This module defines `ScanSettings`, the single source of truth for every option that controls a scan.

The scanner (`todonotifier.scanner.scan`), the config file and the command line interface all build a `ScanSettings`
object. `ScanSettings.from_config` expresses an existing `BaseConfig` in these terms, so the same scan options can be
reached from both the old and the new API.
"""

from copy import deepcopy
from dataclasses import dataclass, field

from todonotifier.config import BaseConfig
from todonotifier.constants import DEFAULT_EXCLUDE_DIRS, DEFAULT_EXCLUDE_FILES


def _default_exclude_dirs() -> dict[str, list[str]]:
    """Provides a fresh copy of the library default directory exclusions

    Returns:
        dict[str, list[str]]: Deep copy of `constants.DEFAULT_EXCLUDE_DIRS`
    """
    return deepcopy(DEFAULT_EXCLUDE_DIRS)


def _default_exclude_files() -> dict[str, list[str]]:
    """Provides a fresh copy of the library default file exclusions

    Returns:
        dict[str, list[str]]: Deep copy of `constants.DEFAULT_EXCLUDE_FILES`
    """
    return deepcopy(DEFAULT_EXCLUDE_FILES)


@dataclass
class ScanSettings:
    """All options that control a scan. Defaults keep the behavior of `DefaultConfig`

    Attributes:
        paths (list[str]): Directories and/or individual files to scan. Defaults to ["."]
        extensions (list[str]): File extensions to scan, without the leading dot (a leading dot is stripped). Defaults to ["py"]
        tags (list[str]): Tags to look for. Defaults to ["TODO"]. Tags are matched on word boundaries, longest first
        ignore_case (bool): Whether to match tags case insensitively. Defaults to False
        exclude_dirs (dict[str, list[str]]): Directories to skip, with the same shape as `BaseConfig.exclude_dirs`. Defaults to `DEFAULT_EXCLUDE_DIRS`
        exclude_files (dict[str, list[str]]): Files to skip, with the same shape as `BaseConfig.exclude_files`. Defaults to `DEFAULT_EXCLUDE_FILES`
        require_comment (bool): Whether a tag must be inside a comment to count. Defaults to False. Which files have which comment
            syntax is defined in `todonotifier.languages`; files of unknown types are matched anywhere
        use_git_blame (bool): Whether to fill missing authors and dates from git blame. Defaults to False
        default_due_days (int | None): Days after the creation date (from git blame, so it needs `use_git_blame`) at which an undated TODO
            becomes stale. None or 0 disables default due dates. Defaults to None
        respect_gitignore (bool): Whether to skip files ignored by git (`.gitignore`), inside a git repository. Defaults to False
        repo_web_url (str | None): Web URL of the repository (e.g. https://github.com/org/repo), used with `commit_sha` to build deep links.
            Defaults to None, in which case it is detected from the environment or the `origin` remote when `use_git_blame` is on
        commit_sha (str | None): Commit the scanned tree corresponds to, used with `repo_web_url` to build deep links.
            Defaults to None, in which case it is detected (`GITHUB_SHA` or `HEAD`) when `use_git_blame` is on
        author_aliases (dict[str, str]): Maps git author emails (lower case) to the handle to show instead, filled from `[tool.todonotifier.authors]`
            in the config file. Defaults to an empty dict
    """

    paths: list[str] = field(default_factory=lambda: ["."])
    extensions: list[str] = field(default_factory=lambda: ["py"])
    tags: list[str] = field(default_factory=lambda: ["TODO"])
    ignore_case: bool = False
    exclude_dirs: dict[str, list[str]] = field(default_factory=_default_exclude_dirs)
    exclude_files: dict[str, list[str]] = field(default_factory=_default_exclude_files)
    require_comment: bool = False
    use_git_blame: bool = False
    default_due_days: int | None = None
    respect_gitignore: bool = False
    repo_web_url: str | None = None
    commit_sha: str | None = None
    author_aliases: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalizes `extensions` by stripping leading dots, so both "py" and ".py" are accepted"""
        self.extensions = [extension.lstrip(".") for extension in self.extensions]

    @classmethod
    def from_config(cls, config: BaseConfig) -> "ScanSettings":
        """Builds the settings equivalent to an existing `BaseConfig`

        Only the options that exist on `BaseConfig` are taken from it. Everything else keeps its default.

        Args:
            config (BaseConfig): Configuration to convert

        Returns:
            ScanSettings: Settings with the extensions, case sensitivity and exclusions of `config`. The lists and dicts are copies
        """
        return cls(
            extensions=list(config.file_extensions),
            ignore_case=config.ignore_todo_case,
            exclude_dirs=deepcopy(config.exclude_dirs),
            exclude_files=deepcopy(config.exclude_files),
        )
