"""Tests of `integrations/github-action/scripts/render.py`, the script behind the GitHub Action. It is imported by path: it is not part of the package"""

import contextlib
import importlib.util
import io
import json
import logging
import os
import runpy
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from types import ModuleType
from typing import Any
from unittest.mock import patch

from tests.sample_results import make_scan_result
from todonotifier import cli
from todonotifier.results import ScanResult, TodoItem

SCRIPT_PATH: str = os.path.join(os.path.dirname(__file__), os.pardir, "integrations", "github-action", "scripts", "render.py")


def load_script() -> ModuleType:
    """Imports the script from its path"""
    spec = importlib.util.spec_from_file_location("action_render", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


render: ModuleType = load_script()


class RenderTestCase(unittest.TestCase):
    """Base class: a temporary directory with `GITHUB_OUTPUT` and `GITHUB_STEP_SUMMARY` files"""

    def setUp(self) -> None:
        super().setUp()
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory: str = temp.name
        self.json_path: str = self.path("todonotifier.json")
        self.output_path: str = self.path("output")
        self.summary_path: str = self.path("summary")
        self.environ: dict[str, str] = {"GITHUB_OUTPUT": self.output_path, "GITHUB_STEP_SUMMARY": self.summary_path}

    def path(self, name: str) -> str:
        return os.path.join(self.directory, name)

    def write_result(self, result: ScanResult) -> None:
        with open(self.json_path, "w", encoding="utf-8") as file:
            json.dump(result.to_dict(), file)

    def read(self, path: str) -> str:
        with open(path, encoding="utf-8") as file:
            return file.read()

    def outputs(self) -> dict[str, str]:
        return dict(line.split("=", 1) for line in self.read(self.output_path).splitlines())

    def run_script(self, *argv: str) -> tuple[int, str]:
        """Runs `main` with the fake environment and returns the exit code and stdout"""
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code: int = render.main(list(argv), self.environ)
        return code, buffer.getvalue()


class TestHelpers(RenderTestCase):
    def test_load_result_reads_the_json_of_the_cli(self) -> None:
        self.write_result(make_scan_result())

        result = render.load_result(self.json_path)

        self.assertEqual(len(result.items), 10)
        self.assertEqual(result.items[0].file, "src/app.py")

    def test_plural(self) -> None:
        self.assertEqual(render.plural(1, "TODO", "TODOs"), "TODO")
        self.assertEqual(render.plural(0, "TODO", "TODOs"), "TODOs")
        self.assertEqual(render.plural(2, "TODO", "TODOs"), "TODOs")

    def test_write_outputs_appends_lines(self) -> None:
        render.write_outputs(self.output_path, {"total": "3"})
        render.write_outputs(self.output_path, {"new": ""})

        self.assertEqual(self.read(self.output_path), "total=3\nnew=\n")

    def test_write_outputs_and_summary_do_nothing_outside_of_github(self) -> None:
        render.write_outputs(None, {"total": "3"})
        render.append_summary(None, "text")
        render.write_outputs("", {"total": "3"})

        self.assertEqual(os.listdir(self.directory), [])

    def test_append_summary_adds_to_the_file(self) -> None:
        render.append_summary(self.summary_path, "one")
        render.append_summary(self.summary_path, "two")

        self.assertEqual(self.read(self.summary_path), "one\ntwo\n")


class TestBuildComment(unittest.TestCase):
    @staticmethod
    def digest_of(result: ScanResult) -> Any:
        return render.build_digest(result, top_n=render.MARKDOWN_TOP_N, new_count=len(result.items))

    def test_the_headline_counts_the_todos_of_the_pull_request(self) -> None:
        digest = self.digest_of(make_scan_result())

        comment: str = render.build_comment(digest, render.render_markdown(digest))

        self.assertTrue(comment.startswith(f"{render.COMMENT_MARKER}\nThis PR adds 10 TODOs: 4 without an owner, 4 overdue, 3 stale.\n\n## TODO digest"))

    def test_a_single_todo_is_singular(self) -> None:
        result = make_scan_result()
        result.items = result.items[:1]
        digest = self.digest_of(result)

        comment: str = render.build_comment(digest, "markdown")

        self.assertIn("This PR adds 1 TODO: 0 without an owner, 1 overdue, 0 stale.", comment)

    def test_without_todos_it_says_so(self) -> None:
        digest = self.digest_of(ScanResult(generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc)))

        self.assertEqual(render.build_comment(digest, "markdown"), f"{render.COMMENT_MARKER}\nThis PR adds no TODOs.\n\nmarkdown")

    def test_a_long_digest_is_cut_at_a_line_end_below_the_limit_of_github(self) -> None:
        digest = self.digest_of(make_scan_result())
        markdown: str = "\n".join(f"- line {number}" for number in range(20000))

        comment: str = render.build_comment(digest, markdown)

        self.assertLessEqual(len(comment), render.MAX_COMMENT_CHARS)
        self.assertLess(render.MAX_COMMENT_CHARS, 65536)
        self.assertTrue(comment.endswith(render.TRUNCATED_NOTICE))
        self.assertTrue(comment.startswith(render.COMMENT_MARKER))
        body: str = comment[: -len(render.TRUNCATED_NOTICE)]
        self.assertRegex(body.splitlines()[-1], r"^- line \d+$")

    def test_a_long_text_without_line_breaks_is_cut_anyway(self) -> None:
        digest = self.digest_of(ScanResult(generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc)))
        # The header has line breaks, so cut inside the first line: only possible if there are none before the limit
        with patch.object(render, "COMMENT_MARKER", "m" * 70000):
            comment: str = render.build_comment(digest, "x")

        self.assertLessEqual(len(comment), render.MAX_COMMENT_CHARS)
        self.assertTrue(comment.endswith(render.TRUNCATED_NOTICE))


