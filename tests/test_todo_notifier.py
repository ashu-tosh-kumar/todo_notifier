import os
import tempfile
import unittest
from typing import Dict, List
from unittest.mock import patch

from todonotifier.constants import DEFAULT_COMPLETION_DATE, UNKNOWN_USER_NAME
from todonotifier.models import POSITION, TODO, USER
from todonotifier.todo_notifier import (
    _parse_todo_from_match,
    parse_files_for_todo_items,
)


class UnitTestCustomException(Exception):
    """Raised to custom fail a test case where we have a custom logic of asserting test
    pass/fail
    """

    pass


class TestParseFilesForTodoItems(unittest.TestCase):
    def _compare_todos(self, expected_value: Dict[str, List[TODO]], actual_value: Dict[str, List[TODO]]) -> bool:
        if (expected_value_set := set(expected_value.keys())) != (actual_value_set := set(actual_value.keys())):
            raise UnitTestCustomException(f"Keys in expected_value: {expected_value_set} is different than keys in actual value: {actual_value_set}")

        for module in actual_value:
            if (expected_value_num := len(expected_value[module])) != (actual_value_num := len(actual_value[module])):
                raise UnitTestCustomException(f"Number of modules in different in expected_value: {expected_value_num} and actual_value: {actual_value_num}")

        for module in actual_value:
            for expected_todo, actual_todo in zip(expected_value[module], actual_value[module]):
                if expected_todo.msg != actual_todo.msg:
                    raise UnitTestCustomException(f"Expected message: {expected_todo.msg} doesn't match with actual message: {actual_todo.msg}")

                if expected_todo.user.user_name != actual_todo.user.user_name:
                    raise UnitTestCustomException(f"Expected user_name: {expected_todo.user_name} doesn't match with actual user_name: {actual_todo.user_name}")

                if expected_todo.completion_date != actual_todo.completion_date:
                    raise UnitTestCustomException(
                        f"Expected completion_date: {expected_todo.completion_date} doesn't match with actual completion_date: {actual_todo.completion_date}"
                    )

                if expected_todo.module != actual_todo.module:
                    raise UnitTestCustomException(f"Expected module: {expected_todo.module} doesn't match with actual module: {actual_todo.module}")

                if expected_todo.position.line_no != actual_todo.position.line_no:
                    raise UnitTestCustomException(
                        f"Expected line_no: {expected_todo.position.line_no} doesn't match with actual line_no: {actual_todo.position.line_no}"
                    )

    def test_parse_files_for_todo_items_should_parse_todo_items(self):
        dummy_files = ["tests/sample_test_file.py"]
        project_parent_dir = "tests"  # Important to keep it same as tests directory
        expected_value = {
            "sample_test_file.py": [
                TODO(
                    "some-message-21f886ac-cc41-452b-9a53-3cfd56446341",
                    USER(UNKNOWN_USER_NAME),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(4),
                ),
                TODO(
                    "some-message-0e4fc40f-f7c6-40bb-a6db-a51e158f4cc4",
                    USER(UNKNOWN_USER_NAME),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(5),
                ),
                TODO("some-message-0b0e31cc-e2e8-4d54-9684-ddf95958d7dc", USER(UNKNOWN_USER_NAME), "2022-05-01", "sample_test_file.py", POSITION(6)),
                TODO("some-message-f53d566a-1fea-422b-9ac6-41a171977ac2", USER(UNKNOWN_USER_NAME), "2022-05-02", "sample_test_file.py", POSITION(7)),
                TODO("some-message-4ef1fe34-ab50-4cc1-8abc-e550dee3be3f", USER("ashutosh"), "2022-05-03", "sample_test_file.py", POSITION(8)),
                TODO("some-message-2af38dcf-29e4-4104-9921-6e654f27a6ca", USER("ashutosh"), "2022-05-04", "sample_test_file.py", POSITION(9)),
                TODO(
                    "some-message-f264a5e7-5758-4145-9513-c5c52c20a9fa TODO some-message-43498a94-6b13-41e8-ac2e-05e84fc6c895",
                    USER(UNKNOWN_USER_NAME),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(10),
                ),
                TODO(
                    "{2022-05-03 @ashutosh some-message-faa74c20-d4c2-444e-9fa0-7f202cb10b44",
                    USER(UNKNOWN_USER_NAME),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(11),
                ),
                TODO(
                    "2022-05-03} @ashutosh some-message-63448d77-07fb-4bc1-bf80-2d94ab902f5f",
                    USER(UNKNOWN_USER_NAME),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(12),
                ),
                TODO(
                    "2022-05-03 @ashutosh some-message-11c6c4a1-5231-47ec-8cc6-11de055ce441",
                    USER(UNKNOWN_USER_NAME),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(13),
                ),
                TODO(
                    "some-message-e1922c58-f6d0-49cf-8005-076c18556f13",
                    USER("ashutosh"),
                    "2022-05",
                    "sample_test_file.py",
                    POSITION(14),
                ),
                TODO(
                    "some-message-1f1d31c2-2a40-4d02-9bcd-b099de963450",
                    USER("ashutosh"),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(15),
                ),
                TODO(
                    "some-message-e8d9c141-f082-44a3-b828-6f83606e9d24",
                    USER("ashutosh"),
                    "05-03",
                    "sample_test_file.py",
                    POSITION(16),
                ),
                TODO(
                    "some-message-1a4a2281-40b0-4df0-942e-8d1a9d74ad45",
                    USER("ashutosh"),
                    "2022",
                    "sample_test_file.py",
                    POSITION(17),
                ),
                TODO(
                    "some-message-c3757bc8-571f-4717-bf16-b102a16d36f5",
                    USER("ashutosh"),
                    "03",
                    "sample_test_file.py",
                    POSITION(18),
                ),
                TODO(
                    "some-message-8882c77a-ba29-40dc-9bcd-fb7d19ce7d49",
                    USER("ashutosh"),
                    "13",
                    "sample_test_file.py",
                    POSITION(19),
                ),
                TODO(
                    "some-message-6d3d70fd-0dfc-46d6-a1ab-2303c292701c",
                    USER("ashutosh"),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(20),
                ),
                TODO(
                    "some-message-5c795770-18f7-4104-a5d5-908af39a6686",
                    USER(UNKNOWN_USER_NAME),
                    "2022-05-08",
                    "sample_test_file.py",
                    POSITION(21),
                ),
                TODO("", USER("ashutosh"), "2022-05-09", "sample_test_file.py", POSITION(22)),
                TODO(
                    "some-@message-726c9e2d-13bf-4309-9b3c-530c7b3404b7",
                    USER(UNKNOWN_USER_NAME),
                    "2022-05-09",
                    "sample_test_file.py",
                    POSITION(23),
                ),
                TODO(
                    "some-message-27cdb8bc-fffe-40df-a212-76452cbdb47c {2022-05-09} some-@message-db1d606f-88d3-474e-890e-8e9c34f093d0",
                    USER(UNKNOWN_USER_NAME),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(24),
                ),
                TODO("", USER(UNKNOWN_USER_NAME), "2022-05-09", "sample_test_file.py", POSITION(25)),
                TODO("", USER(UNKNOWN_USER_NAME), "2022-05-10", "sample_test_file.py", POSITION(26)),
                TODO("", USER("ashutosh"), DEFAULT_COMPLETION_DATE, "sample_test_file.py", POSITION(27)),
                TODO("ashu@tosh", USER(UNKNOWN_USER_NAME), DEFAULT_COMPLETION_DATE, "sample_test_file.py", POSITION(28)),
                TODO(
                    "some-message-35d43513-00df-4c3d-8569-b72d8983f62d",
                    USER("ashutosh"),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(29),
                ),
                TODO("", USER(UNKNOWN_USER_NAME), DEFAULT_COMPLETION_DATE, "sample_test_file.py", POSITION(30)),
                TODO(
                    "some-message-1621700c-bf13-49b7-ab63-e544d570f341",
                    USER(UNKNOWN_USER_NAME),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(31),
                ),
                TODO("{2022-05-09}", USER("ashutosh"), DEFAULT_COMPLETION_DATE, "sample_test_file.py", POSITION(32)),
                TODO(
                    "some-message-40b01cd7-3480-4f9b-9d0c-98ad297cf591 @ashutosh {2022-05-09}",
                    USER(UNKNOWN_USER_NAME),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(33),
                ),
                TODO(
                    "{2022-05-09} some-message-afc38fb9-5a40-470b-9e1c-d4bacc451727",
                    USER("ashutosh"),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(34),
                ),
                TODO("TODO", USER(UNKNOWN_USER_NAME), DEFAULT_COMPLETION_DATE, "sample_test_file.py", POSITION(35)),
                TODO(
                    "TODO {2022-05-11} some-message-7c2a62cb-8037-46cb-bdee-76dd0791d747",
                    USER("ashutosh"),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(36),
                ),
                TODO(
                    "# TODO {2022-05-12} some-message-d2cad1b4-8881-4687-a38d-2d14fbfd1306",
                    USER("ashutosh"),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(37),
                ),
                TODO("", USER("ashutosh"), DEFAULT_COMPLETION_DATE, "sample_test_file.py", POSITION(38)),
                TODO('some-message-a1571791-50fe-4863-8a06-c2d4d921897c"""', USER("ashutosh"), "2022-05-05", "sample_test_file.py", POSITION(42)),
                TODO(":", USER(UNKNOWN_USER_NAME), DEFAULT_COMPLETION_DATE, "sample_test_file.py", POSITION(47)),
                TODO('some-message-ffe6e2ca-c78b-4231-b278-06e3de8aa9c6"""', USER("ashutosh"), "2022-05-06", "sample_test_file.py", POSITION(51)),
                TODO(
                    "some-message-a59653a5-3fae-450a-8289-0c4433e27535",
                    USER("ashutosh"),
                    "2022-05-07",
                    "sample_test_file.py",
                    POSITION(54),
                ),
            ]
        }

        actual_value = parse_files_for_todo_items(project_parent_dir, dummy_files, False)

        self._compare_todos(expected_value, actual_value)

    def test_parse_files_for_todo_items_should_consider_case_insensitive_values_if_set(self):
        dummy_files = ["tests/sample_test_file2.py"]
        project_parent_dir = "tests"  # Important to keep it same as tests directory
        expected_value = {
            "sample_test_file2.py": [
                TODO(
                    "some-message-21f886ac-cc41-452b-9a53-3cfd56446341",
                    USER(UNKNOWN_USER_NAME),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file2.py",
                    POSITION(4),
                ),
                TODO(
                    "some-message-301ac105-3afe-4d1e-adea-176a17e07393",
                    USER(UNKNOWN_USER_NAME),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file2.py",
                    POSITION(5),
                ),
                TODO(
                    "some-message-0e4fc40f-f7c6-40bb-a6db-a51e158f4cc4",
                    USER(UNKNOWN_USER_NAME),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file2.py",
                    POSITION(6),
                ),
                TODO(
                    "some-message-e5f94208-f4c8-4fee-bb9e-b7d9e00a4600",
                    USER(UNKNOWN_USER_NAME),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file2.py",
                    POSITION(7),
                ),
            ]
        }

        actual_value = parse_files_for_todo_items(project_parent_dir, dummy_files, True)

        self._compare_todos(expected_value, actual_value)

    @patch("todonotifier.todo_notifier.compute_line_and_pos_given_span")
    def test_parse_files_for_todo_items_should_handle_exception_in_parsing_todo_items(self, stub_compute_line_and_pos_given_span):
        dummy_files = ["tests/sample_test_file2.py"]
        project_parent_dir = "tests"  # Important to keep it same as tests directory
        stub_compute_line_and_pos_given_span.side_effect = [
            4,
            Exception("unittest-compute-line-and-pos-given-span-exception"),
        ]  # First time letting it call actual function and second time raising an exception
        expected_value = {
            "sample_test_file2.py": [
                TODO(
                    "some-message-21f886ac-cc41-452b-9a53-3cfd56446341",
                    USER(UNKNOWN_USER_NAME),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file2.py",
                    POSITION(4),
                ),
            ]
        }

        actual_value = parse_files_for_todo_items(project_parent_dir, dummy_files, False)

        self._compare_todos(expected_value, actual_value)

    @patch("todonotifier.todo_notifier.compute_file_line_no_to_chars_map")
    def test_parse_files_for_todo_items_should_handle_exception_in_parsing_file(self, stub_compute_file_line_no_to_chars_map):
        dummy_files = ["tests/sample_test_file2.py"]
        project_parent_dir = "tests"  # Important to keep it same as tests directory
        stub_compute_file_line_no_to_chars_map.side_effect = (Exception("unittest-compute-file-line-no-to-chars-map-exception"),)
        expected_value = {"sample_test_file2.py": []}

        actual_value = parse_files_for_todo_items(project_parent_dir, dummy_files, False)

        self._compare_todos(expected_value, actual_value)

    @patch("todonotifier.todo_notifier.STREAMING_THRESHOLD_BYTES", 0)
    @patch("todonotifier.todo_notifier._parse_file_in_memory")
    def test_parse_files_for_todo_items_should_use_streaming_parser_for_large_files(self, stub_parse_file_in_memory):
        dummy_files = ["tests/sample_test_file.py"]
        project_parent_dir = "tests"

        actual_value = parse_files_for_todo_items(project_parent_dir, dummy_files, False)

        stub_parse_file_in_memory.assert_not_called()
        self.assertEqual(len(actual_value["sample_test_file.py"]), len(self._in_memory_todos(dummy_files, project_parent_dir, False)["sample_test_file.py"]))

    def _in_memory_todos(self, files: List[str], project_parent_dir: str, ignore_todo_case: bool) -> Dict[str, List[TODO]]:
        return parse_files_for_todo_items(project_parent_dir, files, ignore_todo_case)

    @patch("todonotifier.todo_notifier.STREAMING_THRESHOLD_BYTES", 0)
    def test_parse_files_for_todo_items_streaming_parser_should_match_in_memory_parser(self):
        dummy_files = ["tests/sample_test_file.py", "tests/sample_test_file2.py"]
        project_parent_dir = "tests"

        for ignore_todo_case in (False, True):
            streamed_value = parse_files_for_todo_items(project_parent_dir, dummy_files, ignore_todo_case)
            with patch("todonotifier.todo_notifier.STREAMING_THRESHOLD_BYTES", 10**9):
                in_memory_value = parse_files_for_todo_items(project_parent_dir, dummy_files, ignore_todo_case)

            self._compare_todos(in_memory_value, streamed_value)

    @patch("todonotifier.todo_notifier.STREAMING_THRESHOLD_BYTES", 0)
    @patch("todonotifier.todo_notifier._parse_todo_from_match")
    def test_parse_files_for_todo_items_streaming_parser_should_handle_exception_in_parsing_todo_items(self, stub_parse_todo_from_match):
        dummy_files = ["tests/sample_test_file2.py"]
        project_parent_dir = "tests"
        stub_parse_todo_from_match.side_effect = Exception("unittest-parse-todo-exception")
        expected_value = {"sample_test_file2.py": []}

        actual_value = parse_files_for_todo_items(project_parent_dir, dummy_files, False)

        self._compare_todos(expected_value, actual_value)

    @patch("todonotifier.todo_notifier.STREAMING_THRESHOLD_BYTES", 0)
    @patch("builtins.open")
    def test_parse_files_for_todo_items_streaming_parser_should_handle_exception_in_reading_file(self, stub_open):
        dummy_files = ["tests/sample_test_file2.py"]
        project_parent_dir = "tests"
        stub_open.side_effect = Exception("unittest-open-exception")
        expected_value = {"sample_test_file2.py": []}

        actual_value = parse_files_for_todo_items(project_parent_dir, dummy_files, False)

        self._compare_todos(expected_value, actual_value)


class DetectionTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = self._tmp.name

    def _write(self, name: str, content) -> str:
        path = os.path.join(self.tmp, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb" if isinstance(content, bytes) else "w", **({} if isinstance(content, bytes) else {"encoding": "utf-8"})) as f:
            f.write(content)
        return path

    def _parse_text(self, name: str, text, ignore_case: bool = False, **kwargs) -> List[TODO]:
        """Parses with the in-memory parser and checks that the streaming parser agrees"""
        path = self._write(name, text)
        in_memory = parse_files_for_todo_items(self.tmp, [path], ignore_case, **kwargs)
        with patch("todonotifier.todo_notifier.STREAMING_THRESHOLD_BYTES", 0):
            streamed = parse_files_for_todo_items(self.tmp, [path], ignore_case, **kwargs)

        summary = {file: [self._summary(todo) for todo in todos] for file, todos in in_memory.items()}
        self.assertEqual(summary, {file: [self._summary(todo) for todo in todos] for file, todos in streamed.items()})
        return in_memory.get(name, [])

    @staticmethod
    def _summary(todo: TODO) -> tuple:
        return (todo.tag, todo.msg, todo.user.user_name, str(todo.completion_date), todo.position.line_no)


class TestDetectionRegressions(DetectionTestCase):
    """The false positives of the known-defects table. Each line used to be reported as a TODO"""

    def test_import_of_todonotifier_should_not_be_a_todo_with_ignore_case(self):
        todos = self._parse_text("a.py", "from todonotifier.config import X\n", ignore_case=True)

        self.assertEqual([], todos)

    def test_identifier_with_todo_prefix_should_not_be_a_todo(self):
        todos = self._parse_text("a.py", "TODO_REGEX_PATTERN = r'TODO_X'\n")

        self.assertEqual([], todos)

    def test_todo_in_a_string_should_be_ignored_when_a_comment_is_required(self):
        todos = self._parse_text("a.py", 'print("TODO list")\n', require_comment=True)

        self.assertEqual([], todos)


class TestWordBoundaries(DetectionTestCase):
    def test_tags_inside_words_should_not_match(self):
        text = "TODO_X\nXTODO\nTODOS\ntodo_list = 1\nMY_TODO\nTODO1\n"

        self.assertEqual([], self._parse_text("a.txt", text, ignore_case=True))

    def test_tag_followed_by_punctuation_should_match(self):
        text = "TODO: a\nTODO(b)\nTODO-c\nTODO. d\n[TODO] e\nx TODO\nTODO\n"

        todos = self._parse_text("a.txt", text)

        self.assertEqual([1, 2, 3, 4, 5, 6, 7], [todo.position.line_no for todo in todos])

    def test_ignore_case_should_still_find_other_cases_on_a_word_boundary(self):
        todos = self._parse_text("a.py", "# todo a\n# Todo b\n# todonotifier\n", ignore_case=True)

        self.assertEqual([("TODO", "a"), ("TODO", "b")], [(todo.tag, todo.msg) for todo in todos])

    def test_case_sensitive_search_should_not_match_other_cases(self):
        self.assertEqual([], self._parse_text("a.py", "# todo a\n# Todo b\n"))


class TestTags(DetectionTestCase):
    def test_default_should_be_todo_only(self):
        todos = self._parse_text("a.py", "# TODO a\n# FIXME b\n")

        self.assertEqual([("TODO", "a")], [(todo.tag, todo.msg) for todo in todos])

    def test_several_tags_should_be_reported_with_their_tag(self):
        todos = self._parse_text("a.py", "# TODO a\n# FIXME b\n# HACK c\n# XXX d\n# NOTE e\n", tags=["TODO", "FIXME", "HACK", "XXX"])

        self.assertEqual([("TODO", "a"), ("FIXME", "b"), ("HACK", "c"), ("XXX", "d")], [(todo.tag, todo.msg) for todo in todos])

    def test_date_and_user_should_work_after_any_tag(self):
        todos = self._parse_text("a.py", "# FIXME {2030-01-02} @alice msg\n# XXX @bob {2030-02-03} msg\n", tags=["FIXME", "XXX"])

        self.assertEqual(
            [("FIXME", "msg", "alice", "2030-01-02", 1), ("XXX", "{2030-02-03} msg", "bob", "9999-12-25", 2)],
            [self._summary(todo) for todo in todos],
        )

    def test_longest_tag_should_be_preferred(self):
        todos = self._parse_text("a.py", "# FIXME a\n# FIX b\n", tags=["FIX", "FIXME"])

        self.assertEqual([("FIXME", "a"), ("FIX", "b")], [(todo.tag, todo.msg) for todo in todos])

    def test_tags_should_be_escaped(self):
        todos = self._parse_text("a.py", "# T.DO a\n# TXDO b\n# C++ c\n", tags=["T.DO", "C++"])

        self.assertEqual([("T.DO", "a"), ("C++", "c")], [(todo.tag, todo.msg) for todo in todos])

    def test_tags_should_be_reported_as_configured_when_ignoring_case(self):
        todos = self._parse_text("a.py", "# fixme a\n# Todo b\n", ignore_case=True, tags=["TODO", "fixme", "todo"])

        self.assertEqual([("fixme", "a"), ("TODO", "b")], [(todo.tag, todo.msg) for todo in todos])

    def test_a_single_tag_given_as_a_string_should_work(self):
        todos = self._parse_text("a.py", "# FIXME a\n", tags="FIXME")

        self.assertEqual(["FIXME"], [todo.tag for todo in todos])

    def test_surrounding_whitespace_of_a_tag_should_be_ignored(self):
        todos = self._parse_text("a.py", "# FIXME a\n", tags=[" FIXME "])

        self.assertEqual(["FIXME"], [todo.tag for todo in todos])

    def test_invalid_tags_should_raise_before_any_file_is_read(self):
        path = self._write("a.py", "# TODO a\n")

        for tags in ([], [""], ["  "], [None], [1]):
            with self.assertRaises(ValueError, msg=str(tags)):
                parse_files_for_todo_items(self.tmp, [path], False, tags)

    def test_positional_arguments_should_keep_working(self):
        path = self._write("a.py", "# TODO a\n# FIXME b\n")

        todos = parse_files_for_todo_items(self.tmp, [path], False, ["FIXME"], False)["a.py"]

        self.assertEqual(["FIXME"], [todo.tag for todo in todos])

    def test_legacy_todo_should_default_its_tag(self):
        self.assertEqual("TODO", TODO("m", USER("u"), "", "a.py", POSITION(1)).tag)
        self.assertEqual("FIXME", TODO("m", USER("u"), "", "a.py", POSITION(1), tag="FIXME").tag)


class TestExtendedSyntax(DetectionTestCase):
    def _extended(self, text: str, **kwargs) -> List[tuple]:
        return [self._summary(todo) for todo in self._parse_text("a.py", text, extended_syntax=True, **kwargs)]

    def test_colon_after_the_tag_should_be_dropped(self):
        self.assertEqual([("TODO", "fix this", "JANE_DOE", "9999-12-25", 1)], self._extended("# TODO: fix this\n"))

    def test_owner_in_parentheses_should_be_the_user(self):
        self.assertEqual([("TODO", "fix", "ashu", "9999-12-25", 1)], self._extended("# TODO(ashu): fix\n"))

    def test_owner_and_date_should_combine(self):
        self.assertEqual([("FIXME", "msg", "ashu", "2025-01-01", 1)], self._extended("# FIXME(ashu) {2025-01-01} msg\n", tags=["FIXME"]))

    def test_colon_after_the_date_and_the_user_should_be_dropped(self):
        text = "# TODO {2025-01-01}: a\n# TODO @bob: b\n# TODO {2025-01-01} @bob: c\n# TODO(bob) {2025-01-01}: d\n# TODO: {2025-01-01} @bob e\n"

        self.assertEqual(
            [
                ("TODO", "a", "JANE_DOE", "2025-01-01", 1),
                ("TODO", "b", "bob", "9999-12-25", 2),
                ("TODO", "c", "bob", "2025-01-01", 3),
                ("TODO", "d", "bob", "2025-01-01", 4),
                ("TODO", "e", "bob", "2025-01-01", 5),
            ],
            self._extended(text),
        )

    def test_only_one_colon_should_be_dropped_per_position(self):
        self.assertEqual([("TODO", "a: b", "JANE_DOE", "9999-12-25", 1)], self._extended("# TODO: a: b\n"))

    def test_a_bare_tag_with_a_colon_should_give_an_empty_message(self):
        self.assertEqual([("TODO", "", "JANE_DOE", "9999-12-25", 1), ("TODO", "", "ashu", "9999-12-25", 2)], self._extended("# TODO:\n# TODO(ashu):\n"))

    def test_the_owner_in_parentheses_should_win_over_a_user(self):
        self.assertEqual([("TODO", "msg", "ashu", "9999-12-25", 1)], self._extended("# TODO(ashu) @bob msg\n"))

    def test_things_that_are_not_a_person_should_stay_in_the_message(self):
        text = "# TODO(#123): a\n# TODO(crbug.com/1): b\n# TODO(123): c\n# TODO(see below) d\n# TODO (ashu) e\n# TODO() f\n"

        self.assertEqual(
            ["(#123): a", "(crbug.com/1): b", "(123): c", "(see below) d", "(ashu) e", "() f"],
            [todo[1] for todo in self._extended(text)],
        )
        self.assertEqual({"JANE_DOE"}, {todo[2] for todo in self._extended(text)})

    def test_date_should_end_at_the_first_closing_brace(self):
        self.assertEqual([("TODO", "fix {braces}", "JANE_DOE", "2025-01-01", 1)], self._extended("# TODO {2025-01-01} fix {braces}\n"))

    def test_user_should_not_include_a_colon(self):
        self.assertEqual("ashu", self._extended("# TODO @ashu: x\n")[0][2])

    def test_legacy_syntax_should_keep_the_old_behavior(self):
        todos = self._parse_text("a.py", "# TODO: a\n# TODO(ashu): b\nclass TODO:\n")

        self.assertEqual([": a", "(ashu): b", ":"], [todo.msg for todo in todos])
        self.assertEqual({"JANE_DOE"}, {todo.user.user_name for todo in todos})

    def test_parse_todo_from_match_should_raise_if_there_is_no_tag(self):
        with self.assertRaises(ValueError):
            _parse_todo_from_match("nothing here", 0, "a.py", 1)


class TestRequireComment(DetectionTestCase):
    def test_tag_in_a_comment_should_be_reported(self):
        todos = self._parse_text("a.py", "x = 1  # TODO a\n# TODO b\n", require_comment=True)

        self.assertEqual(["a", "b"], [todo.msg for todo in todos])

    def test_decoy_before_the_real_tag_on_a_line_should_be_skipped(self):
        todos = self._parse_text("a.py", 'x = "TODO list"  # TODO real\n', require_comment=True)

        self.assertEqual([("TODO", "real", 1)], [(todo.tag, todo.msg, todo.position.line_no) for todo in todos])

    def test_only_the_first_tag_inside_a_comment_should_make_the_item(self):
        todos = self._parse_text("a.py", "# TODO a TODO b\n# FIXME c TODO d\n", require_comment=True, tags=["TODO", "FIXME"])

        self.assertEqual([("TODO", "a TODO b"), ("FIXME", "c TODO d")], [(todo.tag, todo.msg) for todo in todos])

    def test_block_comment_should_end_the_message(self):
        todos = self._parse_text("a.js", "/* TODO a */ var x; /* TODO b */\nvar y; // TODO c\n", require_comment=True)

        self.assertEqual(["a", "c"], [todo.msg for todo in todos])

    def test_multiline_block_comment_should_be_tracked_across_lines(self):
        text = "/**\n * TODO a\n   TODO b\n */\nvar TODO = 1;\nvar s = 2; // TODO c\n"

        todos = self._parse_text("a.js", text, require_comment=True)

        self.assertEqual([("a", 2), ("b", 3), ("c", 6)], [(todo.msg, todo.position.line_no) for todo in todos])

    def test_unknown_extension_should_match_anywhere(self):
        todos = self._parse_text("notes.xyz", 'x = "TODO list"\nTODO plain\n', require_comment=True)

        self.assertEqual(['list"', "plain"], [todo.msg for todo in todos])

    def test_file_without_an_extension_should_match_anywhere(self):
        self.assertEqual(1, len(self._parse_text("Makefile", "build: TODO\n", require_comment=True)))

    def test_without_the_option_a_tag_in_a_string_should_be_reported(self):
        self.assertEqual(1, len(self._parse_text("a.py", 'print("TODO list")\n')))

    def test_markdown_code_fence_should_not_be_reported(self):
        text = "TODO text\n```\n<!-- TODO in fence -->\n```\n<!-- TODO real -->\n"

        todos = self._parse_text("a.md", text, require_comment=True)

        self.assertEqual([("real", 5)], [(todo.msg, todo.position.line_no) for todo in todos])

    def test_file_without_a_trailing_newline_should_work(self):
        todos = self._parse_text("a.py", "# TODO last", require_comment=True)

        self.assertEqual(["last"], [todo.msg for todo in todos])

    def test_streaming_and_in_memory_parsers_should_agree_on_the_fixtures(self):
        fixtures = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "languages")
        files = [os.path.join(fixtures, name) for name in sorted(os.listdir(fixtures))]
        tags = ["TODO", "FIXME", "HACK", "XXX"]
        for require_comment in (False, True):
            in_memory = parse_files_for_todo_items(fixtures, files, False, tags, require_comment, extended_syntax=True)
            with patch("todonotifier.todo_notifier.STREAMING_THRESHOLD_BYTES", 0):
                streamed = parse_files_for_todo_items(fixtures, files, False, tags, require_comment, extended_syntax=True)

            self.assertGreater(sum(len(todos) for todos in in_memory.values()), 0)
            self.assertEqual(
                {file: [self._summary(todo) for todo in todos] for file, todos in in_memory.items()},
                {file: [self._summary(todo) for todo in todos] for file, todos in streamed.items()},
            )


