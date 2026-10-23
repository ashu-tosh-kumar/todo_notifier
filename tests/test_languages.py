import os
import time
import unittest
from datetime import date
from typing import Optional

from todonotifier.languages import (
    COMMENT_SYNTAX,
    COMMON_EXTENSIONS,
    CommentIndex,
    CommentLexer,
    CommentSyntax,
    expand_extensions,
    find_comment_end,
    get_comment_syntax,
)
from todonotifier.scanner import scan
from todonotifier.settings import ScanSettings

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "languages")
ALL_TAGS = ["TODO", "FIXME", "HACK", "XXX"]


class TestExpandExtensions(unittest.TestCase):
    def test_common_preset_should_have_the_agreed_extensions(self):
        self.assertEqual(
            "py js jsx ts tsx java kt go rs rb php c h cpp hpp cs swift scala sh sql yaml yml toml html css scss md".split(),
            COMMON_EXTENSIONS,
        )

    def test_common_string_should_expand_to_the_preset(self):
        self.assertEqual(COMMON_EXTENSIONS, expand_extensions("common"))

    def test_common_should_be_case_insensitive(self):
        self.assertEqual(COMMON_EXTENSIONS, expand_extensions(" Common "))

    def test_expansion_should_return_a_copy(self):
        expand_extensions("common").append("zzz")

        self.assertNotIn("zzz", COMMON_EXTENSIONS)

    def test_common_inside_a_list_should_expand_in_place_and_deduplicate(self):
        result = expand_extensions(["proto", "common", "py", "go"])

        self.assertEqual(["proto"] + COMMON_EXTENSIONS, result)

    def test_single_extension_string_should_become_a_list(self):
        self.assertEqual(["py"], expand_extensions("py"))

    def test_leading_dots_and_blanks_should_be_stripped(self):
        self.assertEqual(["py", "js"], expand_extensions([".py", "  ", "js", ".js", "..", ""]))

    def test_order_of_first_appearance_should_be_kept(self):
        self.assertEqual(["ts", "py", "js"], expand_extensions(["ts", "py", "js", "ts"]))

    def test_empty_list_should_give_an_empty_list(self):
        self.assertEqual([], expand_extensions([]))


def spans_of(extension: str, *lines: str) -> list:
    """Comment spans of each line, lexed in order, for a file with the given extension"""
    lexer = CommentLexer(COMMENT_SYNTAX[extension])
    return [lexer.comment_spans(line) for line in lines]


class TestGetCommentSyntax(unittest.TestCase):
    def test_every_common_extension_should_have_a_comment_syntax(self):
        for extension in COMMON_EXTENSIONS:
            self.assertIsNotNone(get_comment_syntax(f"file.{extension}"), extension)

    def test_markers_should_follow_the_spec(self):
        for extension in ("py", "sh", "rb", "yaml", "yml", "toml"):
            self.assertIn("#", COMMENT_SYNTAX[extension].line_markers, extension)
        for extension in "js jsx ts tsx java kt go c h cpp hpp cs swift rs php scala scss".split():
            self.assertIn("//", COMMENT_SYNTAX[extension].line_markers, extension)
            self.assertIn(("/*", "*/"), COMMENT_SYNTAX[extension].block_comments, extension)
        self.assertEqual((("/*", "*/"),), COMMENT_SYNTAX["css"].block_comments)
        self.assertEqual((), COMMENT_SYNTAX["css"].line_markers)
        for extension in ("sql", "lua"):
            self.assertIn("--", COMMENT_SYNTAX[extension].line_markers, extension)
        for extension in ("html", "md"):
            self.assertIn(("<!--", "-->"), COMMENT_SYNTAX[extension].block_comments, extension)

    def test_lookup_should_use_the_last_extension_and_ignore_case(self):
        self.assertIs(COMMENT_SYNTAX["js"], get_comment_syntax("/a/b.min.JS"))
        self.assertIs(COMMENT_SYNTAX["py"], get_comment_syntax("C:\\proj\\a.py"))

    def test_unknown_extensions_and_files_without_one_should_give_none(self):
        self.assertIsNone(get_comment_syntax("a.unknownext"))
        self.assertIsNone(get_comment_syntax("/a.b/Makefile"))
        self.assertIsNone(get_comment_syntax(""))

    def test_stateful_should_be_true_only_for_syntaxes_that_span_lines(self):
        self.assertFalse(COMMENT_SYNTAX["sh"].stateful)
        self.assertTrue(COMMENT_SYNTAX["c"].stateful)
        self.assertTrue(COMMENT_SYNTAX["py"].stateful)
        self.assertTrue(CommentSyntax(fenced_code=True).stateful)


