"""Tests of `.pre-commit-hooks.yaml`: the hook ids and entries, and that every flag in an entry is accepted by the command line"""

import os
import shlex
from typing import Any

import pytest
import yaml

from todonotifier.cli import EXIT_FAIL_ON, EXIT_OK, main

HOOKS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".pre-commit-hooks.yaml")


@pytest.fixture(scope="module")
def hooks() -> dict[str, dict[str, Any]]:
    with open(HOOKS_FILE, encoding="utf-8") as file:
        loaded: list[dict[str, Any]] = yaml.safe_load(file)
    return {hook["id"]: hook for hook in loaded}


def entry_arguments(hook: dict[str, Any]) -> list[str]:
    """The arguments of the entry without the program name, as pre-commit would run them (shlex splitting)"""
    words: list[str] = shlex.split(hook["entry"])
    assert words[0] == "todonotifier"
    return words[1:]


@pytest.fixture
def staged(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> Any:
    """The current directory, as pre-commit sets it, with files named by repo-relative path"""
    monkeypatch.chdir(tmp_path)
    for name in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM"):
        monkeypatch.setenv(name, os.devnull)
    return tmp_path


def write(directory: Any, name: str, text: str) -> str:
    (directory / name).write_text(text, encoding="utf-8")
    return name


def test_the_file_has_exactly_the_two_documented_hooks(hooks):
    assert list(hooks) == ["todonotifier", "todonotifier-strict"]


@pytest.mark.parametrize(
    "hook_id, entry",
    [
        ("todonotifier", "todonotifier scan --fail-on expired --no-blame"),
        ("todonotifier-strict", "todonotifier scan --fail-on incomplete --no-blame"),
    ],
)
def test_entries(hooks, hook_id, entry):
    assert hooks[hook_id]["entry"] == entry


@pytest.mark.parametrize("hook_id", ["todonotifier", "todonotifier-strict"])
def test_hook_settings(hooks, hook_id):
    hook = hooks[hook_id]

    assert hook["language"] == "python"
    assert hook["types"] == ["text"]
    assert hook["pass_filenames"] is True
    assert hook["require_serial"] is True
    assert hook["name"].strip() and hook["description"].strip()
    assert "files" not in hook and "always_run" not in hook  # the files come from the consumer's staged files


def test_both_hooks_have_distinct_names(hooks):
    assert len({hook["name"] for hook in hooks.values()}) == len(hooks)


def test_the_default_hook_fails_on_an_overdue_todo_and_ignores_the_rest(hooks, staged):
    arguments = entry_arguments(hooks["todonotifier"])

    old = write(staged, "old.py", "# TODO {2020-01-01} long gone\n")
    undated = write(staged, "undated.py", "# TODO no date and no owner\n")
    future = write(staged, "future.py", "# TODO {2999-01-01} later\n")

    assert main([*arguments, old]) == EXIT_FAIL_ON
    assert main([*arguments, undated, future]) == EXIT_OK


def test_the_strict_hook_fails_on_a_todo_without_owner_or_date(hooks, staged):
    arguments = entry_arguments(hooks["todonotifier-strict"])

    complete = write(staged, "complete.py", "# TODO {2999-01-01} @alice fine\n# TODO(bob) {2999-01-01} also fine\n")
    no_owner = write(staged, "no_owner.py", "# TODO {2999-01-01} no owner\n")
    no_date = write(staged, "no_date.py", "# TODO @alice no date\n")

    assert main([*arguments, complete]) == EXIT_OK
    assert main([*arguments, no_owner]) == EXIT_FAIL_ON
    assert main([*arguments, no_date]) == EXIT_FAIL_ON


@pytest.mark.parametrize("hook_id", ["todonotifier", "todonotifier-strict"])
def test_args_of_the_consumer_come_after_the_entry_and_are_accepted(hooks, staged, hook_id):
    """pre-commit runs `entry + args + files`. A later --fail-on and --blame win, which is what the README promises"""
    arguments = entry_arguments(hooks[hook_id])
    undated = write(staged, "undated.py", "# TODO nothing\n")

    assert main([*arguments, "--fail-on", "none", undated]) == EXIT_OK
    assert main([*arguments, "--blame", "--fail-on", "any", undated]) == EXIT_FAIL_ON  # no repository here: blame degrades quietly


def test_non_code_files_and_no_matching_files_pass(hooks, staged):
    arguments = entry_arguments(hooks["todonotifier"])
    (staged / "data.bin").write_bytes(b"\x00\x01 TODO {2020-01-01}")
    write(staged, "poetry.lock", "# TODO {2020-01-01}\n")

    assert main([*arguments, "data.bin", "poetry.lock"]) == EXIT_OK
