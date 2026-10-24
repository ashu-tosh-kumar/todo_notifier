"""Tests for `scripts/gen_docs_reference.py`, which generates the reference pages of the docs site.

The script lives outside the package, so it is imported by path. `test_the_committed_reference_pages_are_up_to_date` is the local copy of the
`--check` step of CI: change `ScanSettings`, a CLI flag, a notifier key or a language, and it fails until you run `python scripts/gen_docs_reference.py`.
"""

import contextlib
import importlib.util
import io
import os
import tempfile
import unittest
from types import ModuleType
from unittest import mock

from todonotifier import settings_file
from todonotifier.settings import ScanSettings

ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT: str = os.path.join(ROOT, "scripts", "gen_docs_reference.py")


def load_script() -> ModuleType:
    """Imports the generator script by path"""
    spec = importlib.util.spec_from_file_location("gen_docs_reference", SCRIPT)
    assert spec is not None and spec.loader is not None
    module: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen: ModuleType = load_script()


def run_main(argv: list[str], root: str) -> tuple[int, str]:
    """Runs `main` with the repository root at `root` and returns the exit code and what it wrote to stderr"""
    err = io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
        code: int = gen.main(argv, root=root)
    return code, err.getvalue()


class TestCommittedPages(unittest.TestCase):
    def test_the_committed_reference_pages_are_up_to_date(self) -> None:
        code, err = run_main(["--check"], ROOT)

        self.assertEqual(code, 0, f"A generated page is stale. {err}")

    def test_every_generated_file_is_committed(self) -> None:
        for relative in gen.generated_files():
            self.assertTrue(os.path.isfile(os.path.join(ROOT, relative)), relative)


class TestCheckMode(unittest.TestCase):
    def test_write_then_check_passes_and_a_changed_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(run_main([], root)[0], 0)
            self.assertEqual(run_main(["--check"], root), (0, ""))

            path: str = os.path.join(root, gen.CONFIGURATION_PAGE)
            with open(path, "a", encoding="utf-8") as file:
                file.write("a hand edit\n")
            code, err = run_main(["--check"], root)

            self.assertEqual(code, 1)
            self.assertIn(gen.CONFIGURATION_PAGE, err)
            self.assertNotIn(gen.CLI_PAGE, err)
            self.assertIn("python scripts/gen_docs_reference.py", err)

    def test_a_missing_file_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            code, err = run_main(["--check"], root)

            self.assertEqual(code, 1)
            for relative in gen.generated_files():
                self.assertIn(relative, err)

    def test_check_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            run_main(["--check"], root)

            self.assertEqual(os.listdir(root), [])


class TestConfigurationPage(unittest.TestCase):
    def setUp(self) -> None:
        self.page: str = gen.render_configuration()

    def test_every_config_key_is_listed_with_its_type_and_defaults(self) -> None:
        for key in settings_file.SETTING_KEYS:
            self.assertIn(f"| `{key}` |", self.page)

        self.assertIn("| `default_due_days` | `Optional[int]` | `unset` | `90` |", self.page)
        self.assertIn('| `tags` | `list[str]` | `["TODO"]` | `["TODO", "FIXME", "HACK", "XXX"]` |', self.page)

    def test_every_scan_settings_key_of_the_config_file_has_a_description(self) -> None:
        descriptions: dict[str, str] = gen.parse_attribute_docs(ScanSettings.__doc__ or "")

        for key in settings_file.SETTING_KEYS:
            self.assertTrue(descriptions.get(key), key)

    def test_fail_on_choices_and_notifier_keys_are_documented(self) -> None:
        for choice in settings_file.FAIL_ON_CHOICES:
            self.assertIn(f"| `{choice}` |", self.page)
        for name, schema in settings_file._NOTIFIER_SCHEMA.items():
            self.assertIn(f"### `[notify.{name}]`", self.page)
            for key in schema:
                self.assertIn(f"| `{key}` |", self.page)

    def test_a_default_that_is_a_plain_sentence_is_dropped_but_a_remark_stays(self) -> None:
        self.assertEqual(gen._without_default('Tags to look for. Defaults to ["TODO"]. Tags are matched.'), "Tags to look for. Tags are matched.")
        self.assertEqual(gen._without_default("Whether to match. Defaults to False"), "Whether to match.")
        self.assertEqual(
            gen._without_default("Web URL. Defaults to None, in which case it is detected"), "Web URL. Defaults to None, in which case it is detected."
        )


class TestHelpers(unittest.TestCase):
    def test_parse_attribute_docs_joins_continuation_lines(self) -> None:
        doc: str = """Summary

        Attributes:
            first (int): The first
                one, on two lines
            second (str | None): The second
        """

        self.assertEqual(gen.parse_attribute_docs(doc), {"first": "The first one, on two lines", "second": "The second"})

    def test_parse_attribute_docs_stops_at_the_next_section(self) -> None:
        doc: str = """Summary

        Attributes:
            first (int): The first

        Example:
            not an attribute
        """

        self.assertEqual(gen.parse_attribute_docs(doc), {"first": "The first"})

    def test_toml_value(self) -> None:
        self.assertEqual(gen._toml_value(None), "unset")
        self.assertEqual(gen._toml_value(True), "true")
        self.assertEqual(gen._toml_value("common"), '"common"')
        self.assertEqual(gen._toml_value(["a", "b"]), '["a", "b"]')
        self.assertEqual(gen._toml_value(90), "90")

    def test_type_name_is_the_same_on_every_python_version(self) -> None:
        self.assertEqual(gen._type_name(bool), "bool")
        self.assertEqual(gen._type_name(list[str]), "list[str]")
        self.assertEqual(gen._type_name(int | None), "Optional[int]")

    def test_code_and_escape(self) -> None:
        self.assertEqual(gen._code("`"), "`` ` ``")
        self.assertEqual(gen._code("//"), "`//`")
        self.assertEqual(gen._escape("a|b <c>"), "a\\|b &lt;c&gt;")


class TestCliPage(unittest.TestCase):
    def test_commands_flags_and_exit_codes_come_from_the_parser(self) -> None:
        page: str = gen.render_cli()

        for command in ("scan", "report", "notify", "init"):
            self.assertIn(f"## `todonotifier {command}`", page)
        for flag in ("--since", "--fail-on", "--no-blame", "--slack-webhook-env", "--standalone", "--out"):
            self.assertIn(flag, page)
        for code in gen.EXIT_CODE_HELP:
            self.assertIn(f"| `{code}` |", page)
        self.assertIn("{none,expired,stale,any,incomplete}", page)

    def test_a_shared_flag_is_listed_once(self) -> None:
        page: str = gen.render_cli()

        self.assertEqual(page.count("| `--default-due-days N` |"), 1)


class TestLanguagesTable(unittest.TestCase):
    def test_extensions_with_the_same_syntax_share_a_row(self) -> None:
        table: str = gen.render_languages()

        self.assertIn("| `py`, `pyi`, `toml` | `#` |", table)
        self.assertIn("`` ` ``", table)
        self.assertIn("Every extension of the `common` preset has a known comment syntax.", table)

    def test_common_extensions_without_a_comment_syntax_are_named(self) -> None:
        with mock.patch.object(gen.languages, "COMMON_EXTENSIONS", ["py", "zzz"]):
            table: str = gen.render_languages()

        self.assertIn("no known comment syntax, so a tag counts anywhere in them: `zzz`.", table)
