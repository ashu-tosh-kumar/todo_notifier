import unittest
from test.mocks import MockTestConfig

from mock import Mock, patch

from driver import TODOException, run


class TestTodoException(unittest.TestCase):
    def test_todo_exception_should_exist(self):
        with self.assertRaises(TODOException):
            raise TODOException


class TestRun(unittest.TestCase):
    def test_run_should_raise_todo_exception_if_missing_project_dir_name(self):
        dummy_connect_kwargs = {}

        with self.assertRaises(TODOException):
            run(dummy_connect_kwargs, MockTestConfig())

    @patch("driver.generate_summary")
    @patch("driver.parse_files_for_todo_items")
    @patch("driver.get_files_in_dir")
    @patch("driver.Connect", Mock())
    def test_run_should_generate_summary(self, stub_get_files_in_dir, stub_parse_files_for_todo_items, spy_generate_summary):
        dummy_all_todos_items = {"unittest-module-1": ["unittest-todo-obj-1"]}
        dummy_connect_kwargs = {"project_dir_name": "unittest-project-dir-name"}
        dummy_config = MockTestConfig()
        stub_get_files_in_dir.return_value = ["unittest-file-1"]
        stub_parse_files_for_todo_items.return_value = dummy_all_todos_items

        run(dummy_connect_kwargs, dummy_config)

        spy_generate_summary.assert_called_once_with(dummy_all_todos_items, dummy_config.summary_generators)

    @patch("driver.Connect")
    def test_run_should_raise_todo_exception_if_any_exception_in_connect(self, stub_connect):
        dummy_connect_kwargs = {"project_dir_name": "unittest-project-dir-name"}
        stub_connect.side_effect = Exception("unittest-connect-exception")

        with self.assertRaises(TODOException):
            run(dummy_connect_kwargs, MockTestConfig())

    @patch("driver.get_files_in_dir")
    @patch("driver.Connect", Mock())
    def test_run_should_raise_todo_exception_if_any_exception_in_get_files_in_dir(self, stub_get_files_in_dir):
        dummy_connect_kwargs = {"project_dir_name": "unittest-project-dir-name"}
        stub_get_files_in_dir.side_effect = Exception("unittest-connect-exception")

        with self.assertRaises(TODOException):
            run(dummy_connect_kwargs, MockTestConfig())

    @patch("driver.parse_files_for_todo_items")
    @patch("driver.get_files_in_dir", Mock())
    @patch("driver.Connect", Mock())
    def test_run_should_raise_todo_exception_if_any_exception_in_parse_files_for_todo_items(self, stub_parse_files_for_todo_items):
        dummy_connect_kwargs = {"project_dir_name": "unittest-project-dir-name"}
        stub_parse_files_for_todo_items.side_effect = Exception("unittest-connect-exception")

        with self.assertRaises(TODOException):
            run(dummy_connect_kwargs, MockTestConfig())

    @patch("driver.generate_summary")
    @patch("driver.parse_files_for_todo_items", Mock())
    @patch("driver.get_files_in_dir", Mock())
    @patch("driver.Connect", Mock())
    def test_run_should_raise_todo_exception_if_any_exception_in_generate_summary(self, stub_generate_summary):
        dummy_connect_kwargs = {"project_dir_name": "unittest-project-dir-name"}
        stub_generate_summary.side_effect = Exception("unittest-connect-exception")

        with self.assertRaises(TODOException):
            run(dummy_connect_kwargs, MockTestConfig())


if __name__ == "__main__":
    unittest.main()
