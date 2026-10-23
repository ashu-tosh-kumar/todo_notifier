import unittest
from datetime import date, datetime, timezone

from tests.sample_results import (
    TODAY,
    assert_matches_snapshot,
    make_item,
    make_scan_result,
)
from todonotifier.digest import (
    MAX_MESSAGE_LENGTH,
    SECTION_DUE_SOON,
    SECTION_OVERDUE,
    SECTION_STALE,
    DigestItem,
    OwnerGroup,
    build_digest,
    describe_item,
    escape_markdown,
    render_markdown,
    render_text,
    safe_url,
    shorten_message,
)
from todonotifier.results import ScanResult


def _result(*items) -> ScanResult:
    return ScanResult(items=list(items), generated_at=datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc))


class TestBuildDigest(unittest.TestCase):
    def test_totals(self):
        digest = build_digest(make_scan_result(), today=TODAY)

        self.assertEqual((10, 4, 3, 2, 4, None), tuple(vars(digest.totals).values()))
        self.assertEqual(TODAY, digest.generated_on)

    def test_new_count_is_part_of_totals_and_headline_only_when_given(self):
        self.assertNotIn("new", build_digest(make_scan_result(), today=TODAY).totals.to_dict())
        self.assertNotIn("new", build_digest(make_scan_result(), today=TODAY).headline)

        digest = build_digest(make_scan_result(), today=TODAY, new_count=0)

        self.assertEqual(0, digest.totals.to_dict()["new"])
        self.assertEqual("10 open, 4 overdue, 3 stale, 2 due this week, 4 unowned, 0 new", digest.headline)

    def test_sections_are_overdue_then_stale_then_due_this_week_and_stale_is_not_overdue(self):
        digest = build_digest(make_scan_result(), today=TODAY)

        self.assertEqual([SECTION_OVERDUE, SECTION_STALE, SECTION_DUE_SOON], [section.key for section in digest.sections])
        self.assertEqual(["Overdue", "Stale", "Due this week"], [section.title for section in digest.sections])
        stale_files = {(item.file, item.line) for group in digest.sections[1].groups for item in group.items}
        self.assertEqual({("src/old.py", 3), ("src/old.py", 40), ("src/api.py", 12)}, stale_files)

    def test_owners_are_sorted_by_count_then_name_with_unowned_last(self):
        past = date(2026, 4, 1)
        digest = build_digest(
            _result(
                make_item("a.py", 1, "m", None, past),
                make_item("a.py", 2, "m", None, past),
                make_item("a.py", 3, "m", None, past),
                make_item("a.py", 4, "m", "zed", past),
                make_item("a.py", 5, "m", "Bob", past),
                make_item("a.py", 6, "m", "amy", past),
                make_item("a.py", 7, "m", "carl", past),
                make_item("a.py", 8, "m", "carl", past),
            ),
            today=TODAY,
        )

        group_owners = [group.owner for group in digest.sections[0].groups]
        self.assertEqual(["carl", "amy", "Bob", "zed", None], group_owners)
        self.assertEqual("Unowned", digest.sections[0].groups[-1].label)

    def test_items_of_an_owner_are_sorted_by_days_past_due_then_location(self):
        digest = build_digest(
            _result(
                make_item("b.py", 1, "m", "amy", date(2026, 4, 20)),
                make_item("z.py", 9, "m", "amy", date(2026, 3, 1)),
                make_item("a.py", 5, "m", "amy", date(2026, 4, 20)),
            ),
            today=TODAY,
        )

        items = digest.sections[0].groups[0].items
        self.assertEqual([("z.py", 9), ("a.py", 5), ("b.py", 1)], [(item.file, item.line) for item in items])
        self.assertEqual([61, 11, 11], [item.days_past_due for item in items])

    def test_top_n_limits_each_section_in_total_and_counts_the_rest(self):
        digest = build_digest(make_scan_result(), top_n=3, today=TODAY)

        overdue = digest.sections[0]
        self.assertEqual(4, overdue.total)
        self.assertEqual(3, sum(len(group.items) for group in overdue.groups))
        self.assertEqual(1, overdue.hidden_count)
        self.assertEqual([2, 1], [group.count for group in overdue.groups])
        self.assertEqual(0, digest.sections[1].hidden_count)

    def test_group_counts_include_hidden_items_and_owners_without_shown_items_are_dropped(self):
        digest = build_digest(make_scan_result(), top_n=2, today=TODAY)

        overdue = digest.sections[0]
        self.assertEqual(["alice"], [group.owner for group in overdue.groups])
        self.assertEqual(2, overdue.hidden_count)
        self.assertEqual(4, overdue.total)

    def test_top_n_below_one_is_rejected(self):
        with self.assertRaises(ValueError):
            build_digest(make_scan_result(), top_n=0)

    def test_today_defaults_to_the_day_of_generated_at(self):
        digest = build_digest(make_scan_result())

        self.assertEqual(date(2026, 5, 1), digest.generated_on)
        self.assertEqual(4, digest.totals.overdue)

    def test_status_is_computed_against_today_not_the_stored_flags(self):
        digest = build_digest(make_scan_result(), today=date(2026, 4, 12))

        self.assertEqual(date(2026, 4, 12), digest.generated_on)
        self.assertEqual(2, digest.totals.overdue)  # only the 2026-04-01 and 2026-03-02 dates have passed
        self.assertEqual(2, digest.totals.stale)

    def test_empty_result_has_empty_sections(self):
        digest = build_digest(_result(), today=TODAY)

        self.assertTrue(digest.is_empty)
        self.assertEqual(0, digest.totals.open)
        self.assertEqual(3, len(digest.sections))

    def test_items_without_due_date_are_only_counted_as_open(self):
        digest = build_digest(_result(make_item("a.py", 1, "no date", "amy")), today=TODAY)

        self.assertFalse(any(section.total for section in digest.sections))
        self.assertEqual(1, digest.totals.open)
        self.assertEqual(0, digest.totals.unowned)

    def test_due_today_counts_as_due_this_week_not_overdue(self):
        digest = build_digest(_result(make_item("a.py", 1, "today", "amy", TODAY)), today=TODAY)

        self.assertEqual((0, 1), (digest.totals.overdue, digest.totals.due_soon))

    def test_empty_author_counts_as_unowned(self):
        item = make_item("a.py", 1, "m", "", date(2026, 4, 1))

        digest = build_digest(_result(item), today=TODAY)

        self.assertEqual(1, digest.totals.unowned)
        self.assertIsNone(digest.sections[0].groups[0].owner)

    def test_long_messages_are_truncated_and_put_on_one_line(self):
        digest = build_digest(_result(make_item("a.py", 1, "word " * 100 + "\n\ttail", "amy", date(2026, 4, 1))), today=TODAY)

        message = digest.sections[0].groups[0].items[0].message
        self.assertEqual(MAX_MESSAGE_LENGTH, len(message))
        self.assertTrue(message.endswith("…"))
        self.assertNotIn("\n", message)

    def test_web_url_is_kept_and_location_is_file_and_line(self):
        digest = build_digest(make_scan_result(), today=TODAY)

        item = digest.sections[0].groups[0].items[0]
        self.assertEqual("src/app.py:10", item.location)
        self.assertEqual("https://github.com/acme/widgets/blob/0123456789abcdef0123456789abcdef01234567/src/app.py#L10", item.web_url)

    def test_to_dict_is_json_friendly(self):
        import json

        data = build_digest(make_scan_result(), top_n=2, today=TODAY, new_count=1).to_dict()

        self.assertEqual(data, json.loads(json.dumps(data)))
        self.assertEqual(1, data["totals"]["new"])
        self.assertEqual("2026-04-01", data["sections"][0]["groups"][0]["items"][0]["due_date"])

    def test_to_dict_without_due_date(self):
        digest = build_digest(_result(make_item("a.py", 1, "m", "amy", TODAY)), today=TODAY)
        digest.sections[2].groups[0].items[0].due_date = None

        self.assertIsNone(digest.to_dict()["sections"][2]["groups"][0]["items"][0]["due_date"])


