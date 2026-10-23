"""This module loads TODO Notifier settings from a project config file and merges them with command line options.

Two file names are supported. `.todonotifier.toml` holds the keys at the top level; `pyproject.toml` holds them under `[tool.todonotifier]`.

Discovery starts at the scan path (its directory, if it is a file) and walks up to the git root (the first directory that contains `.git`, a file
or a directory) or to the filesystem root. In every directory `.todonotifier.toml` is checked before `pyproject.toml` (which counts only if it has
a `[tool.todonotifier]` table). The first match wins. An explicit path to `load_config` skips discovery.

Precedence, highest first: command line overrides, config file, `CLI_DEFAULTS`, then the `ScanSettings` defaults. `CLI_DEFAULTS` are the
batteries-included choices of the command line tool and the config file. The library API (`ScanSettings()`, `DefaultConfig`) keeps its own,
more conservative defaults. An override whose value is `None` counts as "not given".

Accepted keys: every `ScanSettings` option (see `ScanSettings` for the meaning of each), plus `fail_on` and the tables `notify` and `authors`.

    paths, extensions, tags, ignore_case, exclude_dirs, exclude_files, require_comment, use_git_blame, default_due_days, respect_gitignore,
    repo_web_url, commit_sha, fail_on, [notify.<name>], [authors]

Details that are not obvious from the types:

- `paths` in a config file are relative to the directory of that file. Paths given on the command line are left as given.
- `extensions` accepts a string or a list, and the name `"common"` expands to `todonotifier.languages.COMMON_EXTENSIONS`.
- `default_due_days = 0` turns default due dates off (TOML has no null). `ScanSettings.default_due_days` is then `None`. The maximum is 36500 (100 years).
- `exclude_dirs` and `exclude_files` are tables with the optional lists `name`, `pattern` and `abs_path`. They are added to the built-in
  exclusions, they do not replace them.
- `fail_on` is `none`, `expired`, `stale` or `any`. It does not change the scan; the command line uses it to choose the exit code.
- `[authors]` maps git author emails to the handle to show, for example `"a@x.com" = "ashu"`. It fills `ScanSettings.author_aliases`.

Notifier tables live under `[notify.<name>]` (`[tool.todonotifier.notify.<name>]` in `pyproject.toml`). Config files never hold secrets: they name
the environment variables that do, with keys ending in `_env`. This module only stores those names and never reads the variables. `<name>` is
one of the following, and every table also accepts `enabled` (bool, default true):

    slack    webhook_env (required), max_items
    teams    webhook_env (required), max_items
    webhook  url_env (required), headers_env (environment variable holding a JSON object of extra headers)
    email    smtp_host, sender, recipients (list of str) and password_env (all required), smtp_port (int), username_env, starttls (bool)

A key that looks like a literal secret (`webhook`, `url`, `password`, `token`, ...) is rejected with a hint to use the `*_env` key instead.
"""

import difflib
import os
import re
import sys
from copy import deepcopy
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Optional

from todonotifier.languages import expand_extensions
from todonotifier.settings import ScanSettings

if sys.version_info >= (3, 11):  # pragma: no cover - tomllib only exists on Python 3.11+, the dev env runs 3.10 and covers the tomli branch
    import tomllib
else:
    import tomli as tomllib

DOT_FILE_NAME: str = ".todonotifier.toml"
PYPROJECT_FILE_NAME: str = "pyproject.toml"
PYPROJECT_TABLE: str = "tool.todonotifier"

CLI_DEFAULTS: dict[str, Any] = {
    "default_due_days": 90,
    "extensions": "common",
    "tags": ["TODO", "FIXME", "HACK", "XXX"],
    "require_comment": True,
    "respect_gitignore": True,
    "use_git_blame": True,
}
"""Defaults of the command line and the config file. They sit between the config file and the `ScanSettings` defaults"""

# 100 years. More would only overflow `date + timedelta` (year 9999), and "never" is spelled 0
MAX_DEFAULT_DUE_DAYS: int = 36500
FAIL_ON_CHOICES: tuple[str, ...] = ("none", "expired", "stale", "any")
DEFAULT_FAIL_ON: str = "none"

