"""Tests of the command line interface. They call `main([...])` and check the exit code and the output, with temporary directories and git repositories"""

import json
import logging
import os
import re
import runpy
import shutil
import subprocess
import sys
from datetime import date
from typing import Any, Optional
from unittest.mock import patch

import pytest
from jsonschema import Draft202012Validator

from todonotifier import cli
from todonotifier.cli import (
    EXIT_ERROR,
    EXIT_FAIL_ON,
    EXIT_OK,
    EXIT_USAGE,
    CliError,
    _exit_status,
    _use_color,
    _write_stdout,
    get_version,
    main,
    starter_config,
)
from todonotifier.formatters import SCHEMA_PATH
from todonotifier.notifier import (
    BaseNotifier,
    DigestNotifier,
    NotificationError,
)
from todonotifier.results import ScanResult
from todonotifier.settings_file import load_config

GIT_AVAILABLE = shutil.which("git") is not None
needs_git = pytest.mark.skipif(not GIT_AVAILABLE, reason="git is not installed")

OLD = "2020-01-01T12:00:00+0000"
NEWER = "2020-02-01T12:00:00+0000"
SLACK_URL = "https://hooks.slack.com/services/T000/B000/TOPSECRET"
TEAMS_URL = "https://example.webhook.office.com/webhookb2/TOPSECRET"
ANNOTATION = re.compile(r"^::(error|warning|notice) file=[^,:\n]+,line=\d+,title=[^,:\n]+::[^\n]*$")
NOTIFY_CONFIG = """\
[tool.todonotifier.notify.slack]
webhook_env = "TN_SLACK"

[tool.todonotifier.notify.teams]
webhook_env = "TN_TEAMS"
"""


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """No inherited git configuration, CI variables or color settings"""
    for name in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_SHA", "NO_COLOR", "TN_SLACK", "TN_TEAMS", "TERM"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


def git(cwd: str, *args: str, when: str = OLD) -> None:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Alice Anderson",
        "GIT_AUTHOR_EMAIL": "alice@example.com",
        "GIT_COMMITTER_NAME": "Alice Anderson",
        "GIT_COMMITTER_EMAIL": "alice@example.com",
        "GIT_AUTHOR_DATE": when,
        "GIT_COMMITTER_DATE": when,
    }
    subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True)


def write(root: Any, rel_path: str, content: str) -> str:
    path = os.path.join(str(root), *rel_path.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)
    return path


def commit_all(root: Any, when: str = OLD) -> None:
    git(str(root), "add", "-A", when=when)
    git(str(root), "commit", "-q", "-m", "commit", when=when)


def init_repo(root: Any) -> None:
    git(str(root), "init", "-q")
    git(str(root), "config", "commit.gpgsign", "false")


