import json
import os
import re
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone

from jsonschema import Draft202012Validator

from tests.sample_results import (
    TODAY,
    assert_matches_snapshot,
    make_item,
    make_scan_result,
)
from todonotifier.digest import build_digest, render_markdown
from todonotifier.formatters import (
    FORMATS,
    SCHEMA_PATH,
    TEXT_FORMATS,
    _escape_data,
    _escape_property,
    build_reports,
    describe_due,
    format_result,
    severity,
    write_reports,
)
from todonotifier.results import ScanResult

ANNOTATION_PATTERN = re.compile(r"^::(error|warning|notice) file=[^,:\n]+,line=\d+,title=[^,:\n]+::[^\n]*$")


def _result(*items, scanned=None, root="/work/widgets") -> ScanResult:
    return ScanResult(
        items=list(items),
        scanned_files=scanned if scanned is not None else sorted({item.file for item in items}),
        root=root,
        generated_at=datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc),
    )


def _load_schema() -> dict:
    with open(SCHEMA_PATH, encoding="utf-8") as schema_file:
        return json.load(schema_file)


class TestTable(unittest.TestCase):
    def test_snapshot_without_color(self):
        output = format_result(make_scan_result(), "table", color=False, repo_root="/work/widgets")

        assert_matches_snapshot(self, "table.txt", output)
        self.assertNotIn("\x1b", output)

    def test_snapshot_with_color(self):
        output = format_result(make_scan_result(), "table", color=True, repo_root="/work/widgets")

        assert_matches_snapshot(self, "table_color.txt", output.replace("\x1b", "<ESC>"))

    def test_summary_line_counts_and_uses_singular_for_one_item(self):
        summary = format_result(make_scan_result(), "table").splitlines()[-1]
        single = format_result(_result(make_item("a.py", 1, "m", "alice")), "table").splitlines()[-1]

        self.assertEqual("10 TODOs · 4 overdue · 3 stale · 4 unowned", summary)
        self.assertEqual("1 TODO · 0 overdue · 0 stale · 0 unowned", single)

    def test_columns_should_be_aligned(self):
        lines = format_result(make_scan_result(), "table").splitlines()[:11]
        message_columns = {line.index("Remove") for line in lines if "Remove the legacy" in line}

        header_positions = [lines[0].index(name) for name in ("TAG", "OWNER", "DUE", "MESSAGE")]
        for line in lines[1:]:
            self.assertEqual(" ", line[header_positions[0] - 1])  # Every column starts at the position of its header
            self.assertTrue(line[header_positions[3]] != " ")
        self.assertEqual({header_positions[3]}, message_columns)

    def test_status_comes_from_the_reference_day_not_the_stored_flags(self):
        item = make_item("a.py", 1, "m", "alice", date(2026, 5, 10))  # Not overdue on TODAY

        self.assertIn("2026-05-10 due in 9d", format_result(_result(item), "table"))
        self.assertIn("2026-05-10 overdue 2d", format_result(_result(item), "table", today=date(2026, 5, 12)))

    def test_without_items_a_friendly_line_is_shown(self):
        self.assertEqual("No TODOs found (3 files scanned). Nice and tidy!", format_result(_result(scanned=["a.py", "b.py", "c.py"]), "table"))
        self.assertEqual("No TODOs found (1 file scanned). Nice and tidy!", format_result(_result(scanned=["a.py"]), "table"))

    def test_without_scanned_files_the_hint_points_to_the_extensions(self):
        output = format_result(_result(), "table")

        self.assertIn("No files were scanned", output)
        self.assertIn("--ext", output)

    def test_long_messages_are_truncated_and_one_line(self):
        item = make_item("a.py", 1, "word " * 50 + "\tend")

        row = format_result(_result(item), "table").splitlines()[1]

        self.assertLessEqual(len(row.split("  ")[-1]), 80)
        self.assertTrue(row.rstrip().endswith("…"))

    def test_control_characters_of_untrusted_text_are_neutralized(self):
        item = make_item("a.py", 1, "\x1b[31mred\x1b]0;title\x07 message", "bo\x1bb")

        output = format_result(_result(item), "table")

        self.assertNotIn("\x1b", output)
        self.assertNotIn("\x07", output)
        self.assertIn("red", output)

    def test_unowned_items_show_a_dash(self):
        self.assertIn(" -  ", format_result(_result(make_item("a.py", 1, "m")), "table").splitlines()[1])

    def test_paths_are_relative_to_the_repo_root_if_given(self):
        result = _result(make_item("app.py", 3, "m"), root="/work/widgets/src")

        self.assertTrue(format_result(result, "table").splitlines()[1].startswith("app.py:3"))
        self.assertTrue(format_result(result, "table", repo_root="/work/widgets").splitlines()[1].startswith("src/app.py:3"))