# Notifier schema, shared with the notifier workstream. Each key maps to (kind, required).
_NOTIFIER_SCHEMA: dict[str, dict[str, tuple[str, bool]]] = {
    "slack": {"webhook_env": ("env", True), "max_items": ("positive_int", False)},
    "teams": {"webhook_env": ("env", True), "max_items": ("positive_int", False)},
    "webhook": {"url_env": ("env", True), "headers_env": ("env", False)},
    "email": {
        "smtp_host": ("str", True),
        "smtp_port": ("port", False),
        "sender": ("str", True),
        "recipients": ("str_list", True),
        "username_env": ("env", False),
        "password_env": ("env", True),
        "starttls": ("bool", False),
    },
}
_SECRET_WORDS: tuple[str, ...] = ("webhook", "url", "password", "token", "secret", "key", "headers")
_ENV_NAME_PATTERN: re.Pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_EXCLUDE_KEYS: tuple[str, ...] = ("exclude_dirs", "exclude_files")
_EXCLUDE_SECTIONS: tuple[str, ...] = ("name", "pattern", "abs_path")


class ConfigError(Exception):
    """Raised when the config file or the options passed with it are invalid. The message names the key and the file"""


@dataclass
class ProjectConfig:
    """Everything the config file (merged with the defaults) says

    Attributes:
        settings (ScanSettings): Scan options with the `CLI_DEFAULTS` and the config file applied
        fail_on (str): When the command line should exit non-zero: "none", "expired", "stale" or "any". Defaults to "none"
        notify (dict[str, dict[str, Any]]): Validated notifier tables by name. They hold environment variable names, never secret values
        source (str | None): Path of the config file that was used, or None if there was none
    """

    settings: ScanSettings = field(default_factory=ScanSettings)
    fail_on: str = DEFAULT_FAIL_ON
    notify: dict[str, dict[str, Any]] = field(default_factory=dict)
    source: Optional[str] = None


@dataclass(frozen=True)
class _Origin:
    """Where a value came from, used to word error messages

    Attributes:
        file (str): File name, or a description such as "command line options"
        prefix (str): Dotted TOML table path inside the file, empty for the top level
    """

    file: str
    prefix: str = ""

    @property
    def label(self) -> str:
        """Text such as `pyproject.toml [tool.todonotifier]`"""
        return f"{self.file} [{self.prefix}]" if self.prefix else self.file

    def child(self, name: str) -> "_Origin":
        """Origin of the sub-table `name`"""
        return _Origin(self.file, f"{self.prefix}.{name}" if self.prefix else name)

    def where(self, key: str) -> str:
        """Text such as `'tags' in pyproject.toml [tool.todonotifier]`"""
        return f"'{key}' in {self.label}"


@dataclass
class _Layer:
    """Validated values of one source (defaults, config file or command line)

    Attributes:
        values (dict[str, Any]): `ScanSettings` field names to validated values
        fail_on (str | None): Validated `fail_on`, if given
        notify (dict[str, dict[str, Any]]): Validated notifier tables
    """

    values: dict[str, Any] = field(default_factory=dict)
    fail_on: Optional[str] = None
    notify: dict[str, dict[str, Any]] = field(default_factory=dict)


def _type_name(value: Any) -> str:
    """Name of the type of `value` for messages. The value itself is never shown, because it could be a secret"""
    return type(value).__name__


def _suggest(key: str, allowed: Any) -> str:
    """Builds the " Did you mean 'x'?" suffix for an unknown `key`, or an empty string if nothing is close"""
    matches: list[str] = difflib.get_close_matches(key, list(allowed), n=1)
    return f" Did you mean '{matches[0]}'?" if matches else ""


def _str_list(value: Any, where: str, non_empty: bool = True) -> list[str]:
    """Checks that `value` is a list of non-blank strings"""
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ConfigError(f"Key {where} must be a list of non-empty strings, got {_type_name(value)}.")
    if non_empty and not value:
        raise ConfigError(f"Key {where} must not be an empty list.")
    return list(value)


def _boolean(value: Any, where: str) -> bool:
    """Checks that `value` is a bool"""
    if not isinstance(value, bool):
        raise ConfigError(f"Key {where} must be true or false, got {_type_name(value)}.")
    return value


