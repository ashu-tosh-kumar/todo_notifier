import json
import os
import unittest
from datetime import date, datetime, timedelta, timezone

from todonotifier.constants import DEFAULT_COMPLETION_DATE, UNKNOWN_USER_NAME
from todonotifier.models import POSITION, TODO, USER
from todonotifier.results import (
    SCHEMA_VERSION,
    ScanResult,
    TodoItem,
    build_web_url,
    compute_status,
)

TODAY = date(2025, 6, 15)


def make_item(**overrides) -> TodoItem:
    values = {"file": "src/a.py", "line": 3, "tag": "TODO", "message": "unittest-message"}
    values.update(overrides)
    return TodoItem(**values)


class TestBuildWebUrl(unittest.TestCase):
    def test_build_web_url_should_follow_the_blob_pattern(self):
        url = build_web_url("https://github.com/org/repo", "abc123", "src/a.py", 7)

        self.assertEqual("https://github.com/org/repo/blob/abc123/src/a.py#L7", url)

    def test_build_web_url_should_ignore_trailing_slash_and_quote_the_path(self):
        url = build_web_url("https://github.com/org/repo/", "abc123", "my dir/a#b.py", 1)

        self.assertEqual("https://github.com/org/repo/blob/abc123/my%20dir/a%23b.py#L1", url)

    def test_build_web_url_should_be_none_without_repo_web_url_or_commit_sha(self):
        self.assertIsNone(build_web_url(None, "abc123", "a.py", 1))
        self.assertIsNone(build_web_url("https://github.com/org/repo", None, "a.py", 1))
        self.assertIsNone(build_web_url("", "", "a.py", 1))


class TestComputeStatus(unittest.TestCase):
    def test_explicit_date_in_the_past_should_be_overdue(self):
        self.assertEqual((True, False, 5), compute_status(TODAY - timedelta(days=5), "explicit", TODAY))

    def test_default_date_in_the_past_should_be_stale(self):
        self.assertEqual((False, True, 2), compute_status(TODAY - timedelta(days=2), "default", TODAY))

    def test_due_today_or_later_should_be_neither(self):
        self.assertEqual((False, False, 0), compute_status(TODAY, "explicit", TODAY))
        self.assertEqual((False, False, 0), compute_status(TODAY + timedelta(days=1), "default", TODAY))

    def test_no_date_should_be_neither(self):
        self.assertEqual((False, False, 0), compute_status(None, "none", TODAY))
        self.assertEqual((False, False, 0), compute_status(date(2000, 1, 1), "none", TODAY))