class TestDescribeDueAndSeverity(unittest.TestCase):
    def test_describe_due(self):
        cases = [
            (make_item("a.py", 1, "m"), "-"),
            (make_item("a.py", 1, "m", None, date(2026, 4, 1)), "2026-04-01 overdue 30d"),
            (make_item("a.py", 1, "m", None, date(2026, 4, 1), explicit=False), "2026-04-01 stale 30d"),
            (make_item("a.py", 1, "m", None, TODAY), "2026-05-01 due today"),
            (make_item("a.py", 1, "m", None, date(2026, 5, 8)), "2026-05-08 due in 7d"),
        ]
        for item, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(expected, describe_due(item, TODAY))

    def test_describe_due_of_a_passed_date_without_a_source(self):
        item = make_item("a.py", 1, "m", None, date(2026, 4, 29))
        item.due_source = "none"

        self.assertEqual("2026-04-29 2d ago", describe_due(item, TODAY))

    def test_severity(self):
        cases = [
            (make_item("a.py", 1, "m", None, date(2026, 4, 1)), "error"),
            (make_item("a.py", 1, "m", None, date(2026, 4, 1), explicit=False), "warning"),
            (make_item("a.py", 1, "m", None, TODAY), "warning"),
            (make_item("a.py", 1, "m", None, date(2026, 5, 8)), "warning"),
            (make_item("a.py", 1, "m", None, date(2026, 5, 9)), "notice"),
            (make_item("a.py", 1, "m"), "notice"),
        ]
        for item, expected in cases:
            with self.subTest(due=item.due_date, source=item.due_source):
                self.assertEqual(expected, severity(item, TODAY))


class TestJson(unittest.TestCase):
    def test_should_be_the_indented_to_dict(self):
        result = make_scan_result()

        self.assertEqual(json.dumps(result.to_dict(), indent=2), format_result(result, "json"))

    def test_should_validate_against_the_schema(self):
        validator = Draft202012Validator(_load_schema(), format_checker=Draft202012Validator.FORMAT_CHECKER)
        Draft202012Validator.check_schema(_load_schema())

        for result in (make_scan_result(), _result()):
            validator.validate(json.loads(format_result(result, "json")))

    def test_schema_should_reject_bad_documents(self):
        validator = Draft202012Validator(_load_schema(), format_checker=Draft202012Validator.FORMAT_CHECKER)
        good = json.loads(format_result(make_scan_result(), "json"))
        broken = []
        for change in (
            lambda d: d.update(schema_version=2),
            lambda d: d.pop("items"),
            lambda d: d["items"][0].update(line=0),
            lambda d: d["items"][0].update(due_source="maybe"),
            lambda d: d["items"][0].update(due_date="01/04/2026"),
            lambda d: d["items"][0].pop("tag"),
            lambda d: d["items"][0].update(is_overdue="yes"),
        ):
            document = json.loads(json.dumps(good))
            change(document)
            broken.append(document)

        for document in broken:
            with self.subTest(document=document["schema_version"]):
                self.assertFalse(validator.is_valid(document))

    def test_schema_should_ship_next_to_the_module(self):
        self.assertTrue(os.path.isfile(SCHEMA_PATH))
        self.assertEqual("https://json-schema.org/draft/2020-12/schema", _load_schema()["$schema"])