class TestHelpers(unittest.TestCase):
    def test_shorten_message(self):
        self.assertEqual("a b c", shorten_message("a\n  b\tc "))
        self.assertEqual("abcdefghi…", shorten_message("abcdefghijklmnop", limit=10))
        self.assertEqual("abcde", shorten_message("abcde", limit=5))

    def test_safe_url(self):
        self.assertEqual("https://x.test/a%28b%29", safe_url("https://x.test/a(b)"))
        self.assertEqual("http://x.test/a", safe_url("http://x.test/a"))
        for bad in (
            None,
            "",
            "javascript:alert(1)",
            "ftp://x.test/a",
            "https://",
            "https://x.test/a b",
            "https://x.test/a>b",
            "https://x.test/a|b",
            "/relative",
        ):
            self.assertIsNone(safe_url(bad), bad)

    def test_escape_markdown(self):
        self.assertEqual(
            r"\[click\](http://evil) \*bold\* \_i\_ \<b\> a\|b \`c\` \\ \& \# \~", escape_markdown("[click](http://evil) *bold* _i_ <b> a|b `c` \\ & # ~")
        )

    def test_describe_item(self):
        item = DigestItem("a.py", 1, "TODO", "m", days_past_due=1, due_date=date(2026, 5, 3))

        self.assertEqual("1 day overdue", describe_item(SECTION_OVERDUE, item))
        self.assertEqual("1 day stale", describe_item(SECTION_STALE, item))
        item.days_past_due = 5
        self.assertEqual("5 days stale", describe_item(SECTION_STALE, item))
        self.assertEqual("due 2026-05-03", describe_item(SECTION_DUE_SOON, item))
        item.due_date = None
        self.assertEqual("due soon", describe_item(SECTION_DUE_SOON, item))

    def test_owner_group_label(self):
        self.assertEqual("amy", OwnerGroup("amy", 1).label)
        self.assertEqual("Unowned", OwnerGroup(None, 1).label)