class TestRobustness(DetectionTestCase):
    def test_binary_file_should_be_skipped_with_a_debug_log(self):
        binary = self._write("a.py", b"# TODO hidden\x00\x01\n")
        text = self._write("b.py", "# TODO shown\n")

        with self.assertLogs("todonotifier.todo_notifier", level="DEBUG") as logs:
            result = parse_files_for_todo_items(self.tmp, [binary, text], False)

        self.assertEqual(["b.py"], list(result))
        self.assertTrue(any("Skipping binary file" in line and "a.py" in line for line in logs.output))

    def test_nul_byte_after_the_first_8_kb_should_not_make_a_file_binary(self):
        path = self._write("a.py", b"# TODO shown\n" + b"#" * 9000 + b"\x00\n")

        result = parse_files_for_todo_items(self.tmp, [path], False)

        self.assertEqual(1, len(result["a.py"]))

    def test_invalid_utf8_should_be_replaced_not_fail(self):
        text = self._parse_text("a.py", b"# TODO caf\xe9 ok\n# TODO second\n")

        self.assertEqual(["caf\ufffd ok", "second"], [todo.msg for todo in text])

    def test_utf8_should_be_read_regardless_of_the_locale(self):
        todos = self._parse_text("a.py", "# TODO \u00fcber \u2603\n")

        self.assertEqual(["\u00fcber \u2603"], [todo.msg for todo in todos])

    def test_trailing_whitespace_should_not_be_part_of_the_message(self):
        todos = self._parse_text("a.py", "# TODO msg   \n")

        self.assertEqual(["msg"], [todo.msg for todo in todos])

    def test_failing_comment_detection_should_be_logged_and_skipped(self):
        path = self._write("a.py", "# TODO a\n")

        with patch("todonotifier.todo_notifier.CommentIndex", side_effect=Exception("boom")):
            result = parse_files_for_todo_items(self.tmp, [path], False, require_comment=True)

        self.assertEqual({"a.py": []}, result)

    def test_failing_comment_detection_should_be_logged_and_skipped_when_streaming(self):
        path = self._write("a.py", "# TODO a\n")

        with patch("todonotifier.todo_notifier.STREAMING_THRESHOLD_BYTES", 0), patch("todonotifier.todo_notifier.CommentLexer", side_effect=Exception("boom")):
            result = parse_files_for_todo_items(self.tmp, [path], False, require_comment=True)

        self.assertEqual({"a.py": []}, result)


if __name__ == "__main__":
    unittest.main()