class TestTodoItem(unittest.TestCase):
    def test_defaults_should_describe_an_unowned_undated_item(self):
        item = make_item()

        self.assertIsNone(item.author)
        self.assertEqual("unknown", item.author_source)
        self.assertIsNone(item.due_date)
        self.assertEqual("none", item.due_source)
        self.assertIsNone(item.created_date)
        self.assertFalse(item.is_overdue)
        self.assertFalse(item.is_stale)
        self.assertEqual(0, item.days_past_due)
        self.assertIsNone(item.web_url)

    def test_refresh_status_should_recompute_from_due_date(self):
        item = make_item(due_date=TODAY - timedelta(days=3), due_source="default")

        item.refresh_status(TODAY)

        self.assertTrue(item.is_stale)
        self.assertFalse(item.is_overdue)
        self.assertEqual(3, item.days_past_due)

    def test_to_dict_should_use_iso_strings_for_dates(self):
        item = make_item(author="alice", due_date=date(2025, 1, 2), due_source="explicit", created_date=date(2024, 12, 31))

        data = item.to_dict()

        self.assertEqual("2025-01-02", data["due_date"])
        self.assertEqual("2024-12-31", data["created_date"])
        self.assertEqual("alice", data["author"])
        json.dumps(data)

    def test_to_dict_should_keep_missing_dates_as_none(self):
        data = make_item().to_dict()

        self.assertIsNone(data["due_date"])
        self.assertIsNone(data["created_date"])

    def test_dict_round_trip_should_be_unchanged(self):
        item = make_item(
            author="alice",
            author_source="git_blame",
            due_date=date(2025, 1, 2),
            due_source="explicit",
            created_date=date(2024, 12, 31),
            is_overdue=True,
            days_past_due=164,
            web_url="https://example.com/x",
        )

        self.assertEqual(item, TodoItem.from_dict(json.loads(json.dumps(item.to_dict()))))

    def test_from_dict_should_tolerate_missing_optional_keys(self):
        item = TodoItem.from_dict({"file": "a.py", "line": 1, "message": "m"})

        self.assertEqual(make_item(file="a.py", line=1, message="m"), item)

    def test_from_legacy_with_explicit_date_and_user_should_be_explicit_and_annotated(self):
        todo = TODO("msg", USER("alice"), "2025-06-10", "src/a.py", POSITION(4))

        item = TodoItem.from_legacy(todo, today=TODAY)

        self.assertEqual("src/a.py", item.file)
        self.assertEqual(4, item.line)
        self.assertEqual("TODO", item.tag)
        self.assertEqual("msg", item.message)
        self.assertEqual("alice", item.author)
        self.assertEqual("annotation", item.author_source)
        self.assertEqual(date(2025, 6, 10), item.due_date)
        self.assertEqual("explicit", item.due_source)
        self.assertTrue(item.is_overdue)
        self.assertFalse(item.is_stale)
        self.assertEqual(5, item.days_past_due)

    def test_from_legacy_should_turn_the_no_date_sentinel_into_none(self):
        todo = TODO("msg", USER(UNKNOWN_USER_NAME), "", "a.py", POSITION(1))
        self.assertEqual(DEFAULT_COMPLETION_DATE, str(todo.completion_date))

        item = TodoItem.from_legacy(todo, today=TODAY)

        self.assertIsNone(item.due_date)
        self.assertEqual("none", item.due_source)
        self.assertIsNone(item.author)
        self.assertEqual("unknown", item.author_source)
        self.assertFalse(item.is_overdue)

    def test_from_legacy_should_treat_an_empty_user_name_as_unknown(self):
        todo = TODO("msg", USER(""), "", "a.py", POSITION(1))

        self.assertIsNone(TodoItem.from_legacy(todo, today=TODAY).author)

    def test_from_legacy_should_default_today_to_the_current_date(self):
        todo = TODO("msg", USER("alice"), "2000-01-01", "a.py", POSITION(1))

        item = TodoItem.from_legacy(todo)

        self.assertTrue(item.is_overdue)
        self.assertEqual((date.today() - date(2000, 1, 1)).days, item.days_past_due)

    def test_from_legacy_should_convert_the_path_to_posix(self):
        todo = TODO("msg", USER("alice"), "", os.path.join("src", "pkg", "a.py"), POSITION(1))

        self.assertEqual("src/pkg/a.py", TodoItem.from_legacy(todo, today=TODAY).file)

    def test_from_legacy_should_build_web_url_and_accept_a_tag(self):
        todo = TODO("msg", USER("alice"), "", "src/a.py", POSITION(9))

        item = TodoItem.from_legacy(todo, today=TODAY, tag="FIXME", repo_web_url="https://github.com/org/repo", commit_sha="abc")

        self.assertEqual("FIXME", item.tag)
        self.assertEqual("https://github.com/org/repo/blob/abc/src/a.py#L9", item.web_url)

    def test_from_legacy_should_use_the_tag_of_the_legacy_todo(self):
        todo = TODO("msg", USER("alice"), "", "src/a.py", POSITION(9), tag="HACK")

        self.assertEqual("HACK", TodoItem.from_legacy(todo, today=TODAY).tag)
        self.assertEqual("TODO", TodoItem.from_legacy(TODO("msg", USER("alice"), "", "a.py", POSITION(1)), today=TODAY).tag)

    def test_to_legacy_should_keep_the_tag(self):
        self.assertEqual("FIXME", make_item(tag="FIXME").to_legacy().tag)

    def test_to_legacy_should_restore_the_sentinel_and_unknown_user(self):
        legacy = make_item().to_legacy()

        self.assertEqual(DEFAULT_COMPLETION_DATE, str(legacy.completion_date))
        self.assertEqual(UNKNOWN_USER_NAME, legacy.user.user_name)
        self.assertEqual("unittest-message", legacy.msg)
        self.assertEqual("src/a.py", legacy.module)
        self.assertEqual(3, legacy.position.line_no)

    def test_to_legacy_should_keep_author_and_due_date(self):
        legacy = make_item(author="alice", due_date=date(2025, 1, 2), due_source="explicit").to_legacy()

        self.assertEqual("alice", legacy.user.user_name)
        self.assertEqual(date(2025, 1, 2), legacy.completion_date)

    def test_legacy_round_trip_should_preserve_the_todo(self):
        for completion_date_str, user_name in (("", UNKNOWN_USER_NAME), ("2022-05-03", "ashutosh"), ("2022-05-01", UNKNOWN_USER_NAME)):
            original = TODO("msg", USER(user_name), completion_date_str, "a.py", POSITION(2))

            restored = TodoItem.from_legacy(original, today=TODAY).to_legacy()

            self.assertEqual(original.msg, restored.msg)
            self.assertEqual(original.user.user_name, restored.user.user_name)
            self.assertEqual(original.completion_date, restored.completion_date)
            self.assertEqual(original.module, restored.module)
            self.assertEqual(original.position.line_no, restored.position.line_no)


