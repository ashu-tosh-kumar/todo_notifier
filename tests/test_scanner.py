import json
import os
import tempfile
import unittest
from datetime import date
from unittest.mock import patch

from todonotifier.results import ScanResult, TodoItem
from todonotifier.scanner import ScanException, scan
from todonotifier.settings import ScanSettings
from todonotifier.todo_notifier import parse_files_for_todo_items

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_FILES = [os.path.join(TESTS_DIR, "sample_test_file.py"), os.path.join(TESTS_DIR, "sample_test_file2.py")]
TODAY = date(2025, 6, 15)


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

        expected = parse_files_for_todo_items(result.root, SAMPLE_FILES, False)
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