class TestGithub(unittest.TestCase):
    def test_snapshot(self):
        assert_matches_snapshot(self, "github.txt", format_result(make_scan_result(), "github", repo_root="/work/widgets"))

    def test_every_line_is_a_workflow_command_except_the_summary(self):
        lines = format_result(make_scan_result(), "github").splitlines()

        for line in lines[:-1]:
            self.assertRegex(line, ANNOTATION_PATTERN)
        self.assertEqual("10 TODOs: 4 overdue, 3 stale, 4 unowned", lines[-1])
        self.assertEqual(["error"] * 4, [re.match(r"::(\w+)", line).group(1) for line in lines if "overdue by" in line])

    def test_levels_and_titles(self):
        result = _result(
            make_item("a.py", 1, "overdue", None, date(2026, 4, 1)),
            make_item("a.py", 2, "stale", None, date(2026, 4, 1), explicit=False),
            make_item("a.py", 3, "soon", None, date(2026, 5, 4)),
            make_item("a.py", 4, "today", None, TODAY),
            make_item("a.py", 5, "later", None, date(2026, 6, 1)),
            make_item("a.py", 6, "undated"),
        )

        lines = format_result(result, "github").splitlines()

        self.assertEqual(
            [
                ("error", "TODO overdue by 30d"),
                ("warning", "TODO stale by 30d"),
                ("warning", "TODO due in 3d"),
                ("warning", "TODO due today"),
                ("notice", "TODO due in 31d"),
                ("notice", "TODO"),
            ],
            [re.match(r"::(\w+) .*title=([^:]*)::", line).groups() for line in lines[:-1]],
        )

    def test_escaping_follows_the_github_rules(self):
        self.assertEqual("100%25 done%0D%0Aok: a,b", _escape_data("100% done\r\nok: a,b"))
        self.assertEqual("a%3Ab%2Cc%25%0A", _escape_property("a:b,c%\n"))

    def test_untrusted_text_cannot_break_out_of_the_command(self):
        item = make_item("dir:odd,name.py", 3, "50% done\r\n::error::injected, really", "al:ice")

        lines = format_result(_result(item), "github").splitlines()

        self.assertEqual(2, len(lines))  # The command and the summary: the line break in the message did not start a new line
        self.assertTrue(lines[0].startswith("::notice file=dir%3Aodd%2Cname.py,line=3,title=TODO::"))
        self.assertEqual("::notice file=dir%3Aodd%2Cname.py,line=3,title=TODO::50%25 done ::error::injected, really (@al:ice)", lines[0])

    def test_paths_are_repo_relative_when_the_scan_root_is_a_subdirectory(self):
        result = _result(make_item("app.py", 3, "m"), root="/work/widgets/src")

        self.assertIn("file=src/app.py,", format_result(result, "github", repo_root="/work/widgets"))
        self.assertIn("file=app.py,", format_result(result, "github"))

    def test_item_without_message_and_with_owner_and_default_date(self):
        item = make_item("a.py", 1, "", "alice", date(2026, 6, 1), explicit=False)

        self.assertIn(
            "::TODO without a description (@alice, default due 2026-06-01)",
            format_result(_result(item), "github").replace("::notice file=a.py,line=1,title=TODO due in 31d", ""),
        )

    def test_no_items_gives_only_the_summary(self):
        self.assertEqual("0 TODOs: 0 overdue, 0 stale, 0 unowned", format_result(_result(), "github"))


class TestSarif(unittest.TestCase):
    def test_snapshot(self):
        assert_matches_snapshot(self, "sarif.json", json.loads(format_result(make_scan_result(), "sarif", repo_root="/work/widgets")))

    def test_structure(self):
        item_fixme = make_item("src/b.py", 2, "fix", "bob", date(2026, 4, 1))
        item_fixme.tag = "FIXME"
        result = _result(
            make_item("src/a.py", 1, "todo", None, date(2026, 5, 2)), item_fixme, make_item("src/c.py", 9, "stale", None, date(2026, 4, 1), explicit=False)
        )

        sarif = json.loads(format_result(result, "sarif"))

        self.assertEqual("2.1.0", sarif["version"])
        self.assertIn("sarif-2.1.0", sarif["$schema"])
        run = sarif["runs"][0]
        self.assertEqual("todonotifier", run["tool"]["driver"]["name"])
        self.assertEqual(["FIXME", "TODO"], [rule["id"] for rule in run["tool"]["driver"]["rules"]])
        self.assertEqual(["warning", "error", "warning"], [r["level"] for r in run["results"]])
        self.assertEqual([1, 0, 1], [r["ruleIndex"] for r in run["results"]])
        location = run["results"][1]["locations"][0]["physicalLocation"]
        self.assertEqual({"uri": "src/b.py", "uriBaseId": "%SRCROOT%"}, location["artifactLocation"])
        self.assertEqual({"startLine": 2}, location["region"])
        self.assertEqual("bob", run["results"][1]["properties"]["owner"])
        self.assertNotIn("owner", run["results"][0]["properties"])

    def test_no_items_gives_a_run_without_results(self):
        sarif = json.loads(format_result(_result(), "sarif"))

        self.assertEqual([], sarif["runs"][0]["results"])
        self.assertEqual([], sarif["runs"][0]["tool"]["driver"]["rules"])

    def test_paths_are_repo_relative(self):
        result = _result(make_item("app.py", 3, "m"), root="/work/widgets/src")

        sarif = json.loads(format_result(result, "sarif", repo_root="/work/widgets"))

        self.assertEqual("src/app.py", sarif["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"])

    def test_paths_are_percent_encoded_because_a_sarif_uri_is_a_uri_reference(self):
        result = _result(make_item("c#/sub dir/naïve file.py", 3, "m"))

        sarif = json.loads(format_result(result, "sarif"))

        self.assertEqual("c%23/sub%20dir/na%C3%AFve%20file.py", sarif["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"])