class TestCommentLexer(unittest.TestCase):
    def test_line_comment_should_start_at_the_marker(self):
        self.assertEqual([[(7, 15)]], spans_of("py", "x = 1  # TODO a"))

    def test_line_without_comment_should_have_no_spans(self):
        self.assertEqual([[], []], spans_of("py", "x = 1", ""))

    def test_marker_inside_a_string_should_not_start_a_comment(self):
        self.assertEqual([[]], spans_of("py", 'x = "# TODO"'))
        self.assertEqual([[]], spans_of("py", "x = '# TODO'"))
        self.assertEqual([[]], spans_of("js", 'var u = "http://a/b"'))

    def test_comment_after_a_string_should_be_found(self):
        self.assertEqual([[(15, 21)]], spans_of("py", 'x = "a" + "b"  # TODO'))

    def test_escaped_quote_should_not_end_a_string(self):
        self.assertEqual([[]], spans_of("py", r'x = "a \" # TODO"'))
        self.assertEqual([[(14, 20)]], spans_of("py", r'x = "a \" b"  # TODO'))

    def test_unclosed_quote_should_be_an_ordinary_character(self):
        self.assertEqual([[(11, 15)]], spans_of("rs", "fn f<'a>() // c"))
        self.assertEqual([[(10, 13)]], spans_of("py", "x = it's  # c"))

    def test_block_comment_on_one_line_should_exclude_the_markers(self):
        self.assertEqual([[(4, 7)]], spans_of("c", "a /* b */ c"))

    def test_block_comment_across_lines_including_star_lines(self):
        spans = spans_of("c", "/*", " * TODO star line", "   TODO bare line", " */ code // TODO c", "code")

        self.assertEqual([[], [(0, 17)], [(0, 17)], [(0, 1), (9, 18)], []], spans)

    def test_text_after_a_block_comment_closes_is_code(self):
        self.assertEqual([[(2, 5), (10, 14)]], spans_of("c", "/* a */ x // y"))

    def test_block_comment_opener_inside_a_line_comment_is_ignored(self):
        self.assertEqual([[(0, 12)]], spans_of("c", "// a /* b */"))
        self.assertEqual([[]], spans_of("c", "x = 1"))

    def test_multiline_string_should_hide_markers_until_it_closes(self):
        spans = spans_of("py", 'x = """', "# TODO inside", 'end""" # TODO after', "y = 1")

        self.assertEqual([[], [], [(7, 19)], []], spans)

    def test_multiline_string_that_closes_on_its_own_line_is_just_a_string(self):
        self.assertEqual([[(13, 18)]], spans_of("py", 'x = """a"""  # abc'))

    def test_backtick_string_in_javascript(self):
        spans = spans_of("js", "const t = `a", "// TODO in template", "`; // TODO real")

        self.assertEqual([[], [], [(3, 15)]], spans)

    def test_longest_token_should_win_at_the_same_position(self):
        # `--[[` opens a block comment in Lua, `--` alone is a line comment
        self.assertEqual([[(4, 6)], [(0, 2), (7, 11)]], spans_of("lua", "--[[ a", "b ]] c -- d"))

    def test_spaced_line_markers_should_need_whitespace_before_the_hash(self):
        self.assertEqual([[]], spans_of("yaml", "url: http://a/#TODO"))
        self.assertEqual([[]], spans_of("sh", "echo $#"))
        self.assertEqual([[(0, 6)]], spans_of("yaml", "# TODO"))
        self.assertEqual([[(7, 13)]], spans_of("yaml", "key: v # TODO"))

    def test_a_byte_order_mark_should_not_hide_a_comment_on_the_first_line(self):
        # Windows editors put a BOM at the start of YAML and shell files, and "\ufeff#" is not a "# after whitespace"
        self.assertEqual([[(1, 7)]], spans_of("yaml", "\ufeff# TODO"))
        self.assertEqual([[(1, 7)]], spans_of("sh", "\ufeff# TODO"))
        self.assertEqual([[]], spans_of("yaml", "x\ufeff# TODO"))  # Only the mark itself counts as a separator, not the text before it

    def test_markdown_fence_should_hide_comments(self):
        spans = spans_of("md", "<!-- a -->", "```html", "<!-- TODO -->", "```", "<!-- b -->", "~~~", "<!-- c -->", "~~~", "<!-- d -->")

        self.assertEqual([[(4, 7)], [], [], [], [(4, 7)], [], [], [], [(4, 7)]], spans)

    def test_fence_marker_inside_a_html_comment_should_not_open_a_fence(self):
        spans = spans_of("md", "<!--", "```", "-->", "<!-- x -->")

        self.assertEqual([[], [(0, 3)], [(0, 0)], [(4, 7)]], spans)

    def test_a_long_line_should_be_lexed_in_linear_time(self):
        # A minified bundle is one line of megabytes with tens of thousands of string literals. Looking for every token again after every
        # literal took minutes for 1 MB; with remembered positions it takes milliseconds
        line = 'a("k","v");' * 40000 + " /* TODO real */"
        lexer = CommentLexer(COMMENT_SYNTAX["js"])

        started = time.perf_counter()
        spans = lexer.comment_spans(line)
        elapsed = time.perf_counter() - started

        self.assertEqual([(len(line) - len(" TODO real */"), len(line) - len("*/"))], spans)
        self.assertLess(elapsed, 5)

    def test_remembered_token_positions_should_not_change_the_result(self):
        # Several steps over one line, with tokens that are absent, that occur only before the current column, or that occur again later
        for extension, line, expected in (
            ("js", 'x = "a" /* one */ y = "b" // two "c" /* no', [" one ", '// two "c" /* no']),
            ("js", "a /* x */ b /* y */ c /* z */ d // e", [" x ", " y ", " z ", "// e"]),
            ("lua", "a --[[ one ]] b -- two", [" one ", "-- two"]),
            ("py", 'a = """x""" # c """ d', ['# c """ d']),
        ):
            with self.subTest(line=line):
                spans = CommentLexer(COMMENT_SYNTAX[extension]).comment_spans(line)

                self.assertEqual(expected, [line[start:end] for start, end in spans])

    def test_stateful_property_should_follow_the_syntax(self):
        self.assertTrue(CommentLexer(COMMENT_SYNTAX["c"]).stateful)
        self.assertFalse(CommentLexer(COMMENT_SYNTAX["sh"]).stateful)