class TestRender(RenderTestCase):
    def test_pr_mode_prints_annotations_writes_the_summary_and_the_outputs(self) -> None:
        self.write_result(make_scan_result())

        code, stdout = self.run_script("render", "--input", self.json_path, "--mode", "pr")

        self.assertEqual(code, 0)
        annotations = [line for line in stdout.splitlines() if line.startswith("::")]
        self.assertEqual(len(annotations), 10)
        self.assertTrue(annotations[0].startswith("::error file=src/app.py,line=10,title="))
        self.assertEqual(self.outputs(), {"total": "10", "overdue": "4", "stale": "3", "new": "10"})
        summary: str = self.read(self.summary_path)
        self.assertTrue(summary.startswith("_Only TODOs on lines added or changed in this pull request._\n\n## TODO digest 2026-05-01"))
        self.assertIn("| Open | Overdue | Stale | Due this week | Unowned | New |", summary)

    def test_digest_mode_writes_the_reports_and_has_no_new_count(self) -> None:
        self.write_result(make_scan_result())
        reports: str = self.path("reports")

        code, stdout = self.run_script("render", "--input", self.json_path, "--mode", "digest", "--report-dir", reports)

        self.assertEqual(code, 0)
        self.assertEqual(
            self.outputs(),
            {"total": "10", "overdue": "4", "stale": "3", "new": "", "report-path": reports},
        )
        self.assertEqual(sorted(os.listdir(reports)), ["Expired TODO Items.html", "Module-wise Summary.html", "Upcoming Week TODO Items.html"])
        summary: str = self.read(self.summary_path)
        self.assertNotIn("Only TODOs on lines", summary)
        self.assertNotIn("| New |", summary)
        self.assertEqual(len([line for line in stdout.splitlines() if line.startswith("::")]), 10)  # Annotations are printed in digest mode as well

    def test_the_report_generators_do_not_flood_the_log(self) -> None:
        self.write_result(make_scan_result())
        package_logger = logging.getLogger("todonotifier")
        level_before: int = package_logger.level

        records: list[logging.LogRecord] = []
        handler = logging.Handler()
        handler.emit = records.append  # type: ignore[method-assign]
        package_logger.addHandler(handler)
        self.addCleanup(package_logger.removeHandler, handler)

        self.run_script("render", "--input", self.json_path, "--mode", "digest", "--report-dir", self.path("reports"))

        self.assertEqual([record.getMessage() for record in records if record.levelno < logging.WARNING], [])
        self.assertEqual(package_logger.level, level_before)

    def test_the_comment_file_is_written_on_request(self) -> None:
        self.write_result(make_scan_result())
        comment_path: str = self.path("comment.md")

        self.run_script("render", "--input", self.json_path, "--mode", "pr", "--comment-file", comment_path)

        comment: str = self.read(comment_path)
        self.assertTrue(comment.startswith(render.COMMENT_MARKER + "\nThis PR adds 10 TODOs"))

    def test_no_comment_file_without_the_flag(self) -> None:
        self.write_result(make_scan_result())

        self.run_script("render", "--input", self.json_path, "--mode", "pr")

        self.assertFalse(os.path.exists(self.path("comment.md")))

    def test_an_empty_result_prints_only_the_count_line(self) -> None:
        self.write_result(ScanResult(scanned_files=["a.py"], root=self.directory, generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc)))

        code, stdout = self.run_script("render", "--input", self.json_path, "--mode", "pr")

        self.assertEqual((code, stdout), (0, "0 TODOs: 0 overdue, 0 stale, 0 unowned\n"))
        self.assertEqual(self.outputs(), {"total": "0", "overdue": "0", "stale": "0", "new": "0"})
        self.assertIn("Nothing is overdue", self.read(self.summary_path))

    def test_it_works_outside_of_github_actions(self) -> None:
        self.write_result(make_scan_result())

        with patch.dict(os.environ, {}, clear=True):
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code: int = render.main(["render", "--input", self.json_path, "--mode", "pr"])

        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(self.output_path))

    def test_annotation_paths_are_relative_to_the_repository_root(self) -> None:
        """End to end: the CLI writes the JSON, the script renders it (a scan root below the repository root, as with `working-directory`)"""
        repository: str = self.path("repo")
        source: str = os.path.join(repository, "service", "app.py")
        os.makedirs(os.path.dirname(source))
        with open(source, "w", encoding="utf-8") as file:
            file.write("# TODO {2020-01-01} @alice long gone\n")
        previous: str = os.getcwd()
        os.chdir(os.path.join(repository, "service"))
        self.addCleanup(os.chdir, previous)

        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["scan", "--no-blame", "--format", "json", "--output", self.json_path, "--fail-on", "none"]), 0)
        # The repository root is the parent of the scan root, as if `working-directory: service` was used (git itself is not needed for this test)
        with patch.object(render, "find_git_root", side_effect=lambda root: os.path.dirname(root)):
            _, stdout = self.run_script("render", "--input", self.json_path, "--mode", "pr")

        self.assertTrue(stdout.startswith("::error file=service/app.py,line=1,"), stdout)
        self.assertEqual(self.outputs()["overdue"], "1")