class TestMarkdown(unittest.TestCase):
    def test_should_be_the_markdown_digest(self):
        result = make_scan_result()

        self.assertEqual(render_markdown(build_digest(result, today=TODAY)), format_result(result, "markdown", today=TODAY))

    def test_new_count_is_shown_when_given(self):
        output = format_result(make_scan_result(), "markdown", new_count=3)

        self.assertIn("| New |", output)


class TestFormatResult(unittest.TestCase):
    def test_html_is_not_a_text_format(self):
        self.assertEqual(("table", "json", "github", "markdown", "sarif"), TEXT_FORMATS)
        self.assertEqual((*TEXT_FORMATS, "html"), FORMATS)
        with self.assertRaises(ValueError) as context:
            format_result(make_scan_result(), "html")
        self.assertIn("build_reports", str(context.exception))

    def test_unknown_format(self):
        with self.assertRaises(ValueError):
            format_result(make_scan_result(), "yaml")

    def test_every_text_format_works_on_an_empty_result(self):
        for fmt in TEXT_FORMATS:
            with self.subTest(fmt=fmt):
                self.assertTrue(format_result(_result(), fmt))


class TestReports(unittest.TestCase):
    def test_build_reports_renders_the_three_builtin_reports(self):
        reports = build_reports(make_scan_result())

        self.assertEqual(["Module-wise Summary", "Expired TODO Items", "Upcoming Week TODO Items"], [name for name, _ in reports])
        by_name = dict(reports)
        self.assertIn("Remove the legacy path", by_name["Module-wise Summary"])
        self.assertIn("src/app.py", by_name["Module-wise Summary"])
        self.assertIn("Handle &lt;None&gt; &amp; empty input", by_name["Module-wise Summary"])  # Autoescaped

    def test_build_reports_treats_only_explicit_dates_as_expired_or_upcoming(self):
        today = date.today()
        stale = make_item("src/old.py", 3, "stale default date", "alice", today - timedelta(days=30), explicit=False)
        soon = make_item("src/old.py", 9, "default date next week", "bob", today + timedelta(days=3), explicit=False)
        late = make_item("src/new.py", 5, "explicit date passed", "carol", today - timedelta(days=2))
        next_week = make_item("src/new.py", 8, "explicit date next week", "dave", today + timedelta(days=3))
        result = _result(stale, soon, late, next_week)

        by_name = dict(build_reports(result))

        self.assertIn("explicit date passed", by_name["Expired TODO Items"])
        self.assertNotIn("stale default date", by_name["Expired TODO Items"])
        self.assertNotIn("alice", by_name["Expired TODO Items"])
        self.assertIn("explicit date next week", by_name["Upcoming Week TODO Items"])
        self.assertNotIn("default date next week", by_name["Upcoming Week TODO Items"])
        for message in ("stale default date", "default date next week", "explicit date passed", "explicit date next week"):
            self.assertIn(message, by_name["Module-wise Summary"])  # Every TODO is still listed by module

    def test_build_reports_does_not_carry_state_between_calls(self):
        result = make_scan_result()

        self.assertEqual(build_reports(result), build_reports(result))

    def test_write_reports_creates_the_directory_and_returns_the_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "nested", "reports")

            paths = write_reports(build_reports(make_scan_result()), target)

            self.assertEqual(
                [os.path.join(target, f"{name}.html") for name in ("Module-wise Summary", "Expired TODO Items", "Upcoming Week TODO Items")], paths
            )
            self.assertTrue(os.path.getsize(paths[0]) > 0)
            self.assertTrue(all(os.path.isfile(path) for path in paths))