class TestFindCommentEnd(unittest.TestCase):
    def test_should_return_the_end_of_the_containing_span(self):
        spans = [(2, 5), (9, 12)]

        self.assertEqual(5, find_comment_end(spans, 2))
        self.assertEqual(5, find_comment_end(spans, 4))
        self.assertEqual(12, find_comment_end(spans, 10))

    def test_should_return_none_outside_the_spans(self):
        spans = [(2, 5)]

        self.assertIsNone(find_comment_end(spans, 1))
        self.assertIsNone(find_comment_end(spans, 5))
        self.assertIsNone(find_comment_end([], 0))


class TestCommentIndex(unittest.TestCase):
    def test_stateful_syntax_should_track_blocks_across_lines(self):
        index = CommentIndex(COMMENT_SYNTAX["c"], ["a", "/*", " * x", "*/ y", "z // w"])

        self.assertIsNone(index.comment_end(1, 0))
        self.assertEqual(4, index.comment_end(3, 1))
        self.assertIsNone(index.comment_end(4, 3))
        self.assertEqual(6, index.comment_end(5, 4))

    def test_lines_can_be_asked_in_any_order(self):
        index = CommentIndex(COMMENT_SYNTAX["c"], ["/*", "x", "*/ y"])

        self.assertEqual(1, index.comment_end(2, 0))
        self.assertIsNone(index.comment_end(3, 3))
        self.assertEqual(1, index.comment_end(2, 0))

    def test_stateless_syntax_should_look_at_each_line_alone(self):
        index = CommentIndex(COMMENT_SYNTAX["sh"], ["echo a # x", "b"])

        self.assertEqual(10, index.comment_end(1, 8))
        self.assertIsNone(index.comment_end(1, 2))
        self.assertIsNone(index.comment_end(2, 0))


def _item_tuples(path: str, require_comment: bool = True) -> list:
    settings = ScanSettings(paths=[path], extensions=COMMON_EXTENSIONS, tags=ALL_TAGS, require_comment=require_comment)
    result = scan(settings, today=date(2025, 6, 15))

    return [(item.file, item.line, item.tag, item.message, item.author, item.author_source, item.due_date) for item in result.items]


def expected(file: str, line: int, tag: str, message: str, author: Optional[str] = None, due: Optional[date] = None) -> tuple:
    return (file, line, tag, message, author, "annotation" if author else "unknown", due)


D1 = date(2030, 1, 2)
D2 = date(2031, 3, 4)