class TestCheck(RenderTestCase):
    def make_result(self, *, overdue: bool) -> ScanResult:
        item = TodoItem(
            file="a.py",
            line=1,
            tag="TODO",
            message="late" if overdue else "fine",
            author="alice",
            author_source="annotation",
            due_date=date(2020, 1, 1) if overdue else date(2999, 1, 1),
            due_source="explicit",
        )
        item.refresh_status(date(2026, 5, 1))
        return ScanResult(items=[item], scanned_files=["a.py"], root="/r", generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc))

    def check(self, fail_on: str, *extra: str) -> tuple[int, str]:
        return self.run_script("check", "--input", self.json_path, "--fail-on", fail_on, *extra)

    def test_none_never_fails(self) -> None:
        self.write_result(self.make_result(overdue=True))

        self.assertEqual(self.check("none"), (0, ""))

    def test_the_condition_met_fails_with_the_rule_of_the_command_line(self) -> None:
        result = self.make_result(overdue=True)
        self.write_result(result)

        code, stdout = self.check("expired")

        self.assertEqual(code, 1)
        self.assertEqual(stdout, f"::error title=fail-on expired::--fail-on expired: {cli.fail_on_message(result, 'expired')}\n")
        self.assertIn("1 overdue TODO", stdout)

    def test_the_condition_not_met_passes(self) -> None:
        self.write_result(self.make_result(overdue=False))

        self.assertEqual(self.check("expired"), (0, ""))
        self.assertEqual(self.check("any")[0], 1)
        self.assertEqual(self.check("stale"), (0, ""))
        self.assertEqual(self.check("incomplete"), (0, ""))

    def test_a_failed_scan_fails_with_an_explanation_and_needs_no_json(self) -> None:
        for exit_code, expected in ((2, "usage or configuration error"), (3, "unexpected error"), (9, "unexpected exit code")):
            with self.subTest(exit_code=exit_code):
                code, stdout = self.check("expired", "--scan-exit", str(exit_code))

                self.assertEqual(code, 1)
                self.assertEqual(stdout.count("::error"), 1)
                self.assertIn(f"todonotifier scan exited with {exit_code}: ", stdout)
                self.assertIn(expected, stdout)

    def test_a_failed_notification_fails(self) -> None:
        self.write_result(self.make_result(overdue=False))
        for exit_code, expected in ((2, "usage or configuration error"), (3, "could not be delivered"), (7, "unexpected exit code")):
            with self.subTest(exit_code=exit_code):
                code, stdout = self.check("none", "--notify-exit", str(exit_code))

                self.assertEqual(code, 1)
                self.assertIn(f"todonotifier notify exited with {exit_code}: ", stdout)
                self.assertIn(expected, stdout)

    def test_a_failed_notification_and_the_fail_on_condition_are_both_reported(self) -> None:
        self.write_result(self.make_result(overdue=True))

        code, stdout = self.check("expired", "--notify-exit", "3")

        self.assertEqual(code, 1)
        self.assertEqual(stdout.count("::error"), 2)

    def test_an_unknown_fail_on_value_is_a_usage_error(self) -> None:
        self.write_result(self.make_result(overdue=True))

        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            self.check("sometimes")

        self.assertEqual(raised.exception.code, 2)


