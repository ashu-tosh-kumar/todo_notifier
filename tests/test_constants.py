import unittest

from todonotifier.constants import (
    DEFAULT_COMPLETION_DATE,
    DEFAULT_EXCLUDE_DIRS,
    DEFAULT_EXCLUDE_FILES,
    DEFAULT_SUMMARY_GENERATORS_ENUM,
    UNKNOWN_USER_NAME,
)


class TestDefaultExcludeDirs(unittest.TestCase):
    def test_DEFAULT_EXCLUDE_DIRS_should_exist(self):
        self.assertIsNotNone(DEFAULT_EXCLUDE_DIRS)


class TestDefaultExcludeFiles(unittest.TestCase):
    def test_DEFAULT_EXCLUDE_FILES_should_exist(self):
        self.assertIsNotNone(DEFAULT_EXCLUDE_FILES)


class TestUnknownUserName(unittest.TestCase):
    def test_UNKNOWN_USER_NAME_should_exist(self):
        self.assertIsNotNone(UNKNOWN_USER_NAME)


class TestDefaultCompletionDate(unittest.TestCase):
    def test_DEFAULT_COMPLETION_DATE_should_exist(self):
        self.assertIsNotNone(DEFAULT_COMPLETION_DATE)


class TestDefaultSummaryGeneratorsEnum(unittest.TestCase):
    def test_DEFAULT_SUMMARY_GENERATORS_ENUM_should_contain_expected_enums(self):
        self.assertEqual("Expired TODO Items", DEFAULT_SUMMARY_GENERATORS_ENUM.EXPIRED_TODO_BY_USER)
        self.assertEqual("Module-wise Summary", DEFAULT_SUMMARY_GENERATORS_ENUM.TODO_BY_MODULE)
        self.assertEqual(
            "Upcoming Week TODO Items",
            DEFAULT_SUMMARY_GENERATORS_ENUM.UPCOMING_TODO_BY_USER,
        )


if __name__ == "__main__":
    unittest.main()