class TestRenderers(unittest.TestCase):
    def setUp(self):
        self.digest = build_digest(make_scan_result(), top_n=3, today=TODAY, new_count=2)

    def test_render_text_snapshot(self):
        assert_matches_snapshot(self, "digest.txt", render_text(self.digest))

    def test_render_markdown_snapshot(self):
        assert_matches_snapshot(self, "digest.md", render_markdown(self.digest))

    def test_render_markdown_escapes_messages_and_drops_unsafe_links(self):
        item = make_item("a`b.py", 1, "[click](http://evil) <b>x</b>", "amy", date(2026, 4, 1))
        item.web_url = "javascript:alert(1)"

        markdown = render_markdown(build_digest(_result(item), today=TODAY))

        self.assertIn(r"\[click\](http://evil) \<b\>x\</b\>", markdown)
        self.assertIn("`a'b.py:1`", markdown)
        self.assertNotIn("javascript", markdown)

    def test_render_without_new_has_no_new_column(self):
        digest = build_digest(make_scan_result(), today=TODAY)

        self.assertNotIn("New", render_markdown(digest))
        self.assertNotIn(" new", render_text(digest).splitlines()[1])

    def test_render_empty_digest(self):
        digest = build_digest(_result(), today=TODAY)

        self.assertIn("Nothing is overdue, stale or due this week.", render_text(digest))
        self.assertIn("Nothing is overdue, stale or due this week.", render_markdown(digest))

    def test_render_item_without_link_in_text_and_markdown(self):
        digest = build_digest(_result(make_item("a.py", 1, "m", "amy", date(2026, 4, 1), linked=False)), today=TODAY)

        self.assertIn("    a.py:1  m (30 days overdue)", render_text(digest))
        self.assertIn("- `a.py:1` m (30 days overdue)", render_markdown(digest))
