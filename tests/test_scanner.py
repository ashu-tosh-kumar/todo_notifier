import json
import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import date
from unittest.mock import patch

from todonotifier.results import ScanResult, TodoItem
from todonotifier.scanner import ScanException, scan
from todonotifier.settings import ScanSettings
from todonotifier.settings_file import resolve_settings
from todonotifier.todo_notifier import parse_files_for_todo_items

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_FILES = [os.path.join(TESTS_DIR, "sample_test_file.py"), os.path.join(TESTS_DIR, "sample_test_file2.py")]
TODAY = date(2025, 6, 15)
GIT_AVAILABLE = shutil.which("git") is not None


class ScannerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = os.path.realpath(self._tmp.name)
        self._old_cwd = os.getcwd()
        self.addCleanup(os.chdir, self._old_cwd)

    def write(self, rel_path: str, content: str) -> str:
        path = os.path.join(self.tmp, *rel_path.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return path

    def listing(self) -> list:
        return sorted(os.path.join(dir_path, name) for dir_path, dir_names, file_names in os.walk(self.tmp) for name in dir_names + file_names)


class TestScanEquivalence(ScannerTestCase):
    def test_scan_should_find_the_same_todos_as_parse_files_for_todo_items(self):
        result = scan(ScanSettings(paths=SAMPLE_FILES), today=TODAY)

        # `scan` parses with the extended syntax (one colon after a tag is dropped), so the line "class" plus the tag and a colon has the message "" and not ":"
        expected = parse_files_for_todo_items(result.root, SAMPLE_FILES, False, extended_syntax=True)
        actual = [(todo.msg, todo.user.user_name, str(todo.completion_date), todo.position.line_no) for todos in result.to_legacy().values() for todo in todos]
        legacy = [(todo.msg, todo.user.user_name, str(todo.completion_date), todo.position.line_no) for todos in expected.values() for todo in todos]

        self.assertGreater(len(legacy), 0)
        self.assertEqual(sorted(legacy), sorted(actual))

    def test_scan_with_ignore_case_should_match_the_legacy_parser(self):
        result = scan(ScanSettings(paths=SAMPLE_FILES, ignore_case=True), today=TODAY)

        expected = parse_files_for_todo_items(result.root, SAMPLE_FILES, True)

        self.assertEqual(sum(len(todos) for todos in expected.values()), len(result.items))

    def test_scan_should_map_every_legacy_todo_field(self):
        path = self.write("a.py", "# TODO {2025-06-10} @alice fix it\n# TODO no owner no date\n")

        result = scan(ScanSettings(paths=[path]), today=TODAY)

        self.assertEqual(
            [
                TodoItem(
                    file="a.py",
                    line=1,
                    tag="TODO",
                    message="fix it",
                    author="alice",
                    author_source="annotation",
                    due_date=date(2025, 6, 10),
                    due_source="explicit",
                    is_overdue=True,
                    days_past_due=5,
                ),
                TodoItem(file="a.py", line=2, tag="TODO", message="no owner no date"),
            ],
            result.items,
        )


class TestScanPurity(ScannerTestCase):
    def test_scan_should_create_no_files_and_no_temp_dirs(self):
        self.write("src/a.py", "# TODO {2020-01-01} @alice x\n")
        before = self.listing()

        with patch("tempfile.mkdtemp") as spy_mkdtemp, patch("tempfile.mkstemp") as spy_mkstemp, patch("shutil.copytree") as spy_copytree:
            scan(ScanSettings(paths=[self.tmp]), today=TODAY)

        self.assertEqual(before, self.listing())
        spy_mkdtemp.assert_not_called()
        spy_mkstemp.assert_not_called()
        spy_copytree.assert_not_called()


class TestScanPaths(ScannerTestCase):
    def test_scan_of_a_directory_should_use_posix_paths_relative_to_it(self):
        self.write("src/pkg/a.py", "# TODO a\n")
        self.write("b.py", "# TODO b\n")

        result = scan(ScanSettings(paths=[self.tmp]), today=TODAY)

        self.assertEqual(self.tmp, result.root)
        self.assertEqual(["b.py", "src/pkg/a.py"], [item.file for item in result.items])
        self.assertEqual(["b.py", "src/pkg/a.py"], result.scanned_files)

    def test_scan_should_resolve_relative_paths_against_the_working_directory(self):
        self.write("src/a.py", "# TODO a\n")
        os.chdir(self.tmp)

        result = scan(ScanSettings(paths=["src"]), today=TODAY)

        self.assertEqual(os.path.join(self.tmp, "src"), result.root)
        self.assertEqual(["a.py"], [item.file for item in result.items])

    def test_scan_with_default_paths_should_scan_the_working_directory(self):
        self.write("a.py", "# TODO a\n")
        os.chdir(self.tmp)

        result = scan(ScanSettings(), today=TODAY)

        self.assertEqual(self.tmp, result.root)
        self.assertEqual(["a.py"], result.scanned_files)

    def test_scan_of_individual_files_inside_the_working_directory_should_be_relative_to_it(self):
        a = self.write("pkg/a.py", "# TODO a\n")
        b = self.write("pkg/b.py", "# TODO b\n")
        self.write("pkg/c.py", "# TODO not selected\n")
        os.chdir(self.tmp)

        result = scan(ScanSettings(paths=[a, "pkg/b.py"]), today=TODAY)

        self.assertEqual(self.tmp, result.root)
        self.assertEqual(["pkg/a.py", "pkg/b.py"], [item.file for item in result.items])
        self.assertTrue(os.path.samefile(b, os.path.join(result.root, "pkg/b.py")))

    def test_scan_of_a_directory_and_files_should_not_duplicate_files(self):
        a = self.write("pkg/a.py", "# TODO a\n")
        os.chdir(self.tmp)

        result = scan(ScanSettings(paths=["pkg", a]), today=TODAY)

        self.assertEqual(["pkg/a.py"], result.scanned_files)
        self.assertEqual(1, len(result.items))

    def test_scan_of_paths_outside_the_working_directory_should_use_their_common_directory(self):
        a = self.write("one/x/a.py", "# TODO a\n")
        b = self.write("one/y/b.py", "# TODO b\n")
        elsewhere = os.path.join(self.tmp, "cwd")
        os.makedirs(elsewhere)
        os.chdir(elsewhere)

        result = scan(ScanSettings(paths=[a, b]), today=TODAY)

        self.assertEqual(os.path.join(self.tmp, "one"), result.root)
        self.assertEqual(["x/a.py", "y/b.py"], result.scanned_files)

    def test_scan_of_a_file_outside_the_working_directory_should_use_its_directory(self):
        a = self.write("one/a.py", "# TODO a\n")
        elsewhere = os.path.join(self.tmp, "cwd")
        os.makedirs(elsewhere)
        os.chdir(elsewhere)

        result = scan(ScanSettings(paths=[a]), today=TODAY)

        self.assertEqual(os.path.join(self.tmp, "one"), result.root)
        self.assertEqual(["a.py"], result.scanned_files)

    def test_scan_of_an_individual_file_should_apply_extensions_and_exclusions(self):
        wrong_extension = self.write("a.txt", "TODO a\n")
        excluded = self.write("local_settings.py", "# TODO excluded by default\n")
        included = self.write("ok.py", "# TODO ok\n")
        os.chdir(self.tmp)

        result = scan(ScanSettings(paths=[wrong_extension, excluded, included]), today=TODAY)

        self.assertEqual(["ok.py"], result.scanned_files)

    def test_scan_should_skip_excluded_directories_and_other_extensions(self):
        self.write("venv/a.py", "# TODO hidden\n")
        self.write("src/a.py", "# TODO shown\n")
        self.write("src/a.js", "// TODO other language\n")

        default = scan(ScanSettings(paths=[self.tmp]), today=TODAY)
        with_js = scan(ScanSettings(paths=[self.tmp], extensions=[".js"]), today=TODAY)

        self.assertEqual(["src/a.py"], default.scanned_files)
        self.assertEqual(["src/a.js"], with_js.scanned_files)

    def test_scan_should_list_files_without_todos_in_scanned_files(self):
        self.write("clean.py", "x = 1\n")

        result = scan(ScanSettings(paths=[self.tmp]), today=TODAY)

        self.assertEqual([], result.items)
        self.assertEqual(["clean.py"], result.scanned_files)

    def test_scan_should_order_items_by_file_and_line(self):
        self.write("b.py", "# TODO 1\n\n# TODO 2\n")
        self.write("a.py", "\n# TODO 3\n")

        result = scan(ScanSettings(paths=[self.tmp]), today=TODAY)

        self.assertEqual([("a.py", 2), ("b.py", 1), ("b.py", 3)], [(item.file, item.line) for item in result.items])

    def test_scan_without_paths_should_raise(self):
        with self.assertRaises(ScanException):
            scan(ScanSettings(paths=[]))

    def test_scan_of_a_missing_path_should_raise(self):
        with self.assertRaises(ScanException):
            scan(ScanSettings(paths=[os.path.join(self.tmp, "missing")]))


class TestScanResultFields(ScannerTestCase):
    def test_scan_should_use_the_given_reference_day_for_status_and_generated_at(self):
        self.write("a.py", "# TODO {2025-06-10} one\n# TODO {2025-06-20} two\n")

        result = scan(ScanSettings(paths=[self.tmp]), today=TODAY)

        self.assertEqual([1], [item.line for item in result.overdue()])
        self.assertEqual([2], [item.line for item in result.due_within(7)])
        self.assertEqual(TODAY, result.generated_at.date())
        self.assertEqual(1, result.schema_version)

    def test_scan_without_today_should_use_the_current_date(self):
        self.write("a.py", "# TODO {2000-01-01} old\n")

        result = scan(ScanSettings(paths=[self.tmp]))

        self.assertEqual(1, len(result.overdue()))
        self.assertEqual(date.today(), result.generated_at.date())

    def test_scan_should_build_web_urls_when_repo_url_and_commit_are_set(self):
        self.write("src/a.py", "# TODO a\n\n# TODO b\n")

        with_urls = scan(ScanSettings(paths=[self.tmp], repo_web_url="https://github.com/org/repo", commit_sha="abc123"), today=TODAY)
        without_urls = scan(ScanSettings(paths=[self.tmp], repo_web_url="https://github.com/org/repo"), today=TODAY)

        self.assertEqual(
            ["https://github.com/org/repo/blob/abc123/src/a.py#L1", "https://github.com/org/repo/blob/abc123/src/a.py#L3"],
            [item.web_url for item in with_urls.items],
        )
        self.assertEqual([None, None], [item.web_url for item in without_urls.items])

    def test_scan_result_should_survive_a_json_round_trip(self):
        result = scan(ScanSettings(paths=SAMPLE_FILES), today=TODAY)

        restored = ScanResult.from_dict(json.loads(json.dumps(result.to_dict())))

        self.assertEqual(result, restored)

    def test_scan_should_call_the_enrich_hook_with_the_items(self):
        self.write("a.py", "# TODO a\n")

        with patch("todonotifier.scanner._enrich_items", side_effect=lambda items, settings, root, today: items[:0]) as spy_enrich:
            result = scan(ScanSettings(paths=[self.tmp]), today=TODAY)

        spy_enrich.assert_called_once()
        self.assertEqual([], result.items)
        self.assertEqual(TODAY, spy_enrich.call_args.args[3])


if __name__ == "__main__":
    unittest.main()


class TestScanGitHook(ScannerTestCase):
    def test_scan_should_call_git_enrichment_only_when_use_git_blame_is_on(self):
        path = self.write("a.py", "# TODO one\n")

        with patch("todonotifier.scanner.enrich_with_git", side_effect=lambda items, settings, root, today: items) as spy:
            scan(ScanSettings(paths=[path]), today=TODAY)
            spy.assert_not_called()

            scan(ScanSettings(paths=[path], use_git_blame=True), today=TODAY)

        spy.assert_called_once()
        self.assertEqual(os.path.dirname(path), spy.call_args.args[2])
        self.assertEqual(TODAY, spy.call_args.args[3])


class TestScanDetection(ScannerTestCase):
    def test_scan_should_honour_tags(self):
        path = self.write("a.py", "# TODO a\n# FIXME b\n# NOTE c\n")

        result = scan(ScanSettings(paths=[path], tags=["TODO", "FIXME"]), today=TODAY)

        self.assertEqual([("TODO", "a"), ("FIXME", "b")], [(item.tag, item.message) for item in result.items])

    def test_scan_should_default_to_the_todo_tag_only(self):
        path = self.write("a.py", "# TODO a\n# FIXME b\n")

        result = scan(ScanSettings(paths=[path]), today=TODAY)

        self.assertEqual(["TODO"], [item.tag for item in result.items])

    def test_scan_should_honour_ignore_case_and_report_the_configured_tag(self):
        path = self.write("a.py", "# todo a\nfrom todonotifier import x\n")

        result = scan(ScanSettings(paths=[path], ignore_case=True), today=TODAY)

        self.assertEqual([("TODO", "a", 1)], [(item.tag, item.message, item.line) for item in result.items])

    def test_scan_should_honour_require_comment(self):
        path = self.write("a.py", 'x = "TODO list"\n# TODO real\n')

        self.assertEqual([1, 2], [item.line for item in scan(ScanSettings(paths=[path]), today=TODAY).items])
        self.assertEqual([2], [item.line for item in scan(ScanSettings(paths=[path], require_comment=True), today=TODAY).items])

    def test_scan_should_understand_owner_in_parentheses_and_colons(self):
        path = self.write("a.py", "# TODO(ashu): fix this\n# FIXME {2020-01-01} @bob: later\n")

        result = scan(ScanSettings(paths=[path], tags=["TODO", "FIXME"]), today=TODAY)

        self.assertEqual(
            [("TODO", "fix this", "ashu", "annotation", None), ("FIXME", "later", "bob", "annotation", date(2020, 1, 1))],
            [(item.tag, item.message, item.author, item.author_source, item.due_date) for item in result.items],
        )

    def test_scan_should_reject_invalid_tags(self):
        path = self.write("a.py", "# TODO a\n")

        with self.assertRaises(ScanException):
            scan(ScanSettings(paths=[path], tags=[]), today=TODAY)

    def test_scan_should_skip_binary_files(self):
        self.write("a.py", "# TODO a\n")
        with open(os.path.join(self.tmp, "b.py"), "wb") as f:
            f.write(b"# TODO b\x00")

        result = scan(ScanSettings(paths=[self.tmp]), today=TODAY)

        self.assertEqual(["a.py"], result.scanned_files)

    def test_dot_git_should_be_excluded_by_default(self):
        self.write(".git/hooks/x.md", "<!-- TODO hidden -->\n")
        self.write("docs/a.md", "<!-- TODO shown -->\n")

        result = scan(ScanSettings(paths=[self.tmp], extensions=["md"]), today=TODAY)

        self.assertEqual(["docs/a.md"], [item.file for item in result.items])

    def test_scan_with_the_cli_defaults_should_report_comments_of_many_languages(self):
        self.write("a.js", "const s = 'TODO list'; // TODO js\n")
        self.write("b.rs", "/* FIXME(alice): rust */\n")
        self.write("c.md", "TODO not in a comment\n<!-- HACK md -->\n")

        settings = resolve_settings({"paths": [self.tmp], "use_git_blame": False}, None, start=self.tmp)
        result = scan(settings, today=TODAY)

        self.assertEqual(
            [("a.js", "TODO", "js"), ("b.rs", "FIXME", "rust"), ("c.md", "HACK", "md")],
            [(item.file, item.tag, item.message) for item in result.items],
        )


def _git(cwd: str, *args: str) -> None:
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, check=True)


