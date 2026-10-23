import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from tests.mocks import MockSummaryGenerator, MockTestConfig
from todonotifier.config import DefaultConfig
from todonotifier.connect import Connect, ConnectMethod
from todonotifier.driver import TODOException, run
from todonotifier.summary_generators import BaseSummaryGenerator


class TestTodoException(unittest.TestCase):
    def test_todo_exception_should_exist(self):
        with self.assertRaises(TODOException):
            raise TODOException


class TestRun(unittest.TestCase):
    @patch("todonotifier.driver.generate_summary")
    @patch("todonotifier.driver.parse_files_for_todo_items")
    @patch("todonotifier.driver.get_files_in_dir")
    def test_run_should_generate_summary(self, stub_get_files_in_dir, stub_parse_files_for_todo_items, spy_generate_summary):
        dummy_all_todos_items = {"unittest-module-1": ["unittest-todo-obj-1"]}
        dummy_connect = Mock()
        dummy_connect.project_dir_name = ""
        dummy_config = MockTestConfig()
        stub_get_files_in_dir.return_value = ["unittest-file-1"]
        stub_parse_files_for_todo_items.return_value = dummy_all_todos_items

        run(dummy_connect, dummy_config)

        spy_generate_summary.assert_called_once_with(dummy_all_todos_items, dummy_config.summary_generators, dummy_config.generate_html)

    @patch("todonotifier.driver.store_html")
    @patch("todonotifier.driver.generate_summary", Mock())
    @patch("todonotifier.driver.parse_files_for_todo_items", Mock())
    @patch("todonotifier.driver.get_files_in_dir", Mock())
    def test_run_should_store_summary(self, spy_store_html):
        dummy_connect = Mock()
        dummy_connect.project_dir_name = ""
        dummy_config = MockTestConfig(summary_generators=[MockSummaryGenerator])

        run(dummy_connect, dummy_config)

        spy_store_html.assert_called()

    @patch("todonotifier.driver.store_html", Mock())
    @patch("todonotifier.driver.generate_summary", Mock())
    @patch("todonotifier.driver.parse_files_for_todo_items", Mock())
    @patch("todonotifier.driver.get_files_in_dir", Mock())
    def test_run_should_notify(self):
        dummy_connect = Mock()
        dummy_connect.project_dir_name = ""
        spy_notifier = Mock()
        dummy_config = MockTestConfig(notifier=spy_notifier)

        run(dummy_connect, dummy_config)

        spy_notifier.notify.assert_called()

    def test_run_should_raise_todo_exception_if_any_exception_in_connect(self):
        stub_connect = Mock()
        stub_connect.project_dir_name = ""
        stub_connect.pull_repository.side_effect = Exception("unittest-connect-exception")

        with self.assertRaises(TODOException):
            run(stub_connect, MockTestConfig())

    @patch("todonotifier.driver.get_files_in_dir")
    def test_run_should_raise_todo_exception_if_any_exception_in_get_files_in_dir(self, stub_get_files_in_dir):
        dummy_connect = Mock()
        dummy_connect.project_dir_name = ""
        stub_get_files_in_dir.side_effect = Exception("unittest-connect-exception")

        with self.assertRaises(TODOException):
            run(dummy_connect, MockTestConfig())

    @patch("todonotifier.driver.parse_files_for_todo_items")
    @patch("todonotifier.driver.get_files_in_dir", Mock())
    def test_run_should_raise_todo_exception_if_any_exception_in_parse_files_for_todo_items(self, stub_parse_files_for_todo_items):
        dummy_connect = Mock()
        dummy_connect.project_dir_name = ""
        stub_parse_files_for_todo_items.side_effect = Exception("unittest-connect-exception")

        with self.assertRaises(TODOException):
            run(dummy_connect, MockTestConfig())

    @patch("todonotifier.driver.generate_summary")
    @patch("todonotifier.driver.parse_files_for_todo_items", Mock())
    @patch("todonotifier.driver.get_files_in_dir", Mock())
    def test_run_should_raise_todo_exception_if_any_exception_in_generate_summary(self, stub_generate_summary):
        dummy_connect = Mock()
        dummy_connect.project_dir_name = ""
        stub_generate_summary.side_effect = Exception("unittest-connect-exception")

        with self.assertRaises(TODOException):
            run(dummy_connect, MockTestConfig())


class TestRunInPlaceAndRepeatedRuns(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.project_dir = os.path.join(self._tmp.name, "unittest-project")
        os.makedirs(self.project_dir)
        with open(os.path.join(self.project_dir, "a.py"), "w") as f:
            f.write("# TODO {2000-01-01} @alice fix this\n")

    def _connect(self, method: ConnectMethod = ConnectMethod.LOCAL) -> Connect:
        return Connect(connect_method=method, project_dir_name="unittest-project", url=self.project_dir)

    def test_run_twice_should_not_duplicate_report_rows(self):
        config = DefaultConfig(save_html_reports=False)

        run(self._connect(), config)
        run(self._connect(), config)

        for generator in config.summary_generators:
            for rows in generator.container.values():
                self.assertEqual(1, len(rows), f"{generator.name} duplicated rows: {generator.container}")

    def test_run_should_report_paths_starting_with_project_dir_name(self):
        config = DefaultConfig(save_html_reports=False)

        run(self._connect(), config)

        by_module = config.summary_generators[0].container
        self.assertEqual(["unittest-project/a.py"], list(by_module.keys()))

    def test_run_with_local_should_not_copy_the_project(self):
        config = DefaultConfig(save_html_reports=False)

        with patch("todonotifier.driver.tempfile.TemporaryDirectory") as spy_temp_dir, patch("todonotifier.connect.copytree") as spy_copytree:
            run(self._connect(), config)

        spy_temp_dir.assert_not_called()
        spy_copytree.assert_not_called()

    def test_run_with_local_should_leave_the_source_untouched(self):
        config = DefaultConfig(save_html_reports=False)

        run(self._connect(), config)

        self.assertEqual(["a.py"], os.listdir(self.project_dir))

    def test_run_with_dry_run_dir_should_still_copy_and_report_the_same_paths(self):
        config = DefaultConfig(save_html_reports=False)

        run(self._connect(ConnectMethod.DRY_RUN_DIR), config)

        self.assertEqual(["unittest-project/unittest-project/a.py"], list(config.summary_generators[0].container.keys()))

    def test_run_with_local_should_raise_todo_exception_if_the_directory_is_missing(self):
        connect = Connect(connect_method=ConnectMethod.LOCAL, project_dir_name="unittest-project", url=os.path.join(self._tmp.name, "missing"))

        with self.assertRaises(TODOException):
            run(connect, DefaultConfig(save_html_reports=False))

    def test_run_should_call_reset_on_generators_that_define_it_before_generating(self):
        calls = []

        class RecordingGenerator(BaseSummaryGenerator):
            def reset(self) -> None:
                calls.append("reset")

            def generate_summary(self, all_todos_objs) -> None:
                calls.append("generate_summary")

            def generate_html(self) -> None:
                calls.append("generate_html")

        config = MockTestConfig(summary_generators=[RecordingGenerator(name="unittest", container={})], save_html_reports=False)

        run(self._connect(), config)

        self.assertEqual(["reset", "generate_summary", "generate_html"], calls)


if __name__ == "__main__":
    unittest.main()
