import unittest

from tests.mocks import MockTestConfig
from todonotifier.config import DefaultConfig
from todonotifier.constants import DEFAULT_EXCLUDE_DIRS, DEFAULT_EXCLUDE_FILES
from todonotifier.settings import ScanSettings


class TestScanSettings(unittest.TestCase):
    def test_defaults_should_keep_todays_behavior(self):
        settings = ScanSettings()

        self.assertEqual(["."], settings.paths)
        self.assertEqual(["py"], settings.extensions)
        self.assertEqual(["TODO"], settings.tags)
        self.assertFalse(settings.ignore_case)
        self.assertEqual(DEFAULT_EXCLUDE_DIRS, settings.exclude_dirs)
        self.assertEqual(DEFAULT_EXCLUDE_FILES, settings.exclude_files)
        self.assertFalse(settings.require_comment)
        self.assertFalse(settings.use_git_blame)
        self.assertIsNone(settings.default_due_days)
        self.assertFalse(settings.respect_gitignore)
        self.assertIsNone(settings.repo_web_url)
        self.assertIsNone(settings.commit_sha)
        self.assertEqual({}, settings.author_aliases)

    def test_mutable_defaults_should_not_be_shared_between_instances(self):
        first = ScanSettings()
        second = ScanSettings()

        first.paths.append("src")
        first.extensions.append("js")
        first.tags.append("FIXME")
        first.author_aliases["a@x.com"] = "ashu"
        first.exclude_dirs["NAME"].append("unittest-dir")
        first.exclude_files["NAME"].append("unittest-file")

        self.assertEqual(["."], second.paths)
        self.assertEqual(["py"], second.extensions)
        self.assertEqual(["TODO"], second.tags)
        self.assertEqual({}, second.author_aliases)
        self.assertNotIn("unittest-dir", second.exclude_dirs["NAME"])
        self.assertNotIn("unittest-file", second.exclude_files["NAME"])
        self.assertNotIn("unittest-dir", DEFAULT_EXCLUDE_DIRS["NAME"])
        self.assertNotIn("unittest-file", DEFAULT_EXCLUDE_FILES["NAME"])

    def test_extensions_should_have_leading_dots_stripped(self):
        settings = ScanSettings(extensions=[".py", "js", "..ts"])

        self.assertEqual(["py", "js", "ts"], settings.extensions)


class TestFromConfig(unittest.TestCase):
    def test_from_config_should_copy_the_options_that_exist_on_the_config(self):
        config = MockTestConfig(
            exclude_dirs={"NAME": ["unittest-dir"]},
            exclude_files={"PATTERN": ["unittest-pattern"]},
            ignore_todo_case=True,
            file_extensions=["js", "ts"],
        )

        settings = ScanSettings.from_config(config)

        self.assertEqual(["js", "ts"], settings.extensions)
        self.assertTrue(settings.ignore_case)
        self.assertEqual({"NAME": ["unittest-dir"]}, settings.exclude_dirs)
        self.assertEqual({"PATTERN": ["unittest-pattern"]}, settings.exclude_files)

    def test_from_config_should_keep_defaults_for_options_not_on_the_config(self):
        settings = ScanSettings.from_config(MockTestConfig())

        self.assertEqual(ScanSettings().paths, settings.paths)
        self.assertEqual(["TODO"], settings.tags)
        self.assertIsNone(settings.default_due_days)
        self.assertFalse(settings.use_git_blame)

    def test_from_config_should_not_alias_the_config(self):
        config = DefaultConfig()

        settings = ScanSettings.from_config(config)
        settings.extensions.append("js")
        settings.exclude_dirs["NAME"].append("unittest-dir")

        self.assertEqual(["py"], config.file_extensions)
        self.assertNotIn("unittest-dir", config.exclude_dirs["NAME"])

    def test_from_config_of_default_config_should_match_default_settings(self):
        self.assertEqual(ScanSettings(), ScanSettings.from_config(DefaultConfig()))


if __name__ == "__main__":
    unittest.main()
