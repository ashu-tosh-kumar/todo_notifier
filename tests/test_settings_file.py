import os
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

from todonotifier import settings_file
from todonotifier.constants import DEFAULT_EXCLUDE_DIRS
from todonotifier.languages import COMMON_EXTENSIONS
from todonotifier.settings import ScanSettings
from todonotifier.settings_file import (
    CLI_DEFAULTS,
    SETTING_KEYS,
    ConfigError,
    ProjectConfig,
    find_config_file,
    load_config,
    resolve_project_config,
    resolve_settings,
)


class ConfigTestCase(unittest.TestCase):
    """Creates a temporary git repository root per test, so discovery never leaves the temp dir"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = str(Path(self._tmp.name).resolve())
        os.mkdir(os.path.join(self.root, ".git"))

    def write(self, relative_path, content):
        path = os.path.join(self.root, relative_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            file.write(textwrap.dedent(content))
        return path

    def pyproject(self, body, directory=""):
        return self.write(os.path.join(directory, "pyproject.toml"), "[tool.todonotifier]\n" + textwrap.dedent(body))

    def dotfile(self, body, directory=""):
        return self.write(os.path.join(directory, ".todonotifier.toml"), body)


class TestPrecedence(ConfigTestCase):
    def test_cli_defaults_should_have_the_agreed_values(self):
        self.assertEqual(
            {
                "default_due_days": 90,
                "extensions": "common",
                "tags": ["TODO", "FIXME", "HACK", "XXX"],
                "respect_gitignore": True,
                "use_git_blame": True,
            },
            CLI_DEFAULTS,
        )

    def test_defaults_only_should_use_cli_defaults_then_scan_settings_defaults(self):
        settings = resolve_settings({}, start=self.root)

        self.assertEqual(90, settings.default_due_days)
        self.assertEqual(COMMON_EXTENSIONS, settings.extensions)
        self.assertEqual(["TODO", "FIXME", "HACK", "XXX"], settings.tags)
        self.assertTrue(settings.respect_gitignore)
        self.assertTrue(settings.use_git_blame)
        # Not part of CLI_DEFAULTS: the ScanSettings defaults apply
        self.assertEqual(["."], settings.paths)
        self.assertFalse(settings.ignore_case)
        self.assertFalse(settings.require_comment)
        self.assertEqual(DEFAULT_EXCLUDE_DIRS, settings.exclude_dirs)
        self.assertIsNone(settings.repo_web_url)
        self.assertEqual({}, settings.author_aliases)

    def test_library_defaults_should_not_change(self):
        ScanSettings().tags.append("x")  # must not leak into the CLI defaults

        self.assertEqual(["TODO"], ScanSettings().tags)
        self.assertEqual(["py"], ScanSettings().extensions)
        self.assertEqual(["TODO", "FIXME", "HACK", "XXX"], CLI_DEFAULTS["tags"])

    def test_file_only_should_override_cli_defaults(self):
        self.pyproject("""
            tags = ["TODO"]
            extensions = ["py", ".js"]
            use_git_blame = false
            default_due_days = 30
            ignore_case = true
            """)

        settings = resolve_settings({}, start=self.root)

        self.assertEqual(["TODO"], settings.tags)
        self.assertEqual(["py", "js"], settings.extensions)
        self.assertFalse(settings.use_git_blame)
        self.assertEqual(30, settings.default_due_days)
        self.assertTrue(settings.ignore_case)
        self.assertTrue(settings.respect_gitignore)  # untouched CLI default

    def test_cli_only_should_override_cli_defaults(self):
        settings = resolve_settings({"tags": ["FIXME"], "extensions": "py", "use_git_blame": False, "paths": ["src"]}, start=self.root)

        self.assertEqual(["FIXME"], settings.tags)
        self.assertEqual(["py"], settings.extensions)
        self.assertFalse(settings.use_git_blame)
        self.assertEqual(["src"], settings.paths)

    def test_file_plus_cli_should_prefer_cli(self):
        self.pyproject("""
            tags = ["TODO", "HACK"]
            extensions = "common"
            default_due_days = 30
            """)

        settings = resolve_settings({"tags": ["XXX"], "default_due_days": 7}, start=self.root)

        self.assertEqual(["XXX"], settings.tags)
        self.assertEqual(7, settings.default_due_days)
        self.assertEqual(COMMON_EXTENSIONS, settings.extensions)  # from the file, not overridden

    def test_none_override_should_count_as_not_given(self):
        self.pyproject('tags = ["HACK"]')

        settings = resolve_settings({"tags": None, "extensions": None, "fail_on": None}, start=self.root)

        self.assertEqual(["HACK"], settings.tags)
        self.assertEqual(COMMON_EXTENSIONS, settings.extensions)

    def test_false_override_should_not_count_as_not_given(self):
        self.pyproject("respect_gitignore = true")

        self.assertFalse(resolve_settings({"respect_gitignore": False}, start=self.root).respect_gitignore)

    def test_zero_default_due_days_should_turn_default_due_dates_off(self):
        self.assertIsNone(resolve_settings({"default_due_days": 0}, start=self.root).default_due_days)

    def test_fail_on_should_follow_the_same_precedence(self):
        self.assertEqual("none", resolve_project_config({}, start=self.root).fail_on)
        self.pyproject('fail_on = "stale"')
        self.assertEqual("stale", resolve_project_config({}, start=self.root).fail_on)
        self.assertEqual("any", resolve_project_config({"fail_on": "any"}, start=self.root).fail_on)
        self.assertEqual("stale", resolve_project_config({"fail_on": None}, start=self.root).fail_on)

    def test_resolve_settings_should_match_resolve_project_config(self):
        self.pyproject('tags = ["HACK"]')

        self.assertEqual(resolve_project_config({"ignore_case": True}, start=self.root).settings, resolve_settings({"ignore_case": True}, start=self.root))

    def test_resolve_project_config_should_carry_source_and_notify(self):
        path = self.pyproject("""
            [tool.todonotifier.notify.slack]
            webhook_env = "TODO_SLACK_WEBHOOK"
            """)

        config = resolve_project_config({}, start=self.root)

        self.assertEqual(path, config.source)
        self.assertEqual({"slack": {"enabled": True, "webhook_env": "TODO_SLACK_WEBHOOK"}}, config.notify)

    def test_invalid_cli_override_should_raise(self):
        with self.assertRaisesRegex(ConfigError, r"Unknown key 'tagz' in command line options\. Did you mean 'tags'\?"):
            resolve_settings({"tagz": ["TODO"]}, start=self.root)
        with self.assertRaisesRegex(ConfigError, "'tags' in command line options must be a list"):
            resolve_settings({"tags": "TODO"}, start=self.root)
        with self.assertRaisesRegex(ConfigError, "'fail_on' in command line options must be one of"):
            resolve_project_config({"fail_on": "sometimes"}, start=self.root)

    def test_cli_overrides_should_not_accept_tables(self):
        with self.assertRaisesRegex(ConfigError, "Unknown key 'notify'"):
            resolve_settings({"notify": {}}, start=self.root)

    def test_cli_exclusions_should_be_added_to_file_and_defaults(self):
        self.pyproject('exclude_dirs = { name = ["from_file"] }')

        settings = resolve_settings({"exclude_dirs": {"name": ["from_cli"]}}, start=self.root)

        self.assertEqual(DEFAULT_EXCLUDE_DIRS["NAME"] + ["from_file", "from_cli"], settings.exclude_dirs["NAME"])

    def test_every_scan_setting_but_author_aliases_should_be_a_config_key(self):
        from dataclasses import fields

        self.assertEqual({f.name for f in fields(ScanSettings)} - {"author_aliases"}, set(SETTING_KEYS))


class TestDiscovery(ConfigTestCase):
    def test_nearest_file_should_win(self):
        self.pyproject('tags = ["ROOT"]')
        nearest = self.dotfile('tags = ["NEAR"]', "pkg/sub")
        os.makedirs(os.path.join(self.root, "pkg/sub/deeper"))

        self.assertEqual(nearest, find_config_file(os.path.join(self.root, "pkg/sub/deeper")))
        self.assertEqual(["NEAR"], load_config(start=os.path.join(self.root, "pkg/sub/deeper")).settings.tags)

    def test_walk_should_go_up_to_a_parent_file(self):
        path = self.dotfile('tags = ["ROOT"]')
        os.makedirs(os.path.join(self.root, "a/b"))

        self.assertEqual(path, find_config_file(os.path.join(self.root, "a/b")))

    def test_dot_file_should_beat_pyproject_in_the_same_directory(self):
        self.pyproject('tags = ["PYPROJECT"]')
        dotfile = self.dotfile('tags = ["DOT"]')

        self.assertEqual(dotfile, find_config_file(self.root))

    def test_pyproject_without_the_table_should_be_skipped(self):
        self.write("pkg/pyproject.toml", '[tool.black]\nline-length = 100\n[tool.poetry]\nname = "x"\n')
        self.write("pkg/other/pyproject.toml", '[project]\nname = "x"\n')
        parent = self.dotfile('tags = ["PARENT"]')

        self.assertEqual(parent, find_config_file(os.path.join(self.root, "pkg/other")))

    def test_pyproject_with_the_table_should_be_found(self):
        path = self.pyproject('tags = ["X"]', "pkg")

        self.assertEqual(path, find_config_file(os.path.join(self.root, "pkg")))

    def test_start_may_be_a_file(self):
        path = self.pyproject('tags = ["X"]', "pkg")
        source_file = self.write("pkg/mod.py", "# TODO x\n")

        self.assertEqual(path, find_config_file(source_file))

    def test_start_may_be_a_path_that_does_not_exist(self):
        path = self.pyproject('tags = ["X"]', "pkg")

        self.assertEqual(path, find_config_file(os.path.join(self.root, "pkg", "missing", "file.py")))

    def test_search_should_stop_at_the_git_root(self):
        # A config above the git root must be ignored
        project = os.path.join(self.root, "project")
        os.makedirs(os.path.join(project, ".git"))
        os.makedirs(os.path.join(project, "src"))
        self.dotfile('tags = ["ABOVE"]')  # in self.root, above the nested git root

        self.assertIsNone(find_config_file(os.path.join(project, "src")))

    def test_git_root_itself_should_be_searched(self):
        path = self.dotfile('tags = ["AT_ROOT"]')
        os.makedirs(os.path.join(self.root, "src"))

        self.assertEqual(path, find_config_file(os.path.join(self.root, "src")))

    def test_git_file_should_count_as_git_root(self):
        project = os.path.join(self.root, "worktree")
        os.makedirs(os.path.join(project, "src"))
        with open(os.path.join(project, ".git"), "w", encoding="utf-8") as file:
            file.write("gitdir: ../elsewhere\n")
        self.dotfile('tags = ["ABOVE"]')

        self.assertIsNone(find_config_file(os.path.join(project, "src")))

    def test_search_should_stop_at_the_filesystem_root(self):
        with mock.patch("os.path.exists", return_value=False), mock.patch("os.path.isfile", return_value=False), mock.patch("os.path.isdir", return_value=True):
            self.assertIsNone(find_config_file(os.path.join(os.sep, "a", "b")))

    def test_no_file_should_give_defaults_and_no_error(self):
        config = load_config(start=self.root)

        self.assertIsNone(config.source)
        self.assertEqual("none", config.fail_on)
        self.assertEqual({}, config.notify)
        self.assertEqual(resolve_settings({}, start=self.root), config.settings)
        self.assertEqual(90, config.settings.default_due_days)

    def test_explicit_path_should_beat_discovery(self):
        self.dotfile('tags = ["DISCOVERED"]')
        explicit = self.write("ci/todo.toml", 'tags = ["EXPLICIT"]\n')

        config = load_config(explicit, start=self.root)

        self.assertEqual(["EXPLICIT"], config.settings.tags)
        self.assertEqual(explicit, config.source)

    def test_explicit_pyproject_should_use_the_tool_table(self):
        path = self.pyproject('tags = ["EXPLICIT"]', "ci")

        self.assertEqual(["EXPLICIT"], load_config(path).settings.tags)

    def test_explicit_relative_path_should_work(self):
        self.dotfile('tags = ["REL"]')
        cwd = os.getcwd()
        self.addCleanup(os.chdir, cwd)
        os.chdir(self.root)

        config = load_config(".todonotifier.toml")

        self.assertEqual(["REL"], config.settings.tags)
        self.assertEqual(os.path.join(self.root, ".todonotifier.toml"), config.source)

    def test_missing_explicit_path_should_be_an_error(self):
        with self.assertRaisesRegex(ConfigError, "Config file not found: .*nope.toml"):
            load_config(os.path.join(self.root, "nope.toml"), start=self.root)
        with self.assertRaises(ConfigError):
            resolve_settings({}, config_path=os.path.join(self.root, "nope.toml"), start=self.root)

    def test_explicit_pyproject_without_the_table_should_be_an_error(self):
        path = self.write("pyproject.toml", '[project]\nname = "x"\n')

        with self.assertRaisesRegex(ConfigError, r"has no \[tool.todonotifier\] table"):
            load_config(path)

    def test_todonotifier_entry_that_is_not_a_table_should_be_an_error(self):
        self.write("pyproject.toml", "[tool]\ntodonotifier = 1\n")

        with self.assertRaisesRegex(ConfigError, r"\[tool.todonotifier\] in .*pyproject.toml must be a table"):
            find_config_file(self.root)

    def test_tool_that_is_not_a_table_should_be_skipped(self):
        self.write("pyproject.toml", "tool = 1\n")

        self.assertIsNone(find_config_file(self.root))


class TestErrors(ConfigTestCase):
    def test_unknown_key_should_suggest_the_closest_key(self):
        self.pyproject('tagz = ["TODO"]')

        with self.assertRaises(ConfigError) as caught:
            resolve_settings({}, start=self.root)

        self.assertEqual("Unknown key 'tagz' in pyproject.toml [tool.todonotifier]. Did you mean 'tags'?", str(caught.exception))

    def test_unknown_key_in_dot_file_should_name_the_file(self):
        self.dotfile("colour = 1")

        with self.assertRaises(ConfigError) as caught:
            load_config(start=self.root)

        self.assertEqual("Unknown key 'colour' in .todonotifier.toml.", str(caught.exception))

    def test_wrong_types_should_name_the_key_and_the_file(self):
        cases = {
            'tags = "TODO"': r"Key 'tags' in pyproject.toml \[tool.todonotifier\] must be a list of non-empty strings, got str",
            "tags = [1]": "'tags' in .* must be a list of non-empty strings, got list",
            "tags = []": "'tags' in .* must not be an empty list",
            'paths = ""': "'paths' in .* must be a list",
            "extensions = 3": "'extensions' in .* must be a string or a list of strings, got int",
            'extensions = ""': "'extensions' in .* must be a string or a list of strings, got str",
            'ignore_case = "yes"': "'ignore_case' in .* must be true or false, got str",
            "use_git_blame = 1": "'use_git_blame' in .* must be true or false, got int",
            'default_due_days = "90"': "'default_due_days' in .* must be an integer, got str",
            "default_due_days = true": "'default_due_days' in .* must be an integer, got bool",
            "default_due_days = -1": "'default_due_days' in .* must be at least 0, got -1",
            "repo_web_url = 5": "'repo_web_url' in .* must be a non-empty string, got int",
            'commit_sha = " "': "'commit_sha' in .* must be a non-empty string, got str",
            'exclude_dirs = ["a"]': "'exclude_dirs' in .* must be a table",
            "exclude_dirs = { name = 1 }": "'name' of 'exclude_dirs' in .* must be a list",
            'fail_on = "sometimes"': r"'fail_on' in .* must be one of none, expired, stale, any, got 'sometimes'",
            "fail_on = 1": "'fail_on' in .* must be one of",
        }
        for body, pattern in cases.items():
            with self.subTest(body=body):
                self.pyproject(body)
                with self.assertRaisesRegex(ConfigError, pattern):
                    load_config(start=self.root)

    def test_invalid_toml_should_name_the_file_and_the_parser_message(self):
        path = self.dotfile("tags = [\n")

        with self.assertRaises(ConfigError) as caught:
            load_config(start=self.root)

        self.assertIn(f"Invalid TOML in {path}:", str(caught.exception))
        self.assertGreater(len(str(caught.exception)), len(f"Invalid TOML in {path}: "))

    def test_invalid_toml_in_pyproject_should_be_an_error_during_discovery(self):
        self.write("pyproject.toml", "[tool.todonotifier\n")

        with self.assertRaisesRegex(ConfigError, "Invalid TOML in .*pyproject.toml"):
            find_config_file(self.root)

    def test_file_that_is_not_utf8_should_be_an_error(self):
        path = os.path.join(self.root, ".todonotifier.toml")
        with open(path, "wb") as file:
            file.write(b'tags = ["\xff"]\n')

        with self.assertRaisesRegex(ConfigError, "Invalid TOML in"):
            load_config(start=self.root)

    def test_unreadable_file_should_be_an_error(self):
        path = self.dotfile("tags = []")

        with mock.patch("builtins.open", side_effect=PermissionError(13, "Permission denied")):
            with self.assertRaisesRegex(ConfigError, f"Cannot read config file {path}: Permission denied"):
                load_config(start=self.root)

    def test_exclusions_should_be_validated(self):
        self.pyproject('exclude_files = { nme = ["a"] }')
        with self.assertRaisesRegex(ConfigError, r"Unknown entry 'nme' in key 'exclude_files' in .*Did you mean 'name'\?"):
            load_config(start=self.root)

        self.pyproject('exclude_files = { pattern = ["("] }')
        with self.assertRaisesRegex(ConfigError, "Invalid regular expression '\\(' in 'pattern' of 'exclude_files'"):
            load_config(start=self.root)

    def test_unknown_key_without_a_close_match_should_not_suggest(self):
        self.pyproject("zzzzzz = 1")

        with self.assertRaises(ConfigError) as caught:
            load_config(start=self.root)

        self.assertNotIn("Did you mean", str(caught.exception))


class TestValues(ConfigTestCase):
    def test_extensions_should_expand_common_and_strip_dots(self):
        self.pyproject('extensions = ["common", ".proto", "py"]')

        self.assertEqual(COMMON_EXTENSIONS + ["proto"], load_config(start=self.root).settings.extensions)

    def test_extensions_string_should_be_accepted(self):
        self.pyproject('extensions = "py"')

        self.assertEqual(["py"], load_config(start=self.root).settings.extensions)

    def test_all_keys_should_be_accepted_together(self):
        self.pyproject("""
            paths = ["src"]
            extensions = ["py"]
            tags = ["TODO"]
            ignore_case = true
            require_comment = true
            use_git_blame = false
            default_due_days = 14
            respect_gitignore = false
            repo_web_url = "https://github.com/org/repo"
            commit_sha = "abc123"
            fail_on = "expired"
            exclude_dirs = { NAME = ["generated"], pattern = ['.*_gen'], abs_path = ["/tmp/x"] }
            exclude_files = { name = ["a.py"] }
            """)

        config = load_config(start=self.root)

        self.assertEqual("expired", config.fail_on)
        self.assertEqual([os.path.join(self.root, "src")], config.settings.paths)
        self.assertTrue(config.settings.ignore_case)
        self.assertTrue(config.settings.require_comment)
        self.assertFalse(config.settings.use_git_blame)
        self.assertEqual(14, config.settings.default_due_days)
        self.assertFalse(config.settings.respect_gitignore)
        self.assertEqual("https://github.com/org/repo", config.settings.repo_web_url)
        self.assertEqual("abc123", config.settings.commit_sha)
        self.assertIn("generated", config.settings.exclude_dirs["NAME"])
        self.assertIn("__pycache__", config.settings.exclude_dirs["NAME"])  # defaults are kept
        self.assertIn(".*_gen", config.settings.exclude_dirs["PATTERN"])
        self.assertEqual(["/tmp/x"], config.settings.exclude_dirs["ABS_PATH"])
        self.assertIn("a.py", config.settings.exclude_files["NAME"])

    def test_exclusions_should_not_mutate_library_defaults_or_duplicate(self):
        self.pyproject('exclude_dirs = { name = ["__pycache__", "extra", "extra"] }')

        names = load_config(start=self.root).settings.exclude_dirs["NAME"]

        self.assertEqual(1, names.count("__pycache__"))
        self.assertNotIn("extra", DEFAULT_EXCLUDE_DIRS["NAME"])

    def test_exclusion_section_missing_from_defaults_should_be_created(self):
        self.pyproject('exclude_files = { abs_path = ["/a"] }')

        self.assertEqual(["/a"], load_config(start=self.root).settings.exclude_files["ABS_PATH"])

    def test_dot_file_should_use_top_level_keys(self):
        self.dotfile("""
            tags = ["TODO"]
            fail_on = "any"

            [authors]
            "a@x.com" = "ashu"

            [notify.slack]
            webhook_env = "HOOK"
            """)

        config = load_config(start=self.root)

        self.assertEqual(["TODO"], config.settings.tags)
        self.assertEqual("any", config.fail_on)
        self.assertEqual({"a@x.com": "ashu"}, config.settings.author_aliases)
        self.assertEqual({"slack": {"enabled": True, "webhook_env": "HOOK"}}, config.notify)

    def test_project_config_defaults(self):
        config = ProjectConfig()

        self.assertEqual(ScanSettings(), config.settings)
        self.assertEqual("none", config.fail_on)
        self.assertEqual({}, config.notify)
        self.assertIsNone(config.source)


class TestPaths(ConfigTestCase):
    def test_file_paths_should_be_relative_to_the_config_file_not_the_cwd(self):
        self.pyproject('paths = ["src", "../sibling/file.py", "./tests"]', "project")
        elsewhere = tempfile.TemporaryDirectory()
        self.addCleanup(elsewhere.cleanup)
        cwd = os.getcwd()
        self.addCleanup(os.chdir, cwd)
        os.chdir(elsewhere.name)

        settings = resolve_settings({}, start=os.path.join(self.root, "project"))

        self.assertEqual(
            [
                os.path.join(self.root, "project", "src"),
                os.path.join(self.root, "sibling", "file.py"),
                os.path.join(self.root, "project", "tests"),
            ],
            settings.paths,
        )

    def test_absolute_file_paths_should_be_kept(self):
        absolute = os.path.join(self.root, "abs")
        self.pyproject(f'paths = ["{absolute}"]')

        self.assertEqual([absolute], load_config(start=self.root).settings.paths)

    def test_cli_paths_should_be_left_as_given(self):
        self.pyproject('paths = ["src"]')

        self.assertEqual(["rel/dir", "other.py"], resolve_settings({"paths": ["rel/dir", "other.py"]}, start=self.root).paths)

    def test_dot_file_paths_should_resolve_against_its_directory(self):
        self.dotfile('paths = ["code"]', "sub")

        settings = load_config(start=os.path.join(self.root, "sub")).settings

        self.assertEqual([os.path.join(self.root, "sub", "code")], settings.paths)


class TestAuthors(ConfigTestCase):
    def test_authors_should_fill_author_aliases_with_lowercased_emails(self):
        self.pyproject("""
            [tool.todonotifier.authors]
            "A@X.com" = "ashu"
            "b@x.com" = "bee"
            """)

        self.assertEqual({"a@x.com": "ashu", "b@x.com": "bee"}, load_config(start=self.root).settings.author_aliases)

    def test_authors_must_be_a_table(self):
        self.pyproject('authors = ["a@x.com"]')
        with self.assertRaisesRegex(ConfigError, "'authors' in pyproject.toml .* must be a table"):
            load_config(start=self.root)

    def test_authors_values_must_be_strings(self):
        self.pyproject('authors = { "a@x.com" = 1 }')
        with self.assertRaisesRegex(ConfigError, "Entry 'a@x.com' of 'authors' in .* must map to a non-empty string handle, got int"):
            load_config(start=self.root)

        self.pyproject('authors = { "a@x.com" = "" }')
        with self.assertRaisesRegex(ConfigError, "must map to a non-empty string handle"):
            load_config(start=self.root)

    def test_authors_keys_must_not_be_blank(self):
        self.pyproject('authors = { " " = "x" }')
        with self.assertRaisesRegex(ConfigError, "need a non-empty email"):
            load_config(start=self.root)


class TestNotify(ConfigTestCase):
    def load(self, body):
        self.pyproject(body)
        return load_config(start=self.root)

    def test_all_notifiers_should_be_accepted(self):
        config = self.load("""
            [tool.todonotifier.notify.slack]
            webhook_env = "TODO_SLACK_WEBHOOK"
            max_items = 20

            [tool.todonotifier.notify.teams]
            webhook_env = "TODO_TEAMS_WEBHOOK"
            enabled = false

            [tool.todonotifier.notify.webhook]
            url_env = "TODO_WEBHOOK_URL"
            headers_env = "TODO_WEBHOOK_HEADERS"

            [tool.todonotifier.notify.email]
            smtp_host = "smtp.example.com"
            smtp_port = 587
            sender = "todo@example.com"
            recipients = ["a@example.com", "b@example.com"]
            username_env = "TODO_SMTP_USER"
            password_env = "TODO_SMTP_PASSWORD"
            starttls = true
            """)

        self.assertEqual(
            {
                "slack": {"enabled": True, "webhook_env": "TODO_SLACK_WEBHOOK", "max_items": 20},
                "teams": {"enabled": False, "webhook_env": "TODO_TEAMS_WEBHOOK"},
                "webhook": {"enabled": True, "url_env": "TODO_WEBHOOK_URL", "headers_env": "TODO_WEBHOOK_HEADERS"},
                "email": {
                    "enabled": True,
                    "smtp_host": "smtp.example.com",
                    "smtp_port": 587,
                    "sender": "todo@example.com",
                    "recipients": ["a@example.com", "b@example.com"],
                    "username_env": "TODO_SMTP_USER",
                    "password_env": "TODO_SMTP_PASSWORD",
                    "starttls": True,
                },
            },
            config.notify,
        )

    def test_notify_should_not_read_environment_variables(self):
        with mock.patch.dict(os.environ, {"TODO_SLACK_WEBHOOK": "https://hooks.slack.test/secret"}):
            config = self.load('[tool.todonotifier.notify.slack]\nwebhook_env = "TODO_SLACK_WEBHOOK"\n')

        self.assertNotIn("secret", repr(config))

    def test_unknown_notifier_should_suggest(self):
        with self.assertRaisesRegex(
            ConfigError, r"Unknown notifier 'slak' in pyproject.toml \[tool.todonotifier.notify\]\. Supported notifiers: .*Did you mean 'slack'\?"
        ):
            self.load('[tool.todonotifier.notify.slak]\nwebhook_env = "X"\n')

    def test_notify_must_be_a_table_of_tables(self):
        with self.assertRaisesRegex(ConfigError, "'notify' in pyproject.toml .* must be a table of notifiers, got str"):
            self.load('notify = "slack"')
        with self.assertRaisesRegex(ConfigError, r"'slack' in pyproject.toml \[tool.todonotifier.notify\] must be a table, got str"):
            self.load('[tool.todonotifier.notify]\nslack = "x"\n')

    def test_unknown_notifier_key_should_suggest(self):
        with self.assertRaisesRegex(
            ConfigError,
            r"Unknown key 'max_item' in pyproject.toml \[tool.todonotifier.notify.slack\]\. Allowed keys: enabled, webhook_env, max_items\."
            r" Did you mean 'max_items'\?",
        ):
            self.load('[tool.todonotifier.notify.slack]\nwebhook_env = "X"\nmax_item = 3\n')

    def test_unknown_notifier_key_without_a_close_match_should_not_suggest(self):
        with self.assertRaises(ConfigError) as caught:
            self.load('[tool.todonotifier.notify.slack]\nwebhook_env = "X"\nzzzzz = 3\n')

        self.assertNotIn("Did you mean", str(caught.exception))

    def test_literal_secrets_should_be_rejected_without_echoing_them(self):
        secret = "https://hooks.slack.test/T000/B000/XXXXSECRET"
        cases = [
            ("slack", f'webhook = "{secret}"', "use 'webhook_env'"),
            ("slack", f'webhook_url = "{secret}"', "use 'webhook_env'"),
            ("teams", f'webhook = "{secret}"', "use 'webhook_env'"),
            ("webhook", f'url = "{secret}"', "use 'url_env'"),
            ("webhook", f'headers = "{secret}"', "use 'headers_env'"),
            ("email", f'password = "{secret}"\nsmtp_host = "h"', "use 'password_env'"),
            ("email", f'smtp_password = "{secret}"', "use 'password_env'"),
            ("slack", f'token = "{secret}"', "use a key ending in '_env'"),
        ]
        for name, body, hint in cases:
            with self.subTest(body=body.splitlines()[0]):
                with self.assertRaises(ConfigError) as caught:
                    self.load(f"[tool.todonotifier.notify.{name}]\n{body}\n")

                message = str(caught.exception)
                self.assertIn("looks like a literal secret", message)
                self.assertIn(hint, message)
                self.assertNotIn("SECRET", message)

    def test_env_keys_must_be_variable_names_and_never_echo_the_value(self):
        for value in ['"https://hooks.slack.test/XXXXSECRET"', '"has space"', "1", '"1ABC"']:
            with self.subTest(value=value):
                with self.assertRaises(ConfigError) as caught:
                    self.load(f"[tool.todonotifier.notify.slack]\nwebhook_env = {value}\n")

                self.assertIn("must be the NAME of an environment variable", str(caught.exception))
                self.assertNotIn("SECRET", str(caught.exception))

    def test_required_keys_should_be_enforced(self):
        with self.assertRaisesRegex(ConfigError, r"Missing required key 'webhook_env' in pyproject.toml \[tool.todonotifier.notify.slack\]"):
            self.load("[tool.todonotifier.notify.slack]\nmax_items = 3\n")
        with self.assertRaisesRegex(ConfigError, "Missing required key 'url_env' in"):
            self.load("[tool.todonotifier.notify.webhook]\nenabled = true\n")

        base = 'smtp_host = "h"\nsender = "s@x.com"\nrecipients = ["r@x.com"]\npassword_env = "PW"\n'
        for missing in ("smtp_host", "sender", "recipients", "password_env"):
            body = "\n".join(line for line in base.splitlines() if not line.startswith(missing))
            with self.subTest(missing=missing):
                with self.assertRaisesRegex(ConfigError, f"Missing required key '{missing}'"):
                    self.load(f"[tool.todonotifier.notify.email]\n{body}\n")

    def test_notifier_value_types_should_be_validated(self):
        base = 'smtp_host = "h"\nsender = "s@x.com"\nrecipients = ["r@x.com"]\npassword_env = "PW"\n'
        cases = {
            "slack": [
                ('webhook_env = "X"\nmax_items = "3"', "'max_items' in .* must be an integer, got str"),
                ('webhook_env = "X"\nmax_items = 0', "must be at least 1"),
                ('webhook_env = "X"\nenabled = "no"', "'enabled' in .* must be true or false"),
            ],
            "email": [
                (base + "smtp_port = 70000", "'smtp_port' in .* must be between 1 and 65535, got 70000"),
                (base + 'smtp_port = "587"', "'smtp_port' in .* must be an integer"),
                (base + 'starttls = "yes"', "'starttls' in .* must be true or false"),
                (base.replace('["r@x.com"]', '"r@x.com"'), "'recipients' in .* must be a list of non-empty strings, got str"),
                (base.replace('["r@x.com"]', "[]"), "'recipients' in .* must not be an empty list"),
                (base.replace('"h"', "1"), "'smtp_host' in .* must be a non-empty string, got int"),
            ],
        }
        for name, items in cases.items():
            for body, pattern in items:
                with self.subTest(name=name, pattern=pattern):
                    with self.assertRaisesRegex(ConfigError, pattern):
                        self.load(f"[tool.todonotifier.notify.{name}]\n{body}\n")


class TestTomlBackend(unittest.TestCase):
    def test_tomllib_or_tomli_should_be_used_for_the_running_python(self):
        import sys

        expected = "tomllib" if sys.version_info >= (3, 11) else "tomli"
        self.assertEqual(expected, settings_file.tomllib.__name__)
