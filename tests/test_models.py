import unittest

from dateutil import parser

from todonotifier.constants import DEFAULT_COMPLETION_DATE
from todonotifier.models import POSITION, TODO, USER


class TestUser(unittest.TestCase):
    def setUp(self):
        self._dummy_user_name = "unittest-dummy-user-name"
        self._user = USER(self._dummy_user_name)

    def test_user_name_should_give_correct_user_name(self):
        self.assertEqual(self._dummy_user_name, self._user.user_name)

    def test___str__(self):
        expected_value = f"User: {repr(self._user)} user_name: {self._user.user_name}"
        self.assertEqual(expected_value, str(self._user))


class TestPosition(unittest.TestCase):
    def setUp(self):
        self._dummy_line_no = 1
        self._position = POSITION(self._dummy_line_no)

    def test_line_no_should_return_correct_line_no(self):
        self.assertEqual(self._dummy_line_no, self._position.line_no)

    def test___str__(self):
        expected_value = f"Position: {repr(self._position)} line_no: {self._position.line_no}"
        self.assertEqual(expected_value, str(self._position))


class TestTodo(unittest.TestCase):
    def setUp(self):
        self._dummy_msg = "unittest-dummy-msg"
        self._dummy_user_name = "unittest-dummy-user-name"
        self._dummy_user = USER(self._dummy_user_name)
        self._dummy_completion_date_str = "2022-09-22"
        self._dummy_module = "unittest-module"
        self._dummy_line_no = 1
        self._dummy_position = POSITION(self._dummy_line_no)
        self._todo = TODO(self._dummy_msg, self._dummy_user, self._dummy_completion_date_str, self._dummy_module, self._dummy_position)

    def test_todo_should_use_default_completion_date_if_any_issue_in_parser(self):
        expected_completion_date = parser.parse(DEFAULT_COMPLETION_DATE).date()
        todo = TODO(self._dummy_msg, self._dummy_user, None, self._dummy_module, self._dummy_position)

        self.assertEqual(expected_completion_date, todo.completion_date)

    def test_a_date_that_is_too_large_should_give_the_default_date_instead_of_raising(self):
        with self.assertLogs("todonotifier.models", level="WARNING"):
            todo = TODO(self._dummy_msg, self._dummy_user, "99999999999999999999", self._dummy_module, self._dummy_position)

        self.assertEqual(parser.parse(DEFAULT_COMPLETION_DATE).date(), todo.completion_date)

    def test_the_warning_for_a_bad_date_should_not_contain_raw_control_characters(self):
        # The date and the path come from a scanned file and the warning goes to a terminal
        with self.assertLogs("todonotifier.models", level="WARNING") as logs:
            TODO(self._dummy_msg, self._dummy_user, "\x1b]0;evil\x07 soon", "dir/\x1b[31mfile.py", self._dummy_position)

        message = logs.records[0].getMessage()
        self.assertNotIn("\x1b", message)
        self.assertNotIn("\x07", message)
        self.assertIn("\\x1b]0;evil\\x07 soon", message)
        self.assertIn("line 1", message)

    def test_msg_should_return_correct_msg(self):
        self.assertAlmostEqual(self._dummy_msg, self._todo.msg)

    def test_user_should_return_correct_user(self):
        self.assertAlmostEqual(self._dummy_user, self._todo.user)

    def test_completion_date_should_return_correct_completion_date(self):
        expected_value = parser.parse(self._dummy_completion_date_str).date()
        self.assertAlmostEqual(expected_value, self._todo.completion_date)

    def test_module_should_return_correct_module(self):
        self.assertAlmostEqual(self._dummy_module, self._todo.module)

    def test_tag_should_default_to_todo_and_not_change_the_str_representation(self):
        todo = TODO("msg", USER("u"), "", "m", POSITION(1))
        fixme = TODO("msg", USER("u"), "", "m", POSITION(1), tag="FIXME")

        self.assertEqual("TODO", todo.tag)
        self.assertEqual("FIXME", fixme.tag)
        self.assertTrue(str(fixme).startswith("TODO: "))
        self.assertNotIn("FIXME", str(fixme))

    def test_position_should_return_correct_position(self):
        self.assertAlmostEqual(self._dummy_position, self._todo.position)

    def test___str__(self):
        expected_value = f"""TODO: {repr(self._todo)} msg: {self._todo.msg} user: {str(self._todo.user)} completion date: {self._todo.completion_date} module: {self._todo.module} position: {str(self._todo.position)}"""  # noqa
        self.assertEqual(expected_value, str(self._todo))


if __name__ == "__main__":
    unittest.main()
