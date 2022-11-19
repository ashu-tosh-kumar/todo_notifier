import unittest
from unittest.mock import patch

from todonotifier.config import BaseConfig, DefaultConfig, default_config
from todonotifier.constants import DEFAULT_EXCLUDE_DIRS, DEFAULT_EXCLUDE_FILES


class TestBaseConfig(unittest.TestCase):
    def setUp(self) -> None:
        self._dummy_exclude_dirs = {"unittest-key1": "unittest-val1"}
        self._dummy_exclude_files = {"unittest-key2": "unittest-val2"}
        self._dummy_summary_generators = ["unittest-item"]
        self._dummy_generate_html = True
        self._dummy_save_html_reports = True
        self._dummy_ignore_todo_case = False
        self._dummy_notifier = None

        self._base_config = BaseConfig(
            self._dummy_exclude_dirs,
            self._dummy_exclude_files,
            self._dummy_summary_generators,
            self._dummy_generate_html,
            self._dummy_save_html_reports,
            self._dummy_ignore_todo_case,
            self._dummy_notifier,
        )

    def test_exclude_dirs_should_return_excluded_directory(self):
        expected_value = self._dummy_exclude_dirs

        actual_value = self._base_config.exclude_dirs

        self.assertEqual(expected_value, actual_value)

    def test_exclude_files_should_return_excluded_files(self):
        expected_value = self._dummy_exclude_files

        actual_value = self._base_config.exclude_files

        self.assertEqual(expected_value, actual_value)

    def test_summary_generators_should_return_summary_generators(self):
        expected_value = self._dummy_summary_generators

        actual_value = self._base_config.summary_generators

        self.assertEqual(expected_value, actual_value)

    def test_generate_html_should_return_generate_html(self):
        expected_value = self._dummy_generate_html

        actual_value = self._base_config.generate_html

        self.assertEqual(expected_value, actual_value)

    def test_save_html_reports_should_return_save_html_reports(self):
        expected_value = self._dummy_save_html_reports

        actual_value = self._base_config.save_html_reports

        self.assertEqual(expected_value, actual_value)

    def test_ignore_todo_case_should_return_ignore_todo_case(self):
        expected_value = self._dummy_ignore_todo_case

        actual_value = self._base_config.ignore_todo_case

        self.assertEqual(expected_value, actual_value)

    def test_notifier_should_return_notifier(self):
        expected_value = self._dummy_notifier

        actual_value = self._base_config.notifier

        self.assertEqual(expected_value, actual_value)


class TestDefaultConfig(unittest.TestCase):
    def setUp(self):
        self._default_config = DefaultConfig()

    def test_default_config_should_return_default_exclude_dirs(self):
        expected_value = DEFAULT_EXCLUDE_DIRS

        actual_value = self._default_config.exclude_dirs

        self.assertEqual(expected_value, actual_value)

    def test_default_config_should_not_add_default_dirs_if_flag_is_false(self):
        dummy_exclude_dirs = ["unittest-exclude-dir"]

        default_config = DefaultConfig(exclude_dirs=dummy_exclude_dirs, flag_default_exclude_dirs=False)
        actual_value = default_config.exclude_dirs

        self.assertEqual(dummy_exclude_dirs, actual_value)

    def test_default_config_should_return_default_exclude_files(self):
        expected_value = DEFAULT_EXCLUDE_FILES

        actual_value = self._default_config.exclude_files

        self.assertEqual(expected_value, actual_value)

    def test_default_config_should_not_add_default_files_if_flag_is_false(self):
        dummy_exclude_files = ["unittest-exclude-file"]

        default_config = DefaultConfig(exclude_files=dummy_exclude_files, flag_default_exclude_files=False)
        actual_value = default_config.exclude_files

        self.assertEqual(dummy_exclude_files, actual_value)

    @patch("todonotifier.config.UpcomingWeekTodosByUserSummaryGenerator")
    @patch("todonotifier.config.ExpiredTodosByUserSummaryGenerator")
    @patch("todonotifier.config.ByModuleSummaryGenerator")
    def test_default_config_should_return_default_summary_generators(
        self, stub_by_module_summary_generator, stub_expired_todos_by_user_summary_generator, stub_upcoming_week_todos_by_user_summary_generator
    ):
        expected_value = [
            stub_by_module_summary_generator(),
            stub_expired_todos_by_user_summary_generator(),
            stub_upcoming_week_todos_by_user_summary_generator(),
        ]

        default_config = DefaultConfig()
        actual_value = default_config.summary_generators

        self.assertEqual(expected_value, actual_value)

    def test_default_config_should_not_add_default_summary_generators_if_flag_is_false(self):
        dummy_summary_generators = ["unittest-exclude-file"]

        default_config = DefaultConfig(summary_generators=dummy_summary_generators, flag_default_summary_generators=False)
        actual_value = default_config.summary_generators

        self.assertEqual(dummy_summary_generators, actual_value)


class TestDefaultConfigInstance(unittest.TestCase):
    def test_default_config_instance_should_exist(self):
        self.assertIsInstance(default_config, DefaultConfig)


if __name__ == "__main__":
    unittest.main()