class TestEntryPoint(RenderTestCase):
    def test_main_without_arguments_uses_sys_argv_and_the_real_environment(self) -> None:
        self.write_result(make_scan_result())
        argv = ["render.py", "check", "--input", self.json_path, "--fail-on", "none"]

        with patch.object(sys, "argv", argv):
            self.assertEqual(render.main(), 0)

    def test_running_the_file_exits_with_the_code(self) -> None:
        self.write_result(make_scan_result())
        argv = ["render.py", "check", "--input", self.json_path, "--fail-on", "any"]

        with patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as raised:
            runpy.run_path(SCRIPT_PATH, run_name="__main__")

        self.assertEqual(raised.exception.code, 1)


class TestActionFiles(unittest.TestCase):
    """The files of the action, read as the runner does"""

    ACTION_DIRECTORY: str = os.path.join(os.path.dirname(__file__), os.pardir, "integrations", "github-action")

    @classmethod
    def load_yaml(cls, *parts: str) -> Any:
        import yaml  # Comes with pre-commit (a dev dependency); see tests/test_pre_commit_hooks.py

        with open(os.path.join(cls.ACTION_DIRECTORY, *parts), encoding="utf-8") as file:
            return yaml.safe_load(file)

    def test_action_yml_declares_the_documented_inputs_and_outputs(self) -> None:
        action = self.load_yaml("action.yml")

        self.assertEqual(action["runs"]["using"], "composite")
        self.assertEqual(
            list(action["inputs"]),
            [
                "mode",
                "version",
                "package",
                "config",
                "working-directory",
                "fail-on",
                "default-due-days",
                "tags",
                "extensions",
                "slack-webhook",
                "teams-webhook",
                "webhook-url",
                "comment",
                "github-token",
                "python-version",
                "artifact-name",
            ],
        )
        self.assertEqual(list(action["outputs"]), ["total", "overdue", "stale", "new", "report-path"])
        defaults = {name: spec["default"] for name, spec in action["inputs"].items()}
        self.assertEqual(
            (defaults["mode"], defaults["fail-on"], defaults["default-due-days"], defaults["python-version"], defaults["comment"]),
            ("pr", "none", "90", "3.12", "false"),
        )
        for name, spec in action["inputs"].items():
            self.assertIn("description", spec, name)
            self.assertIsInstance(spec["default"], str, name)

    def test_inputs_and_event_data_never_appear_inside_a_run_script(self) -> None:
        """Injection safety: `${{ ... }}` in a `run:` script would paste attacker controlled text (a branch name, an input) into the shell"""
        for step in self.load_yaml("action.yml")["runs"]["steps"]:
            self.assertNotIn("${{", step.get("run", ""), step.get("name"))

    def test_actions_are_pinned_by_commit_sha_with_a_version_comment(self) -> None:
        with open(os.path.join(self.ACTION_DIRECTORY, "action.yml"), encoding="utf-8") as file:
            uses = [line.strip() for line in file if line.strip().startswith("uses:")]

        self.assertEqual(len(uses), 3)
        for line in uses:
            self.assertRegex(line, r"^uses: [\w./-]+@[0-9a-f]{40} # v\d+\.\d+\.\d+$")

    def test_the_default_version_is_the_version_of_this_package(self) -> None:
        """Bump `version` in action.yml with pyproject.toml (RELEASING.md), or the action installs an older release than the one documented"""
        self.assertEqual(self.load_yaml("action.yml")["inputs"]["version"]["default"], cli.get_version())

    def test_the_selftest_workflow_expects_what_the_fixtures_contain(self) -> None:
        """The numbers asserted by .github/workflows/action-selftest.yml, checked here with the same config and the command line of the action"""
        import yaml

        from tests.test_languages import EXPECTED_FIXTURE_ITEMS

        workflow_path: str = os.path.join(os.path.dirname(__file__), os.pardir, ".github", "workflows", "action-selftest.yml")
        with open(workflow_path, encoding="utf-8") as file:
            workflow = yaml.safe_load(file)
        config: str = os.path.join(self.ACTION_DIRECTORY, "selftest.toml")
        fixtures: str = os.path.join(os.path.dirname(__file__), "fixtures")
        self.assertEqual(workflow["env"]["EXPECTED_FIXTURE_TOTAL"], str(len(EXPECTED_FIXTURE_ITEMS)))

        for folder, total, overdue in (("languages", len(EXPECTED_FIXTURE_ITEMS), 0), ("action", 3, 2)):
            with self.subTest(folder=folder), tempfile.TemporaryDirectory() as temp:
                output: str = os.path.join(temp, "scan.json")
                with contextlib.redirect_stderr(io.StringIO()):
                    code: int = cli.main(
                        ["scan", os.path.join(fixtures, folder), "--config", config, "--no-blame", "--fail-on", "none", "--format", "json", "--output", output]
                    )
                with open(output, encoding="utf-8") as file:
                    result = ScanResult.from_dict(json.load(file))
                self.assertEqual(code, 0)
                self.assertEqual((len(result.items), len(result.overdue())), (total, overdue))
                self.assertEqual(cli.fail_on_message(result, "expired") is not None, overdue > 0)
