import unittest

from config import BaseConfig


class TestBaseConfig(unittest.TestCase):
    def setUp(self) -> None:
        self._dummy_exclude_dirs = {"unittest-key1": "unittest-val1"}
        self._dummy_exclude_files = {"unittest-key2": "unittest-val2"}
        self._dummy_summary_generators = ["unittest-item"]
        self._base_config = BaseConfig(
            self._dummy_exclude_dirs, self._dummy_exclude_files, self._dummy_summary_generators)

    def test_EXCLUDE_DIRS_should_return_excluded_directory(self):
        expected_value = self._dummy_exclude_dirs

        actual_value = self._base_config.EXCLUDE_DIRS

        self.assertEqual(expected_value, actual_value)

    def test_EXCLUDE_FILES_should_return_excluded_files(self):
        expected_value = self._dummy_exclude_files

        actual_value = self._base_config.EXCLUDE_FILES

        self.assertEqual(expected_value, actual_value)

    def test_EXCLUDE_FILES_should_return_summary_generators(self):
        expected_value = self._dummy_summary_generators

        actual_value = self._base_config.SUMMARY_GENERATORS

        self.assertEqual(expected_value, actual_value)


if __name__ == "__main__":
    unittest.main()