@pytest.fixture
def project(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> Any:
    """An empty directory, which is also the current directory"""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def repo(project: Any) -> Any:
    """A git repository (current directory) with one commit from 2020 that has an overdue, a dated-in-the-future and an undated TODO"""
    init_repo(project)
    write(project, "app.py", "# TODO {2020-01-01} @bob explicit and long gone\n# TODO {2999-01-01} far future\n# TODO undated\nx = 1\n")
    write(project, "README.md", "No todos here.\n")
    commit_all(project)
    return project


def run(capsys: pytest.CaptureFixture, *argv: str) -> tuple:
    code = main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def load_schema_validator() -> Draft202012Validator:
    with open(SCHEMA_PATH, encoding="utf-8") as schema_file:
        return Draft202012Validator(json.load(schema_file), format_checker=Draft202012Validator.FORMAT_CHECKER)


class TestParsing:
    def test_version(self, capsys):
        code, out, _ = run(capsys, "--version")

        assert code == EXIT_OK
        assert out == f"todonotifier {get_version()}\n"

    def test_version_falls_back_to_unknown(self):
        with patch("todonotifier.cli.metadata.version", side_effect=cli.metadata.PackageNotFoundError):
            assert get_version() == "unknown"

    def test_help_documents_the_exit_codes(self, capsys):
        for argv in (["--help"], ["scan", "--help"], ["report", "-h"], ["notify", "-h"], ["init", "-h"]):
            code, out, _ = run(capsys, *argv)

            assert code == EXIT_OK
            assert "exit codes:" in out
            assert "unexpected runtime error" in out

    def test_help_lists_the_flags(self, capsys):
        _, out, _ = run(capsys, "scan", "--help")

        for flag in ("--config", "--tags", "--ext", "--ignore-case", "--no-blame", "--default-due-days", "--no-require-comment", "--no-gitignore"):
            assert flag in out
        for flag in ("--since", "--fail-on", "--format", "--output", "--quiet", "--verbose"):
            assert flag in out

    def test_no_command_prints_the_help_and_is_a_usage_error(self, capsys):
        code, out, err = run(capsys)

        assert code == EXIT_USAGE
        assert out == ""
        assert "COMMAND" in err

    @pytest.mark.parametrize(
        "argv",
        [
            ["frobnicate"],
            ["scan", "--fail-on", "sometimes"],
            ["scan", "--format", "xml"],
            ["scan", "--tags", ","],
            ["scan", "--default-due-days", "many"],
            ["scan", "-q", "-v"],
            ["scan", "--no-such-flag"],
            ["init", "--pyproject", "--standalone"],
        ],
    )
    def test_usage_errors_return_2_and_main_never_exits(self, capsys, argv):
        code, out, err = run(capsys, *argv)

        assert code == EXIT_USAGE
        assert out == ""
        assert "usage:" in err

    def test_exit_status_of_argparse_requests(self):
        assert _exit_status(SystemExit()) == 0
        assert _exit_status(SystemExit(0)) == 0
        assert _exit_status(SystemExit(2)) == 2
        assert _exit_status(SystemExit("message")) == EXIT_USAGE

    def test_python_dash_m_runs_main(self, capsys):
        with patch.object(sys, "argv", ["todonotifier", "--version"]), pytest.raises(SystemExit) as raised:
            runpy.run_module("todonotifier", run_name="__main__")

        assert raised.value.code == 0
        assert capsys.readouterr().out.startswith("todonotifier ")


class TestFlagsToSettings:
    @pytest.fixture
    def captured(self, project, monkeypatch):
        seen: dict = {}

        def fake_scan(settings, today=None):
            seen["settings"] = settings
            seen["today"] = today
            return ScanResult(root=str(project))

        monkeypatch.setattr(cli, "scan", fake_scan)
        return seen

    def test_defaults_are_the_cli_defaults(self, capsys, captured):
        assert main(["scan"]) == EXIT_OK

        settings = captured["settings"]
        assert settings.paths == ["."]
        assert settings.tags == ["TODO", "FIXME", "HACK", "XXX"]
        assert (settings.require_comment, settings.respect_gitignore, settings.use_git_blame, settings.default_due_days) == (True, True, True, 90)
        assert "go" in settings.extensions and "py" in settings.extensions
        assert captured["today"] == date.today()

    def test_every_flag_overrides_its_setting(self, capsys, captured):
        argv = [
            "scan",
            "a.py",
            "src",
            "--tags",
            "bug, fixme",
            "--ext",
            "py,.md",
            "--ignore-case",
            "--no-blame",
            "--default-due-days",
            "30",
            "--no-require-comment",
            "--no-gitignore",
        ]
        assert main(argv) == EXIT_OK

        settings = captured["settings"]
        assert settings.paths == ["a.py", "src"]
        assert settings.tags == ["bug", "fixme"]
        assert settings.extensions == ["py", "md"]
        assert settings.ignore_case is True
        assert settings.use_git_blame is False
        assert settings.default_due_days == 30
        assert settings.require_comment is False
        assert settings.respect_gitignore is False

    def test_default_due_days_zero_disables_the_default_date(self, capsys, captured):
        main(["scan", "--default-due-days", "0"])

        assert captured["settings"].default_due_days is None

    def test_ext_accepts_the_common_preset(self, capsys, captured):
        main(["scan", "--ext", "common,proto"])

        assert "proto" in captured["settings"].extensions and "rs" in captured["settings"].extensions

    def test_negative_default_due_days_is_a_config_error(self, capsys, captured):
        code, _, err = run(capsys, "scan", "--default-due-days", "-1")

        assert code == EXIT_USAGE
        assert "default_due_days" in err and "command line options" in err
        assert "Traceback" not in err

    def test_config_file_is_used_and_flags_beat_it(self, capsys, project, captured):
        write(project, "pyproject.toml", '[tool.todonotifier]\ntags = ["FIXME"]\nextensions = ["py"]\npaths = ["src"]\n')

        main(["scan"])
        from_file = captured["settings"]
        main(["scan", "--tags", "TODO", "other"])
        from_flags = captured["settings"]

        assert (from_file.tags, from_file.extensions, from_file.paths) == (["FIXME"], ["py"], [str(project / "src")])
        assert (from_flags.tags, from_flags.paths) == (["TODO"], ["other"])

    def test_explicit_config_option(self, capsys, project, captured):
        write(project, "custom.toml", 'tags = ["NOTE"]\n')

        main(["scan", "--config", "custom.toml"])

        assert captured["settings"].tags == ["NOTE"]


class TestScan:
    def test_zero_config_scan_of_a_git_repository_prints_a_table(self, capsys, repo):
        code, out, err = run(capsys, "scan", ".")

        assert code == EXIT_OK
        assert err == ""
        lines = out.splitlines()
        assert lines[0].split() == ["LOCATION", "TAG", "OWNER", "DUE", "MESSAGE"]
        assert "app.py:1" in lines[1] and "@bob" not in lines[1] and "bob" in lines[1] and "overdue" in lines[1]
        assert "stale" in lines[3]
        assert lines[-1] == "3 TODOs · 1 overdue · 1 stale · 0 unowned"
        assert "\x1b" not in out

    def test_default_path_is_the_current_directory(self, capsys, repo):
        assert run(capsys, "scan") == run(capsys, "scan", ".")

    def test_scan_outside_a_repository_works_and_says_why_blame_is_off(self, capsys, project):
        write(project, "a.py", "# TODO {2020-01-01} old\n")

        code, out, err = run(capsys, "scan", ".")

        assert code == EXIT_OK
        assert "a.py:1" in out
        assert "not inside a git repository" in err

    def test_quiet_hides_warnings_and_verbose_shows_debug_logs(self, capsys, project):
        write(project, "a.py", "# TODO x\n")

        _, _, quiet_err = run(capsys, "scan", "-q", ".")
        _, _, verbose_err = run(capsys, "scan", "-v", ".")

        assert quiet_err == ""
        assert "INFO" in verbose_err and "Scanning 1 files" in verbose_err

    def test_logging_is_restored_after_main(self, capsys, project):
        logger = logging.getLogger("todonotifier")
        before = (list(logger.handlers), logger.level)

        main(["scan", "-v", "."])

        assert (list(logger.handlers), logger.level) == before

    def test_no_todos_is_a_friendly_message(self, capsys, project):
        write(project, "a.py", "x = 1\n")

        code, out, _ = run(capsys, "scan", ".", "--no-blame")

        assert code == EXIT_OK
        assert out == "No TODOs found (1 file scanned). Nice and tidy!\n"

    def test_only_the_named_files_are_scanned(self, capsys, repo):
        write(repo, "f1.py", "# TODO one\n")
        write(repo, "f2.py", "# TODO two\n")
        write(repo, "f3.py", "# TODO three\n")

        code, out, _ = run(capsys, "scan", "f1.py", "f2.py", "--format", "json", "--no-blame")

        document = json.loads(out)
        assert code == EXIT_OK
        assert document["scanned_files"] == ["f1.py", "f2.py"]
        assert [item["file"] for item in document["items"]] == ["f1.py", "f2.py"]

    def test_a_missing_path_is_a_usage_error_with_a_one_line_message(self, capsys, project):
        code, out, err = run(capsys, "scan", "nowhere")

        assert code == EXIT_USAGE
        assert out == ""
        assert err.startswith("todonotifier: error: Path does not exist: ")
        assert err.count("\n") == 1

    def test_bad_config_files_are_usage_errors(self, capsys, project):
        write(project, ".todonotifier.toml", 'tagz = ["TODO"]\n')
        _, _, unknown_key = run(capsys, "scan")
        write(project, ".todonotifier.toml", "tags = [\n")
        _, _, bad_toml = run(capsys, "scan")
        code, _, missing = run(capsys, "scan", "--config", "nope.toml")

        assert "Unknown key 'tagz'" in unknown_key and "Did you mean 'tags'?" in unknown_key
        assert "Invalid TOML" in bad_toml
        assert code == EXIT_USAGE and "Config file not found: nope.toml" in missing

    def test_unexpected_errors_return_3_and_show_the_traceback_only_with_verbose(self, capsys, project, monkeypatch):
        def boom(settings, today=None):
            raise RuntimeError("boom\nsecond line")

        monkeypatch.setattr(cli, "scan", boom)

        code, out, err = run(capsys, "scan")
        verbose_code, _, verbose_err = run(capsys, "scan", "-v")

        assert (code, verbose_code) == (EXIT_ERROR, EXIT_ERROR)
        assert out == ""
        assert err == "todonotifier: error: unexpected RuntimeError: boom\nRun again with -v for the full traceback.\n"
        assert "Traceback (most recent call last)" in verbose_err and "RuntimeError: boom" in verbose_err

    def test_table_status_uses_the_day_of_the_run(self, capsys, project, monkeypatch):
        monkeypatch.setattr(cli, "_today", lambda: date(2026, 5, 1))
        write(project, "a.py", "# TODO {2026-05-03} @alice soon\n# TODO {2026-04-01} late\n")

        _, out, _ = run(capsys, "scan", ".", "--no-blame")

        assert "2026-05-03 due in 2d" in out
        assert "2026-04-01 overdue 30d" in out
        assert out.splitlines()[-1] == "2 TODOs · 1 overdue · 0 stale · 1 unowned"


class TestFailOn:
    @pytest.fixture
    def only_stale(self, project):
        init_repo(project)
        write(project, "a.py", "# TODO undated and old\n")
        commit_all(project)

    @pytest.mark.parametrize("fail_on, expected", [("none", 0), ("expired", 1), ("stale", 1), ("any", 1)])
    def test_overdue_explicit_date(self, capsys, project, fail_on, expected):
        write(project, "a.py", "# TODO {2020-01-01} long gone\n")

        code, _, err = run(capsys, "scan", ".", "--no-blame", "--fail-on", fail_on)

        assert code == expected
        assert ("--fail-on " + fail_on in err) == bool(expected)

    @needs_git
    @pytest.mark.parametrize("fail_on, expected", [("none", 0), ("expired", 0), ("stale", 1), ("any", 1)])
    def test_only_stale_todos_do_not_fail_expired(self, capsys, only_stale, fail_on, expected):
        code, out, err = run(capsys, "scan", ".", "--fail-on", fail_on)

        assert "stale" in out
        assert code == expected
        if expected:
            assert err == f"todonotifier: --fail-on {fail_on}: " + ("0 overdue and 1 stale TODO\n" if fail_on == "stale" else "1 TODO found\n")

    def test_any_needs_a_todo_and_a_clean_repo_passes_everything(self, capsys, project):
        write(project, "a.py", "x = 1\n")

        for fail_on in ("expired", "stale", "any"):
            assert main(["scan", ".", "--no-blame", "--fail-on", fail_on]) == EXIT_OK

    def test_far_future_dates_do_not_fail(self, capsys, project):
        write(project, "a.py", "# TODO {2999-01-01} much later\n")

        assert main(["scan", ".", "--no-blame", "--fail-on", "stale"]) == EXIT_OK

    def test_default_comes_from_the_config_file_and_the_flag_wins(self, capsys, project):
        write(project, "pyproject.toml", '[tool.todonotifier]\nfail_on = "any"\n')
        write(project, "a.py", "# TODO something\n")

        assert main(["scan", ".", "--no-blame"]) == EXIT_FAIL_ON
        assert main(["scan", ".", "--no-blame", "--fail-on", "none"]) == EXIT_OK

    def test_the_output_is_still_printed_when_the_condition_is_met(self, capsys, project):
        write(project, "a.py", "# TODO {2020-01-01} long gone\n")

        code, out, _ = run(capsys, "scan", ".", "--no-blame", "--fail-on", "expired", "-q")

        assert code == EXIT_FAIL_ON
        assert "a.py:1" in out

    @needs_git
    def test_it_is_evaluated_on_the_result_filtered_by_since(self, capsys, repo):
        write(repo, "new.py", "# TODO {2999-01-01} harmless and new\n")
        commit_all(repo, NEWER)

        old_problem = run(capsys, "scan", ".", "--fail-on", "expired")[0]
        since = run(capsys, "scan", ".", "--fail-on", "expired", "--since", "HEAD~1")[0]

        assert (old_problem, since) == (EXIT_FAIL_ON, EXIT_OK)


class TestFormats:
    def test_json_validates_against_the_schema(self, capsys, repo):
        code, out, _ = run(capsys, "scan", ".", "--format", "json")

        document = json.loads(out)
        assert code == EXIT_OK
        load_schema_validator().validate(document)
        assert document["schema_version"] == 1
        assert [item["due_source"] for item in document["items"]] == ["explicit", "explicit", "default"]
        assert document["items"][0]["author"] == "bob"
        assert document["items"][2]["author"] == "Alice Anderson"

    def test_json_of_an_empty_scan_validates_too(self, capsys, project):
        write(project, "a.py", "x = 1\n")

        _, out, _ = run(capsys, "scan", ".", "--format", "json")

        load_schema_validator().validate(json.loads(out))

    def test_github_annotations_match_the_workflow_command_syntax(self, capsys, repo):
        code, out, _ = run(capsys, "scan", ".", "--format", "github")

        lines = out.splitlines()
        assert code == EXIT_OK
        for line in lines[:-1]:
            assert ANNOTATION.match(line), line
        assert lines[0].startswith("::error file=app.py,line=1,title=TODO overdue by ")
        assert lines[2].startswith("::warning file=app.py,line=3,title=TODO stale by ")
        assert lines[-1] == "3 TODOs: 1 overdue, 1 stale, 0 unowned"

    @needs_git
    def test_github_paths_are_relative_to_the_repository_root_for_a_subdirectory(self, capsys, repo):
        write(repo, "services/api/handler.py", "# TODO {2020-01-01} fix\n")
        commit_all(repo, NEWER)

        _, out, _ = run(capsys, "scan", "services", "--format", "github", "--no-blame")
        _, sarif_out, _ = run(capsys, "scan", "services", "--format", "sarif", "--no-blame")

        assert out.splitlines()[0].startswith("::error file=services/api/handler.py,line=1,")
        uri = json.loads(sarif_out)["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
        assert uri == "services/api/handler.py"

    def test_sarif(self, capsys, repo):
        code, out, _ = run(capsys, "scan", ".", "--format", "sarif")

        sarif = json.loads(out)
        results = sarif["runs"][0]["results"]
        assert code == EXIT_OK and sarif["version"] == "2.1.0"
        assert [result["level"] for result in results] == ["error", "notice" if False else "note", "warning"]
        assert all(result["locations"][0]["physicalLocation"]["artifactLocation"]["uriBaseId"] == "%SRCROOT%" for result in results)

    def test_markdown(self, capsys, repo):
        code, out, _ = run(capsys, "scan", ".", "--format", "markdown")

        assert code == EXIT_OK
        assert out.startswith("## TODO digest ")
        assert "### Overdue (1)" in out and "### Stale (1)" in out

    def test_output_writes_a_file_instead_of_stdout(self, capsys, repo):
        code, out, err = run(capsys, "scan", ".", "--format", "json", "--output", "results/out.json")

        assert code == EXIT_OK and out == ""
        assert err == "Wrote the json output to results/out.json\n"
        with open(repo / "results" / "out.json", encoding="utf-8") as file:
            load_schema_validator().validate(json.load(file))

    def test_quiet_output_prints_nothing(self, capsys, repo):
        assert run(capsys, "scan", ".", "--output", "t.txt", "-q") == (EXIT_OK, "", "")

    def test_an_unwritable_output_is_a_usage_error(self, capsys, repo):
        code, _, err = run(capsys, "scan", ".", "--output", str(repo))

        assert code == EXIT_USAGE
        assert err.startswith("todonotifier: error: Cannot write to ")

    def test_html_writes_the_reports_to_a_directory_and_prints_their_paths(self, capsys, repo):
        code, out, _ = run(capsys, "scan", ".", "--format", "html", "--output", "reports")

        assert code == EXIT_OK
        assert out.splitlines() == [
            os.path.join("reports", f"{name}.html") for name in ("Module-wise Summary", "Expired TODO Items", "Upcoming Week TODO Items")
        ]
        with open(repo / "reports" / "Module-wise Summary.html", encoding="utf-8") as file:
            assert "explicit and long gone" in file.read()

    def test_report_defaults_to_the_report_directory(self, capsys, repo):
        code, out, _ = run(capsys, "report", ".")

        assert code == EXIT_OK
        assert out.splitlines()[0] == os.path.join(".report", "Module-wise Summary.html")
        assert os.path.isfile(repo / ".report" / "Expired TODO Items.html")

    def test_report_out_is_the_directory(self, capsys, repo):
        _, out, _ = run(capsys, "report", "--out", "elsewhere", "--no-blame")

        assert out.splitlines()[0] == os.path.join("elsewhere", "Module-wise Summary.html")

    def test_report_can_use_another_format(self, capsys, repo):
        _, out, _ = run(capsys, "report", "--format", "json", "--no-blame")

        assert json.loads(out)["schema_version"] == 1

    def test_unwritable_report_directory_is_a_usage_error(self, capsys, repo):
        write(repo, "blocker", "a file, not a directory")

        code, _, err = run(capsys, "report", "--out", "blocker/inside")

        assert code == EXIT_USAGE
        assert "Cannot write the reports to blocker/inside" in err

    def test_unicode_that_the_terminal_cannot_show_is_replaced(self, capsys, project, monkeypatch):
        import io

        stream = io.TextIOWrapper(io.BytesIO(), encoding="ascii")
        monkeypatch.setattr(sys, "stdout", stream)

        _write_stdout("1 TODO · 2")
        stream.flush()

        assert stream.buffer.getvalue() == b"1 TODO ? 2\n"


class TestColor:
    def tty(self, monkeypatch):
        """Makes the current stdout look like a terminal. Called in the test body, because the stdout of `capsys` exists only there"""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)

    def test_color_needs_a_terminal_and_no_output_file_and_no_no_color(self, capsys, monkeypatch):
        self.tty(monkeypatch)
        assert _use_color(None) is True
        assert _use_color("file.txt") is False
        monkeypatch.setenv("NO_COLOR", "1")
        assert _use_color(None) is False
        monkeypatch.delenv("NO_COLOR")
        monkeypatch.setenv("TERM", "dumb")
        assert _use_color(None) is False

    def test_an_empty_no_color_does_not_count(self, capsys, monkeypatch):
        self.tty(monkeypatch)
        monkeypatch.setenv("NO_COLOR", "")

        assert _use_color(None) is True

    def test_not_a_terminal(self, capsys):
        assert _use_color(None) is False

    def test_the_table_is_colored_on_a_terminal(self, capsys, project, monkeypatch):
        self.tty(monkeypatch)
        write(project, "a.py", "# TODO {2020-01-01} late\n")

        _, out, _ = run(capsys, "scan", ".", "--no-blame")

        assert "\x1b[31m2020-01-01 overdue" in out

    def test_no_color_and_output_files_stay_plain(self, capsys, project, monkeypatch):
        self.tty(monkeypatch)
        write(project, "a.py", "# TODO {2020-01-01} late\n")

        _, plain_out, _ = run(capsys, "scan", ".", "--no-blame", "--output", "t.txt")
        monkeypatch.setenv("NO_COLOR", "1")
        _, no_color_out, _ = run(capsys, "scan", ".", "--no-blame")

        with open(project / "t.txt", encoding="utf-8") as file:
            assert "\x1b" not in file.read()
        assert "\x1b" not in plain_out + no_color_out


@needs_git
class TestSince:
    @pytest.fixture
    def history(self, repo):
        """HEAD~1 has the TODOs of `repo`; HEAD adds one TODO line to app.py and a new file"""
        write(repo, "app.py", "# TODO {2020-01-01} @bob explicit and long gone\n# TODO {2999-01-01} far future\n# TODO undated\nx = 1\n# TODO added later\n")
        write(repo, "new.py", "x = 1\n# TODO in a new file\n")
        commit_all(repo, NEWER)
        return repo

    def messages(self, out: str) -> list:
        return [item["message"] for item in json.loads(out)["items"]]

    def test_only_todos_on_changed_lines_are_reported(self, capsys, history):
        code, out, _ = run(capsys, "scan", ".", "--since", "HEAD~1", "--format", "json")

        assert code == EXIT_OK
        assert self.messages(out) == ["added later", "in a new file"]

    def test_the_whole_history_without_since(self, capsys, history):
        _, out, _ = run(capsys, "scan", ".", "--format", "json")

        assert len(self.messages(out)) == 5

    def test_uncommitted_and_untracked_changes_count(self, capsys, history):
        write(history, "app.py", "# TODO {2020-01-01} @bob explicit and long gone\n# TODO edited today\n# TODO undated\nx = 1\n# TODO added later\n")
        write(history, "brand_new.py", "# TODO untracked\n")

        _, out, _ = run(capsys, "scan", ".", "--since", "HEAD", "--format", "json")

        assert self.messages(out) == ["edited today", "untracked"]

    def test_a_subdirectory_scan_maps_paths_through_the_repository_root(self, capsys, history):
        write(history, "pkg/mod.py", "# TODO old one\n")
        commit_all(history, NEWER)
        write(history, "pkg/mod.py", "# TODO old one\n# TODO new one\n")

        _, out, _ = run(capsys, "scan", "pkg", "--since", "HEAD", "--format", "json")

        assert self.messages(out) == ["new one"]

    def test_since_composes_with_the_table_and_an_empty_result(self, capsys, history):
        _, out, _ = run(capsys, "scan", ".", "--since", "HEAD")

        assert out.startswith("No TODOs found")

    def test_an_unknown_ref_is_a_usage_error(self, capsys, history):
        code, out, err = run(capsys, "scan", ".", "--since", "no-such-ref")

        assert code == EXIT_USAGE and out == ""
        assert err.startswith("todonotifier: error: --since no-such-ref: Unknown git ref 'no-such-ref'")

    def test_an_option_like_ref_is_rejected(self, capsys, history):
        code, _, err = run(capsys, "scan", ".", "--since=--output=/tmp/pwned")

        assert code == EXIT_USAGE and "Invalid git ref" in err
        assert not os.path.exists("/tmp/pwned")

    def test_outside_a_repository_is_a_usage_error(self, capsys, tmp_path, monkeypatch):
        outside = tmp_path / "plain"
        outside.mkdir()
        write(outside, "a.py", "# TODO x\n")
        monkeypatch.chdir(outside)
        with patch("todonotifier.cli.find_git_root", return_value=None):
            code, _, err = run(capsys, "scan", ".", "--since", "HEAD~1", "--no-blame")

        assert code == EXIT_USAGE
        assert "--since needs a git repository" in err


class RecordingNotifier(DigestNotifier):
    def __init__(self, fail_with: Optional[BaseException] = None) -> None:
        super().__init__()
        self.fail_with = fail_with
        self.calls: list = []

    def notify(self, summary: list) -> None:  # pragma: no cover - the CLI calls notify_result
        raise AssertionError("not used")

    def notify_result(self, result: ScanResult, reports: list) -> None:
        self.calls.append((result, reports, self.new_count))
        if self.fail_with:
            raise self.fail_with


class RecordedPosts(list):
    """The posts a notifier made: `(label, url, payload)`. `failing` maps a label to the exception its post raises"""

    def __init__(self) -> None:
        super().__init__()
        self.failing: dict = {}


class PlainNotifier(BaseNotifier):
    def __init__(self) -> None:
        super().__init__()
        self.new_count_seen: Any = "untouched"
        self.calls = 0

    def notify(self, summary: list) -> None:
        self.calls += 1


class TestNotify:
    @pytest.fixture
    def configured(self, project, monkeypatch):
        write(project, "pyproject.toml", "[tool.todonotifier]\n" + NOTIFY_CONFIG.replace("[tool.todonotifier.notify", "[tool.todonotifier.notify"))
        write(project, "a.py", "# TODO {2020-01-01} @alice late\n# TODO later\n")
        monkeypatch.setenv("TN_SLACK", SLACK_URL)
        monkeypatch.setenv("TN_TEAMS", TEAMS_URL)
        return project

    @pytest.fixture
    def posts(self, monkeypatch):
        """Replaces the network: records the posts and fails the ones named in `failing`"""
        recorded = RecordedPosts()

        def fake_post(url, payload, headers, label, sleep, timeout=10):
            recorded.append((label, url, payload))
            if label in recorded.failing:
                raise recorded.failing[label]

        monkeypatch.setattr("todonotifier.notifier._post_json", fake_post)
        return recorded

    def test_without_notifiers_it_explains_how_to_set_one_up(self, capsys, project):
        write(project, "a.py", "# TODO x\n")

        code, out, err = run(capsys, "notify", ".")

        assert code == EXIT_USAGE and out == ""
        assert "No notifiers are configured (there is no config file)" in err
        assert "todonotifier init" in err and "#notifications" in err

    def test_with_a_config_without_notifiers_it_names_the_file(self, capsys, project):
        write(project, "pyproject.toml", "[tool.todonotifier]\n")

        code, _, err = run(capsys, "notify")

        assert code == EXIT_USAGE
        assert "No notifiers are configured in " in err and "pyproject.toml" in err

    def test_disabled_notifiers_are_reported_as_such(self, capsys, project):
        write(project, ".todonotifier.toml", '[notify.slack]\nwebhook_env = "TN_SLACK"\nenabled = false\n')

        code, _, err = run(capsys, "notify")

        assert code == EXIT_USAGE and "disabled" in err

    def test_a_missing_environment_variable_is_a_usage_error_that_names_the_variable(self, capsys, configured, monkeypatch):
        monkeypatch.delenv("TN_SLACK")

        code, _, err = run(capsys, "notify")

        assert code == EXIT_USAGE
        assert "TN_SLACK" in err and "Traceback" not in err

    def test_it_sends_the_digest_to_every_notifier(self, capsys, configured, posts):
        code, out, err = run(capsys, "notify", ".", "--no-blame")

        assert code == EXIT_OK and out == ""
        assert [(label, url) for label, url, _ in posts] == [("Slack webhook", SLACK_URL), ("Teams webhook", TEAMS_URL)]
        assert "1 overdue" in json.dumps(posts[0][2])
        assert err == "Notified SlackWebhookNotifier\nNotified TeamsWebhookNotifier\n"

    def test_quiet_hides_the_success_lines(self, capsys, configured, posts):
        assert run(capsys, "notify", ".", "--no-blame", "-q") == (EXIT_OK, "", "")

    def test_all_notifiers_are_tried_and_a_failure_returns_3_without_leaking_secrets(self, capsys, configured, posts):
        posts.failing["Slack webhook"] = NotificationError("Slack webhook POST failed with HTTP 500 (attempt 3/3)")

        code, _, err = run(capsys, "notify", ".", "--no-blame")

        assert code == EXIT_ERROR
        assert [label for label, _, _ in posts] == ["Slack webhook", "Teams webhook"]
        assert err.splitlines() == [
            "todonotifier: SlackWebhookNotifier failed: Slack webhook POST failed with HTTP 500 (attempt 3/3)",
            "Notified TeamsWebhookNotifier",
        ]
        assert "TOPSECRET" not in err

    def test_an_unexpected_notifier_error_shows_only_the_type_unless_verbose(self, capsys, configured, posts):
        posts.failing["Slack webhook"] = OSError("password=hunter2 in message")

        code, _, err = run(capsys, "notify", ".", "--no-blame")
        _, _, verbose_err = run(capsys, "notify", ".", "--no-blame", "-v")

        assert code == EXIT_ERROR
        assert "SlackWebhookNotifier failed: unexpected OSError" in err and "hunter2" not in err and "Traceback" not in err
        assert "Traceback (most recent call last)" in verbose_err

    def test_the_fail_on_condition_wins_over_a_failed_notification(self, capsys, configured, posts):
        posts.failing["Slack webhook"] = NotificationError("Slack webhook POST failed with HTTP 500 (attempt 3/3)")

        code, _, err = run(capsys, "notify", ".", "--no-blame", "--fail-on", "expired")

        assert code == EXIT_FAIL_ON
        assert "failed" in err and "--fail-on expired" in err

    def test_fail_on_alone_returns_1_after_notifying(self, capsys, configured, posts):
        assert main(["notify", ".", "--no-blame", "--fail-on", "any"]) == EXIT_FAIL_ON
        assert len(posts) == 2

    def test_reports_are_passed_to_the_notifiers(self, capsys, configured, monkeypatch):
        recording = RecordingNotifier()
        monkeypatch.setattr(cli, "build_notifiers", lambda notify: [recording])

        assert main(["notify", ".", "--no-blame"]) == EXIT_OK

        ((result, reports, new_count),) = recording.calls
        assert len(result.items) == 2
        assert [name for name, _ in reports] == ["Module-wise Summary", "Expired TODO Items", "Upcoming Week TODO Items"]
        assert new_count is None

    @needs_git
    def test_since_sets_new_count_on_digest_notifiers_only(self, capsys, project, monkeypatch):
        init_repo(project)
        write(project, "pyproject.toml", "[tool.todonotifier]\n" + NOTIFY_CONFIG)
        write(project, "a.py", "# TODO old\n")
        commit_all(project)
        write(project, "a.py", "# TODO old\n# TODO new one\n# TODO new two\n")
        commit_all(project, NEWER)
        digest, plain = RecordingNotifier(), PlainNotifier()
        monkeypatch.setattr(cli, "build_notifiers", lambda notify: [digest, plain])

        code = main(["notify", ".", "--since", "HEAD~1", "--no-blame"])

        assert code == EXIT_OK
        assert digest.calls[0][2] == 2
        assert len(digest.calls[0][0].items) == 2
        assert plain.calls == 1 and plain.new_count_seen == "untouched"

    def test_format_prints_the_result_too(self, capsys, configured, monkeypatch):
        monkeypatch.setattr(cli, "build_notifiers", lambda notify: [RecordingNotifier()])

        code, out, _ = run(capsys, "notify", ".", "--no-blame", "--format", "github")

        assert code == EXIT_OK
        assert out.startswith("::error file=a.py,line=1,")

    def test_email_notifier_is_built_from_the_config(self, capsys, project, monkeypatch):
        write(
            project,
            ".todonotifier.toml",
            '[notify.email]\nsmtp_host = "smtp.example.com"\nsender = "todo@example.com"\nrecipients = ["a@example.com"]\npassword_env = "TN_PASSWORD"\n',
        )
        monkeypatch.setenv("TN_PASSWORD", "hunter2")
        write(project, "a.py", "# TODO x\n")
        sent: list = []
        monkeypatch.setattr("todonotifier.notifier.EmailNotifier._send", lambda self, message: sent.append(message))

        code, _, err = run(capsys, "notify", ".", "--no-blame")

        assert code == EXIT_OK and len(sent) == 1
        assert "Notified EmailNotifier" in err and "hunter2" not in err


class TestInit:
    def test_creates_a_standalone_file_when_there_is_no_pyproject(self, capsys, project):
        code, out, _ = run(capsys, "init")

        assert code == EXIT_OK
        assert out.startswith("Created .todonotifier.toml.")
        assert "todonotifier scan ." in out
        with open(project / ".todonotifier.toml", encoding="utf-8") as file:
            assert file.read() == starter_config(pyproject=False)

    def test_never_overwrites_an_existing_file(self, capsys, project):
        write(project, ".todonotifier.toml", "# mine\ntags = ['X']\n")

        code, out, _ = run(capsys, "init")

        assert code == EXIT_OK and "already exists" in out
        with open(project / ".todonotifier.toml", encoding="utf-8") as file:
            assert file.read() == "# mine\ntags = ['X']\n"

    def test_appends_to_pyproject_and_keeps_its_content(self, capsys, project):
        original = '[project]\nname = "demo"\n\n[tool.black]\nline-length = 100\n'
        write(project, "pyproject.toml", original)

        code, out, _ = run(capsys, "init")

        with open(project / "pyproject.toml", encoding="utf-8") as file:
            text = file.read()
        assert code == EXIT_OK and "Added a commented [tool.todonotifier] section to pyproject.toml" in out
        assert text == original + "\n" + starter_config(pyproject=True)
        assert not os.path.exists(project / ".todonotifier.toml")
        assert load_config(start=str(project)).source == str(project / "pyproject.toml")

    def test_separates_the_section_from_a_file_without_a_final_newline(self, capsys, project):
        write(project, "pyproject.toml", '[project]\nname = "demo"')

        main(["init"])

        with open(project / "pyproject.toml", encoding="utf-8") as file:
            assert file.read().startswith('[project]\nname = "demo"\n\n# TODO Notifier configuration')

    def test_an_empty_pyproject_gets_the_section_only(self, capsys, project):
        write(project, "pyproject.toml", "")

        main(["init"])

        with open(project / "pyproject.toml", encoding="utf-8") as file:
            assert file.read() == starter_config(pyproject=True)

    def test_never_adds_a_second_section(self, capsys, project):
        original = '[tool.todonotifier]\ntags = ["FIXME"]\n'
        write(project, "pyproject.toml", original)

        code, out, _ = run(capsys, "init")
        again = run(capsys, "init", "--pyproject")

        assert code == EXIT_OK and "already has a [tool.todonotifier] section" in out
        assert again[0] == EXIT_OK
        with open(project / "pyproject.toml", encoding="utf-8") as file:
            assert file.read() == original

    def test_running_init_twice_changes_nothing_the_second_time(self, capsys, project):
        write(project, "pyproject.toml", '[project]\nname = "demo"\n')
        main(["init"])
        with open(project / "pyproject.toml", encoding="utf-8") as file:
            first = file.read()

        code, out, _ = run(capsys, "init")

        with open(project / "pyproject.toml", encoding="utf-8") as file:
            assert file.read() == first
        assert code == EXIT_OK and "already has" in out

    def test_a_standalone_file_wins_over_pyproject_by_default(self, capsys, project):
        write(project, ".todonotifier.toml", "")
        write(project, "pyproject.toml", "[project]\n")

        code, out, _ = run(capsys, "init")

        assert code == EXIT_OK and "already exists" in out
        with open(project / "pyproject.toml", encoding="utf-8") as file:
            assert file.read() == "[project]\n"

    def test_standalone_flag_creates_the_file_even_with_a_pyproject(self, capsys, project):
        write(project, "pyproject.toml", "[project]\n")

        code, out, _ = run(capsys, "init", "--standalone")

        assert code == EXIT_OK and out.startswith("Created .todonotifier.toml")
        with open(project / "pyproject.toml", encoding="utf-8") as file:
            assert file.read() == "[project]\n"

    def test_pyproject_flag_without_a_pyproject_is_a_usage_error(self, capsys, project):
        code, out, err = run(capsys, "init", "--pyproject")

        assert code == EXIT_USAGE and out == ""
        assert "no pyproject.toml" in err.lower() and "--standalone" in err

    def test_an_invalid_pyproject_is_a_usage_error_and_stays_untouched(self, capsys, project):
        write(project, "pyproject.toml", "[tool\nbroken")

        code, _, err = run(capsys, "init")

        assert code == EXIT_USAGE and "Invalid TOML" in err
        with open(project / "pyproject.toml", encoding="utf-8") as file:
            assert file.read() == "[tool\nbroken"

    def test_write_failures_are_usage_errors(self, capsys, project):
        with patch("builtins.open", side_effect=PermissionError(13, "Permission denied")):
            code, _, err = run(capsys, "init")

        assert code == EXIT_USAGE
        assert err == "todonotifier: error: Cannot write the config file: Permission denied\n"

    def test_the_starter_for_pyproject_and_standalone_load_cleanly_as_the_defaults(self, capsys, tmp_path):
        defaults = load_config(start=str(tmp_path))
        for pyproject, name in ((True, "pyproject.toml"), (False, ".todonotifier.toml")):
            directory = tmp_path / name.strip(".").replace(".", "_")
            directory.mkdir()
            write(directory, name, starter_config(pyproject))

            loaded = load_config(start=str(directory))

            assert loaded.source == str(directory / name)
            assert loaded.settings == defaults.settings
            assert (loaded.fail_on, loaded.notify) == ("none", {})

    def test_every_commented_example_of_the_starter_is_valid_when_uncommented(self, tmp_path):
        example = re.compile(r'^# (\[[a-z_.]+\]|[a-z_]+ = .*|"[^"]+" = .*)$')
        for pyproject in (True, False):
            lines = [example.sub(r"\1", line) for line in starter_config(pyproject).splitlines()]
            directory = tmp_path / ("p" if pyproject else "s")
            directory.mkdir()
            write(directory, "pyproject.toml" if pyproject else ".todonotifier.toml", "\n".join(lines) + "\n")

            loaded = load_config(start=str(directory))

            assert set(loaded.notify) == {"slack", "teams", "webhook", "email"}
            assert loaded.settings.default_due_days == 90
            assert loaded.settings.exclude_dirs["NAME"][-2:] == ["generated", "vendor"]
            assert loaded.settings.author_aliases == {"jane@example.com": "jane"}

    def test_the_starter_mentions_the_docs(self):
        assert "github.com/ashu-tosh-kumar/todo_notifier" in starter_config(True)


def test_cli_error_is_a_plain_exception():
    assert str(CliError("message")) == "message"