def _string(value: Any, where: str) -> str:
    """Checks that `value` is a non-blank string"""
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Key {where} must be a non-empty string, got {_type_name(value)}.")
    return value


def _integer(value: Any, where: str, minimum: int, maximum: Optional[int] = None) -> int:
    """Checks that `value` is an int (not a bool) within the bounds"""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"Key {where} must be an integer, got {_type_name(value)}.")
    if value < minimum or (maximum is not None and value > maximum):
        bounds: str = f"at least {minimum}" if maximum is None else f"between {minimum} and {maximum}"
        raise ConfigError(f"Key {where} must be {bounds}, got {value}.")
    return value


def _env_name(value: Any, where: str) -> str:
    """Checks that `value` looks like the name of an environment variable. The value is not echoed, in case a secret was pasted by mistake"""
    if not isinstance(value, str) or not _ENV_NAME_PATTERN.match(value):
        raise ConfigError(
            f"Key {where} must be the NAME of an environment variable (for example 'TODO_SLACK_WEBHOOK'), not its value. "
            f"Got a {_type_name(value)} that is not a valid variable name."
        )
    return value


def _extensions(value: Any, where: str) -> list[str]:
    """Checks `extensions` and expands the "common" preset"""
    if isinstance(value, str) and value.strip():
        return expand_extensions(value)
    if isinstance(value, list):
        return expand_extensions(_str_list(value, where))
    raise ConfigError(f'Key {where} must be a string or a list of strings, got {_type_name(value)}. Use "common" for the common languages.')


def _default_due_days(value: Any, where: str) -> Optional[int]:
    """Checks `default_due_days`. 0 turns default due dates off, which is `None` in `ScanSettings`"""
    days: int = _integer(value, where, minimum=0, maximum=MAX_DEFAULT_DUE_DAYS)
    return days or None


def _exclusions(value: Any, where: str) -> dict[str, list[str]]:
    """Checks an `exclude_dirs` / `exclude_files` table and returns it with the keys upper-cased like `ScanSettings` expects"""
    if not isinstance(value, dict):
        raise ConfigError(f"Key {where} must be a table with the lists {', '.join(_EXCLUDE_SECTIONS)}, got {_type_name(value)}.")
    result: dict[str, list[str]] = {}
    for section, items in value.items():
        lowered: str = section.lower()
        if lowered not in _EXCLUDE_SECTIONS:
            raise ConfigError(
                f"Unknown entry '{section}' in key {where}. Allowed entries: {', '.join(_EXCLUDE_SECTIONS)}.{_suggest(lowered, _EXCLUDE_SECTIONS)}"
            )
        names: list[str] = _str_list(items, f"'{section}' of {where}", non_empty=False)
        if lowered == "pattern":
            for pattern in names:
                try:
                    re.compile(pattern)
                except re.error as error:
                    raise ConfigError(f"Invalid regular expression {pattern!r} in '{section}' of {where}: {error}.") from error
        result.setdefault(lowered.upper(), []).extend(names)
    return result


def _fail_on(value: Any, where: str) -> str:
    """Checks `fail_on`"""
    if value not in FAIL_ON_CHOICES:
        raise ConfigError(f"Key {where} must be one of {', '.join(FAIL_ON_CHOICES)}, got {value!r}.")
    return value


_SETTING_VALIDATORS: dict[str, Callable[[Any, str], Any]] = {
    "paths": _str_list,
    "extensions": _extensions,
    "tags": _str_list,
    "ignore_case": _boolean,
    "exclude_dirs": _exclusions,
    "exclude_files": _exclusions,
    "require_comment": _boolean,
    "use_git_blame": _boolean,
    "default_due_days": _default_due_days,
    "respect_gitignore": _boolean,
    "repo_web_url": _string,
    "commit_sha": _string,
}
SETTING_KEYS: tuple[str, ...] = tuple(_SETTING_VALIDATORS)


def _authors(value: Any, origin: _Origin) -> dict[str, str]:
    """Checks the `authors` table (email to handle). Emails are lower-cased, because they are matched case insensitively"""
    where: str = origin.where("authors")
    if not isinstance(value, dict):
        raise ConfigError(f"Key {where} must be a table of git email = handle, got {_type_name(value)}.")
    aliases: dict[str, str] = {}
    for email, handle in value.items():
        if not isinstance(handle, str) or not handle.strip():
            raise ConfigError(f"Entry '{email}' of {where} must map to a non-empty string handle, got {_type_name(handle)}.")
        if not email.strip():
            raise ConfigError(f"Entries of {where} need a non-empty email as the key.")
        aliases[email.strip().lower()] = handle
    return aliases