EXPECTED_FIXTURE_ITEMS = [
    expected("Sample.java", 1, "TODO", "plain tag with a colon"),
    expected("Sample.java", 3, "FIXME", "javadoc line", "alice"),
    expected("Sample.java", 4, "HACK", "javadoc with date and user", "bob", D1),
    expected("Sample.java", 7, "XXX", "trailing comment"),
    expected("sample.go", 3, "TODO", "plain tag with an owner", "alice"),
    expected("sample.go", 4, "FIXME", "block comment", None, D1),
    expected("sample.go", 5, "HACK", "trailing comment"),
    expected("sample.go", 12, "XXX", "in a block comment", "bob"),
    expected("sample.html", 2, "TODO", "plain tag with a colon"),
    expected("sample.html", 6, "FIXME", "multi-line comment", "alice", D1),
    expected("sample.html", 7, "XXX", "second line"),
    expected("sample.html", 9, "HACK", "trailing comment"),
    expected("sample.js", 1, "TODO", "plain tag with a colon"),
    expected("sample.js", 2, "FIXME", "block comment on one line", "alice", D1),
    expected("sample.js", 4, "HACK", "inside a block comment", "bob"),
    expected("sample.js", 5, "XXX", "on a line that starts with a star", None, D2),
    expected("sample.js", 8, "TODO", "trailing comment"),
    expected("sample.md", 5, "TODO", "plain tag with a colon"),
    expected("sample.md", 12, "HACK", "after the fence", "alice", D1),
    expected("sample.py", 3, "TODO", "plain tag with a colon"),
    expected("sample.py", 4, "FIXME", "date and user", "alice", D1),
    expected("sample.py", 5, "HACK", "owner in parentheses", "bob"),
    expected("sample.py", 6, "XXX", "owner and date", "carol", D2),
    expected("sample.py", 10, "TODO", "trailing comment"),
    expected("sample.py", 11, "FIXME", "after a string with the tag"),
    expected("sample.py", 17, "TODO", "after an escaped quote"),
    expected("sample.rs", 1, "TODO", "plain tag with a colon"),
    expected("sample.rs", 2, "FIXME", "doc comment", "alice"),
    expected("sample.rs", 4, "HACK", "trailing comment after a lifetime"),
    expected("sample.rs", 7, "XXX", "", "bob", D1),
    expected("sample.sql", 1, "TODO", "plain tag with a colon"),
    expected("sample.sql", 2, "FIXME", "trailing comment", "alice"),
    expected("sample.sql", 3, "HACK", "", "bob", D1),
    expected("sample.sql", 4, "XXX", "second line of a block comment"),
    expected("sample.ts", 1, "TODO", "plain tag with a colon"),
    expected("sample.ts", 3, "FIXME", "documented field", "alice"),
    expected("sample.ts", 4, "HACK", "trailing comment", None, D1),
    expected("sample.ts", 8, "XXX", "block comment without stars", "bob"),
    expected("sample.yaml", 1, "TODO", "plain tag with a colon"),
    expected("sample.yaml", 4, "FIXME", "trailing comment", "alice", D1),
    expected("sample.yaml", 6, "HACK", "", "bob"),
]


class TestLanguageFixtures(unittest.TestCase):
    def test_fixtures_should_cover_at_least_six_languages(self):
        extensions = {name.rsplit(".", 1)[-1] for name in os.listdir(FIXTURES_DIR)}

        self.assertGreaterEqual(len(extensions), 6)

    def test_fixtures_should_produce_exactly_the_expected_items_with_require_comment(self):
        self.assertEqual(sorted(EXPECTED_FIXTURE_ITEMS, key=lambda t: (t[0], t[1])), _item_tuples(FIXTURES_DIR))

    def test_every_tag_and_every_form_should_be_covered_by_every_fixture_language(self):
        items = _item_tuples(FIXTURES_DIR)

        self.assertEqual(set(ALL_TAGS), {item[2] for item in items})
        self.assertEqual(10, len({item[0] for item in items}))
        self.assertTrue(any(item[4] and item[6] for item in items))  # TAG {date} @user or TAG(owner) {date}

    def test_without_require_comment_the_decoys_should_be_reported_too(self):
        lines = {(item[0], item[1]) for item in _item_tuples(FIXTURES_DIR, require_comment=False)}

        for decoy in [
            ("sample.py", 1),
            ("sample.py", 8),
            ("sample.py", 9),
            ("sample.py", 16),
            ("sample.js", 7),
            ("sample.js", 10),
            ("sample.md", 3),
            ("sample.md", 8),
            ("sample.html", 3),
        ]:
            self.assertIn(decoy, lines)
        self.assertNotIn(("sample.py", 12), lines)  # `todonotifier` is never a tag

    def test_decoys_should_never_be_reported_with_require_comment(self):
        lines = {(item[0], item[1]) for item in _item_tuples(FIXTURES_DIR)}

        for decoy in [
            ("sample.py", 1),
            ("sample.py", 8),
            ("sample.py", 9),
            ("sample.py", 16),
            ("sample.js", 7),
            ("sample.js", 10),
            ("sample.go", 8),
            ("Sample.java", 9),
        ]:
            self.assertNotIn(decoy, lines)
        self.assertNotIn(("sample.md", 8), lines)
        self.assertNotIn(("sample.md", 9), lines)