@unittest.skipUnless(GIT_AVAILABLE, "git is not installed")
class TestScanRespectGitignore(ScannerTestCase):
    def make_repo(self) -> None:
        _git(self.tmp, "init", "-q")
        self.write(".gitignore", "node_modules/\n*.min.js\n")
        self.write("src/a.js", "// TODO tracked\n")
        self.write("node_modules/x.js", "// TODO in node_modules\n")
        self.write("src/b.min.js", "// TODO minified\n")
        _git(self.tmp, "add", ".gitignore", "src/a.js")
        self.write("src/new.js", "// TODO untracked but not ignored\n")

    def test_default_cli_settings_should_not_report_gitignored_files(self):
        self.make_repo()

        settings = resolve_settings({"paths": [self.tmp]}, None, start=self.tmp)
        settings.use_git_blame = False
        result = scan(settings, today=TODAY)

        self.assertEqual(["src/a.js", "src/new.js"], [item.file for item in result.items])

    def test_without_respect_gitignore_the_tree_should_be_walked(self):
        self.make_repo()

        result = scan(ScanSettings(paths=[self.tmp], extensions=["js"], exclude_dirs={"NAME": []}), today=TODAY)

        self.assertEqual(["node_modules/x.js", "src/a.js", "src/b.min.js", "src/new.js"], [item.file for item in result.items])

    def test_git_listing_should_still_apply_extensions_and_exclusions(self):
        self.make_repo()
        self.write("src/skip/c.js", "// TODO excluded dir\n")
        self.write("src/d.js", "// TODO excluded file\n")
        self.write("src/e.py", "# TODO other extension\n")
        self.write("src/sub/skip/deep.js", "// TODO deep excluded dir\n")
        _git(self.tmp, "add", "-A")
        settings = ScanSettings(
            paths=[self.tmp],
            extensions=["js"],
            respect_gitignore=True,
            exclude_dirs={"NAME": ["skip"]},
            exclude_files={"NAME": ["d.js"]},
        )

        result = scan(settings, today=TODAY)

        self.assertEqual(["src/a.js", "src/new.js"], [item.file for item in result.items])

    def test_exclusion_by_absolute_path_should_apply(self):
        self.make_repo()
        settings = ScanSettings(paths=[self.tmp], extensions=["js"], respect_gitignore=True, exclude_dirs={"ABS_PATH": [os.path.join(self.tmp, "src")]})

        result = scan(settings, today=TODAY)

        self.assertEqual([], result.items)

    def test_scan_of_a_subdirectory_should_list_only_that_subdirectory(self):
        self.make_repo()
        self.write("other/z.js", "// TODO elsewhere\n")

        result = scan(ScanSettings(paths=[os.path.join(self.tmp, "src")], extensions=["js"], respect_gitignore=True), today=TODAY)

        self.assertEqual(["a.js", "new.js"], [item.file for item in result.items])

    def test_tracked_file_deleted_from_disk_should_be_skipped(self):
        self.make_repo()
        os.remove(os.path.join(self.tmp, "src", "a.js"))

        result = scan(ScanSettings(paths=[self.tmp], extensions=["js"], respect_gitignore=True), today=TODAY)

        self.assertEqual(["src/new.js"], [item.file for item in result.items])

    def test_individual_files_should_be_checked_against_gitignore(self):
        self.make_repo()
        ignored = os.path.join(self.tmp, "node_modules", "x.js")
        shown = os.path.join(self.tmp, "src", "a.js")

        result = scan(ScanSettings(paths=[ignored, shown], extensions=["js"], respect_gitignore=True), today=TODAY)

        self.assertEqual(["src/a.js"], [item.file for item in result.items])

    def test_many_explicit_files_should_need_one_git_ls_files_call_and_no_blame_without_use_git_blame(self):
        self.make_repo()
        files = [self.write(f"src/f{number}.js", f"// TODO number {number}\n") for number in range(30)]
        real_run = subprocess.run
        calls = []

        def spy(command, *args, **kwargs):
            calls.append(command)
            return real_run(command, *args, **kwargs)

        with patch("todonotifier.git_meta.subprocess.run", side_effect=spy):
            result = scan(ScanSettings(paths=files, extensions=["js"], respect_gitignore=True), today=TODAY)

        self.assertEqual(30, len(result.items))
        self.assertEqual(1, sum(1 for command in calls if "ls-files" in command))
        self.assertEqual(0, sum(1 for command in calls if "blame" in command))
        self.assertLessEqual(len(calls), 3)

    def test_many_explicit_files_with_blame_should_need_one_ls_files_call_and_one_blame_per_file(self):
        self.make_repo()
        files = [self.write(f"src/f{number}.js", f"// TODO number {number}\n") for number in range(10)]
        _git(self.tmp, "add", "-A")
        real_run = subprocess.run
        calls = []

        def spy(command, *args, **kwargs):
            calls.append(command)
            return real_run(command, *args, **kwargs)

        with patch("todonotifier.git_meta.subprocess.run", side_effect=spy):
            scan(ScanSettings(paths=files, extensions=["js"], respect_gitignore=True, use_git_blame=True), today=TODAY)

        self.assertEqual(1, sum(1 for command in calls if "ls-files" in command))
        self.assertEqual(10, sum(1 for command in calls if "blame" in command))

    def test_outside_a_repository_the_tree_should_be_walked(self):
        self.write("node_modules/x.js", "// TODO walked\n")
        self.write("a.js", "// TODO a\n")
        file_path = os.path.join(self.tmp, "a.js")

        with patch("todonotifier.git_meta.find_git_root", return_value=None):
            result = scan(ScanSettings(paths=[self.tmp, file_path], extensions=["js"], respect_gitignore=True, exclude_dirs={"NAME": []}), today=TODAY)

        self.assertEqual(["a.js", "node_modules/x.js"], [item.file for item in result.items])

    def test_if_git_is_unavailable_the_tree_should_be_walked(self):
        self.write("a.js", "// TODO a\n")

        with patch("todonotifier.git_meta.subprocess.run", side_effect=FileNotFoundError):
            result = scan(ScanSettings(paths=[self.tmp], extensions=["js"], respect_gitignore=True), today=TODAY)

        self.assertEqual(["a.js"], [item.file for item in result.items])