def _looks_like_secret(key: str) -> bool:
    """Whether a notifier key name suggests that it holds a literal secret"""
    lowered: str = key.lower()
    return any(word in lowered for word in _SECRET_WORDS)


def _env_replacement(key: str, schema: dict[str, tuple[str, bool]]) -> str:
    """Suggests the allowed `*_env` key that replaces the secret-looking `key`, or a generic hint"""
    lowered: str = key.lower()
    for candidate in schema:
        if candidate.endswith("_env") and candidate[: -len("_env")] in lowered:
            return f"use '{candidate}'"
    return "use a key ending in '_env'"


def _notifier(name: str, table: Any, origin: _Origin) -> dict[str, Any]:
    """Validates one `notify.<name>` table"""
    schema: dict[str, tuple[str, bool]] = _NOTIFIER_SCHEMA[name]
    if not isinstance(table, dict):
        raise ConfigError(f"Key {origin.where(name)} must be a table, got {_type_name(table)}.")
    origin = origin.child(name)

    result: dict[str, Any] = {"enabled": True}
    for key, value in table.items():
        key_where: str = origin.where(key)
        if key == "enabled":
            result[key] = _boolean(value, key_where)
        elif key not in schema:
            if _looks_like_secret(key):
                raise ConfigError(
                    f"Key {key_where} looks like a literal secret. Config files must not hold secrets: put the value in an environment variable "
                    f"and {_env_replacement(key, schema)} to name it."
                )
            raise ConfigError(f"Unknown key {key_where}. Allowed keys: enabled, {', '.join(schema)}.{_suggest(key, [*schema, 'enabled'])}")
        else:
            kind: str = schema[key][0]
            if kind == "env":
                result[key] = _env_name(value, key_where)
            elif kind == "positive_int":
                result[key] = _integer(value, key_where, minimum=1)
            elif kind == "port":
                result[key] = _integer(value, key_where, minimum=1, maximum=65535)
            elif kind == "bool":
                result[key] = _boolean(value, key_where)
            elif kind == "str_list":
                result[key] = _str_list(value, key_where)
            else:
                result[key] = _string(value, key_where)

    for key, (_, required) in schema.items():
        if required and key not in table:
            raise ConfigError(f"Missing required key '{key}' in {origin.label}.")
    return result


def _notify_tables(value: Any, origin: _Origin) -> dict[str, dict[str, Any]]:
    """Validates the whole `notify` table"""
    notify_origin: _Origin = origin.child("notify")
    if not isinstance(value, dict):
        raise ConfigError(f"Key {origin.where('notify')} must be a table of notifiers, got {_type_name(value)}.")
    result: dict[str, dict[str, Any]] = {}
    for name, table in value.items():
        if name not in _NOTIFIER_SCHEMA:
            raise ConfigError(
                f"Unknown notifier '{name}' in {notify_origin.label}. Supported notifiers: {', '.join(_NOTIFIER_SCHEMA)}.{_suggest(name, _NOTIFIER_SCHEMA)}"
            )
        result[name] = _notifier(name, table, notify_origin)
    return result


def _parse_table(table: dict[str, Any], origin: _Origin, base_dir: Optional[str] = None, allow_tables: bool = True) -> _Layer:
    """Validates the keys of one source and returns them as a layer

    Args:
        table (dict[str, Any]): Raw keys from the config file or the command line
        origin (_Origin): Where `table` came from, for messages
        base_dir (str | None): If given, relative `paths` are resolved against it
        allow_tables (bool): Whether `notify` and `authors` are accepted (they are in config files, not in command line overrides)

    Returns:
        _Layer: Validated values
    """
    allowed: list[str] = [*SETTING_KEYS, "fail_on"] + (["notify", "authors"] if allow_tables else [])
    layer: _Layer = _Layer()

    for key, value in table.items():
        if key not in allowed:
            raise ConfigError(f"Unknown key '{key}' in {origin.label}.{_suggest(key, allowed)}")
        where: str = origin.where(key)
        if key == "fail_on":
            layer.fail_on = _fail_on(value, where)
        elif key == "notify":
            layer.notify = _notify_tables(value, origin)
        elif key == "authors":
            layer.values["author_aliases"] = _authors(value, origin)
        else:
            layer.values[key] = _SETTING_VALIDATORS[key](value, where)

    if base_dir is not None and "paths" in layer.values:
        layer.values["paths"] = [path if os.path.isabs(path) else os.path.normpath(os.path.join(base_dir, path)) for path in layer.values["paths"]]
    return layer