class TestScanResult(unittest.TestCase):
    def setUp(self) -> None:
        self.overdue = make_item(file="b.py", line=1, author="alice", due_date=TODAY - timedelta(days=1), due_source="explicit")
        self.stale = make_item(file="a.py", line=2, author="bob", due_date=TODAY - timedelta(days=9), due_source="default")
        self.soon = make_item(file="a.py", line=5, author="alice", due_date=TODAY + timedelta(days=7), due_source="explicit")
        self.later = make_item(file="c.py", line=1, due_date=TODAY + timedelta(days=8), due_source="explicit")
        self.today = make_item(file="c.py", line=2, due_date=TODAY, due_source="default")
        self.undated = make_item(file="c.py", line=3)
        for item in (self.overdue, self.stale, self.soon, self.later, self.today, self.undated):
            item.refresh_status(TODAY)
        self.result = ScanResult(
            items=[self.overdue, self.stale, self.soon, self.later, self.today, self.undated],
            scanned_files=["a.py", "b.py", "c.py", "d.py"],
            root="/unittest/root",
            generated_at=datetime(2025, 6, 15, 8, 30, tzinfo=timezone(timedelta(hours=5, minutes=30))),
        )

    def test_schema_version_should_start_at_one(self):
        self.assertEqual(1, SCHEMA_VERSION)
        self.assertEqual(1, ScanResult().schema_version)

    def test_default_generated_at_should_be_timezone_aware(self):
        self.assertIsNotNone(ScanResult().generated_at.tzinfo)

    def test_overdue_should_only_return_explicit_dates_that_passed(self):
        self.assertEqual([self.overdue], self.result.overdue())

    def test_stale_should_only_return_default_dates_that_passed(self):
        self.assertEqual([self.stale], self.result.stale())

    def test_due_within_should_include_today_and_the_last_day_of_the_window(self):
        self.assertCountEqual([self.soon, self.today], self.result.due_within(7))

    def test_due_within_should_use_the_given_reference_day(self):
        self.assertEqual([self.stale], self.result.due_within(0, today=TODAY - timedelta(days=9)))

    def test_by_author_should_group_missing_authors_under_the_unknown_user(self):
        grouped = self.result.by_author()

        self.assertEqual([self.overdue, self.soon], grouped["alice"])
        self.assertEqual([self.stale], grouped["bob"])
        self.assertEqual([self.later, self.today, self.undated], grouped[UNKNOWN_USER_NAME])

    def test_by_file_should_group_items(self):
        grouped = self.result.by_file()

        self.assertEqual({"a.py", "b.py", "c.py"}, set(grouped))
        self.assertEqual([self.stale, self.soon], grouped["a.py"])

    def test_to_legacy_should_include_scanned_files_without_todos(self):
        legacy = self.result.to_legacy()

        self.assertEqual(["a.py", "b.py", "c.py", "d.py"], sorted(legacy))
        self.assertEqual([], legacy["d.py"])
        self.assertEqual(2, len(legacy["a.py"]))
        self.assertIsInstance(legacy["a.py"][0], TODO)

    def test_to_legacy_should_include_files_missing_from_scanned_files(self):
        result = ScanResult(items=[make_item(file="x.py")])

        self.assertEqual(["x.py"], list(result.to_legacy()))

    def test_json_round_trip_should_be_unchanged(self):
        restored = ScanResult.from_dict(json.loads(json.dumps(self.result.to_dict())))

        self.assertEqual(self.result, restored)

    def test_to_dict_should_be_self_describing(self):
        data = self.result.to_dict()

        self.assertEqual(1, data["schema_version"])
        self.assertEqual("/unittest/root", data["root"])
        self.assertEqual("2025-06-15T08:30:00+05:30", data["generated_at"])
        self.assertEqual(["a.py", "b.py", "c.py", "d.py"], data["scanned_files"])
        self.assertEqual(6, len(data["items"]))
        self.assertTrue(data["items"][0]["is_overdue"])
        self.assertEqual(1, data["items"][0]["days_past_due"])

    def test_from_dict_should_tolerate_missing_optional_keys(self):
        result = ScanResult.from_dict({})

        self.assertEqual([], result.items)
        self.assertEqual([], result.scanned_files)
        self.assertEqual("", result.root)
        self.assertEqual(1, result.schema_version)
        self.assertIsNotNone(result.generated_at.tzinfo)

    def test_from_dict_should_reject_a_newer_schema_version(self):
        with self.assertRaises(ValueError):
            ScanResult.from_dict({"schema_version": 2})


if __name__ == "__main__":
    unittest.main()
