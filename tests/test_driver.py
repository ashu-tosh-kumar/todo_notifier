import unittest
from unittest.mock import Mock, patch

from tests.mocks import MockSummaryGenerator, MockTestConfig
from todonotifier.driver import TODOException, run


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


if __name__ == "__main__":
    unittest.main()