def _merge_exclusions(base: dict[str, list[str]], extra: dict[str, list[str]]) -> dict[str, list[str]]:
    """Returns a copy of `base` with the entries of `extra` appended (without duplicates)"""
    merged: dict[str, list[str]] = deepcopy(base)
    for section, items in extra.items():
        target: list[str] = merged.setdefault(section, [])
        target.extend(item for item in items if item not in target)
    return merged


def _apply_layer(settings: ScanSettings, layer: _Layer) -> ScanSettings:
    """Returns `settings` with the values of `layer` on top. Exclusions are added to, everything else is replaced"""
    values: dict[str, Any] = dict(layer.values)
    for key in _EXCLUDE_KEYS:
        if key in values:
            values[key] = _merge_exclusions(getattr(settings, key), values[key])
    return replace(settings, **values)


def _defaults_layer() -> _Layer:
    """The `CLI_DEFAULTS` as a validated layer"""
    return _parse_table(CLI_DEFAULTS, _Origin("built-in defaults"), allow_tables=False)


def _read_toml(path: str) -> dict[str, Any]:
    """Reads and parses a TOML file

    Raises:
        ConfigError: If the file cannot be read or is not valid TOML. The message has the path and the parser message
    """
    try:
        with open(path, "rb") as file:
            return tomllib.load(file)
    except OSError as error:
        raise ConfigError(f"Cannot read config file {path}: {error.strerror or error}") from error
    except ValueError as error:  # TOMLDecodeError (and UnicodeDecodeError) are ValueErrors
        raise ConfigError(f"Invalid TOML in {path}: {error}") from error


def _pyproject_table(data: dict[str, Any], path: str) -> Optional[dict[str, Any]]:
    """Returns the `[tool.todonotifier]` table of parsed pyproject data, or None if it has none"""
    tool: Any = data.get("tool")
    if not isinstance(tool, dict) or "todonotifier" not in tool:
        return None
    table: Any = tool["todonotifier"]
    if not isinstance(table, dict):
        raise ConfigError(f"[{PYPROJECT_TABLE}] in {path} must be a table, got {_type_name(table)}.")
    return table


def has_pyproject_table(path: str) -> bool:
    """Tells whether a `pyproject.toml` has a `[tool.todonotifier]` table (an empty one counts)

    Args:
        path (str): Path of the `pyproject.toml`

    Returns:
        bool: True if the table exists

    Raises:
        ConfigError: If the file cannot be read or is not valid TOML
    """
    return _pyproject_table(_read_toml(path), path) is not None


def _discover(start: str) -> Optional[tuple[str, dict[str, Any]]]:
    """Walks up from `start` and returns the path and raw table of the first config file found"""
    current: str = os.path.abspath(start)
    if not os.path.isdir(current):
        current = os.path.dirname(current)

    while True:
        dot_file: str = os.path.join(current, DOT_FILE_NAME)
        if os.path.isfile(dot_file):
            return dot_file, _read_toml(dot_file)

        pyproject: str = os.path.join(current, PYPROJECT_FILE_NAME)
        if os.path.isfile(pyproject):
            table: Optional[dict[str, Any]] = _pyproject_table(_read_toml(pyproject), pyproject)
            if table is not None:
                return pyproject, table

        parent: str = os.path.dirname(current)
        if os.path.exists(os.path.join(current, ".git")) or parent == current:
            return None
        current = parent


def find_config_file(start: str) -> Optional[str]:
    """Finds the config file that applies to a scan path

    Starts at `start` (its directory, if it is a file) and walks up to the git root or the filesystem root. In each directory
    `.todonotifier.toml` wins over a `pyproject.toml` that has a `[tool.todonotifier]` table. The first match wins.

    Args:
        start (str): Scan path to start from

    Returns:
        str | None: Absolute path of the config file, or None if there is none

    Raises:
        ConfigError: If a candidate file cannot be read or parsed
    """
    found: Optional[tuple[str, dict[str, Any]]] = _discover(start)
    return found[0] if found else None


def load_config(config_path: Optional[str] = None, start: str = ".") -> ProjectConfig:
    """Loads the config file and applies it over the `CLI_DEFAULTS` and the `ScanSettings` defaults

    Args:
        config_path (str | None, optional): Explicit config file, which skips discovery. A file named `pyproject.toml` is read from its
            `[tool.todonotifier]` table, any other file is read with the keys at the top level. Defaults to None
        start (str, optional): Scan path to start discovery from. Defaults to "."

    Returns:
        ProjectConfig: The merged settings. If there is no config file, the defaults and `source=None`

    Raises:
        ConfigError: If `config_path` does not exist, or a file is unreadable, not valid TOML, or has unknown keys or wrong types
    """
    table: Optional[dict[str, Any]]
    source: Optional[str] = None

    if config_path is not None:
        source = os.path.abspath(config_path)
        if not os.path.isfile(source):
            raise ConfigError(f"Config file not found: {config_path}")
        data: dict[str, Any] = _read_toml(source)
        if os.path.basename(source) == PYPROJECT_FILE_NAME:
            table = _pyproject_table(data, source)
            if table is None:
                raise ConfigError(f"{source} has no [{PYPROJECT_TABLE}] table.")
        else:
            table = data
    else:
        found: Optional[tuple[str, dict[str, Any]]] = _discover(start)
        source, table = found if found else (None, None)

    settings: ScanSettings = _apply_layer(ScanSettings(), _defaults_layer())
    if source is None or table is None:
        return ProjectConfig(settings=settings)

    is_pyproject: bool = os.path.basename(source) == PYPROJECT_FILE_NAME
    origin: _Origin = _Origin(os.path.basename(source), PYPROJECT_TABLE if is_pyproject else "")
    layer: _Layer = _parse_table(table, origin, base_dir=os.path.dirname(source))
    return ProjectConfig(settings=_apply_layer(settings, layer), fail_on=layer.fail_on or DEFAULT_FAIL_ON, notify=layer.notify, source=source)


def resolve_project_config(cli_overrides: dict[str, Any], config_path: Optional[str] = None, start: str = ".") -> ProjectConfig:
    """Merges command line overrides over the config file, the `CLI_DEFAULTS` and the `ScanSettings` defaults

    Args:
        cli_overrides (dict[str, Any]): Options given on the command line, by setting name. A value of None means "not given". Besides the
            `ScanSettings` options, `fail_on` is accepted. Relative `paths` stay relative to the current directory
        config_path (str | None, optional): Explicit config file, which skips discovery. Defaults to None
        start (str, optional): Scan path to start discovery from. Defaults to "."

    Returns:
        ProjectConfig: The merged settings, `fail_on`, notifier tables and the config file that was used

    Raises:
        ConfigError: If the config file or an override is invalid, or `config_path` does not exist
    """
    config: ProjectConfig = load_config(config_path, start)
    given: dict[str, Any] = {key: value for key, value in cli_overrides.items() if value is not None}
    layer: _Layer = _parse_table(given, _Origin("command line options"), allow_tables=False)
    return ProjectConfig(
        settings=_apply_layer(config.settings, layer),
        fail_on=layer.fail_on or config.fail_on,
        notify=config.notify,
        source=config.source,
    )


def resolve_settings(cli_overrides: dict[str, Any], config_path: Optional[str] = None, start: str = ".") -> ScanSettings:
    """Merges command line overrides over the config file, the `CLI_DEFAULTS` and the `ScanSettings` defaults

    Precedence, highest first: `cli_overrides`, the config file, `CLI_DEFAULTS`, `ScanSettings` defaults. See `resolve_project_config` for the
    arguments and the errors.

    Returns:
        ScanSettings: The merged settings
    """
    return resolve_project_config(cli_overrides, config_path, start).settings
