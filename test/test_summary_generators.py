import unittest
from datetime import datetime, timedelta

from models import POSITION, TODO, USER
from summary_generators import (
    ByModuleSummaryGenerator,
    ExpiredTodosByUserSummaryGenerator,
    UpcomingWeekTodosByUserSummaryGenerator,
)


class TestByModuleSummaryGenerator(unittest.TestCase):
    def setUp(self):
        self._dummy_msg = "unittest-dummy-msg"
        self._dummy_user_name = "unittest-dummy-user-name"
        self._dummy_user = USER(self._dummy_user_name)
        self._dummy_completion_date_str = "2022-09-22"
        self._dummy_module = "unittest-module"
        self._dummy_line_no = 1
        self._dummy_position = POSITION(self._dummy_line_no)
        self._dummy_todo_obj = TODO(self._dummy_msg, self._dummy_user, self._dummy_completion_date_str, self._dummy_module, self._dummy_position)
        self._dummy_all_todo_objs = {self._dummy_module: [self._dummy_todo_obj, self._dummy_todo_obj]}
        self._by_module_summary_generator = ByModuleSummaryGenerator()

    def test_generate_summary(self):
        expected_value = {
            self._dummy_module: [
                [self._dummy_user_name, None, self._dummy_msg, self._dummy_line_no, "2022-09-22 00:00:00"],
                [self._dummy_user_name, None, self._dummy_msg, self._dummy_line_no, "2022-09-22 00:00:00"],
            ]
        }

        self._by_module_summary_generator.generate_summary(self._dummy_all_todo_objs)

        self.assertEqual(expected_value, self._by_module_summary_generator.container)


class TestExpiredTodosByUserSummaryGenerator(unittest.TestCase):
    def setUp(self):
        self._dummy_msg = "unittest-dummy-msg"
        self._dummy_user_name = "unittest-dummy-user-name"
        self._dummy_user = USER(self._dummy_user_name)
        self._dummy_completion_date_str1 = "2020-09-22"
        self._dummy_completion_date_str2 = str((datetime.today() + timedelta(days=2)).date())
        self._dummy_module = "unittest-module"
        self._dummy_line_no = 1
        self._dummy_position = POSITION(self._dummy_line_no)
        self._dummy_todo_obj1 = TODO(self._dummy_msg, self._dummy_user, self._dummy_completion_date_str1, self._dummy_module, self._dummy_position)
        self._dummy_todo_obj2 = TODO(self._dummy_msg, self._dummy_user, self._dummy_completion_date_str2, self._dummy_module, self._dummy_position)
        self._dummy_all_todo_objs = {self._dummy_module: [self._dummy_todo_obj1, self._dummy_todo_obj1, self._dummy_todo_obj2]}
        self._expired_todos_by_user_summary_generator = ExpiredTodosByUserSummaryGenerator()

    def test_generate_summary(self):
        expected_value = {
            self._dummy_user.user_name: [
                [None, self._dummy_msg, self._dummy_module, self._dummy_line_no, "2020-09-22 00:00:00"],
                [None, self._dummy_msg, self._dummy_module, self._dummy_line_no, "2020-09-22 00:00:00"],
            ]
        }

        self._expired_todos_by_user_summary_generator.generate_summary(self._dummy_all_todo_objs)

        self.assertEqual(expected_value, self._expired_todos_by_user_summary_generator.container)


class TestUpcomingWeekTodosByUserSummaryGenerator(unittest.TestCase):
    def setUp(self):
        self._dummy_msg = "unittest-dummy-msg"
        self._dummy_user_name = "unittest-dummy-user-name"
        self._dummy_user = USER(self._dummy_user_name)
        self._dummy_completion_date_str1 = str((datetime.today() + timedelta(days=2)).date())
        self._dummy_completion_date_str2 = str((datetime.today() + timedelta(days=10)).date())
        self._dummy_module = "unittest-module"
        self._dummy_line_no = 1
        self._dummy_position = POSITION(self._dummy_line_no)
        self._dummy_todo_obj1 = TODO(self._dummy_msg, self._dummy_user, self._dummy_completion_date_str1, self._dummy_module, self._dummy_position)
        self._dummy_todo_obj2 = TODO(self._dummy_msg, self._dummy_user, self._dummy_completion_date_str2, self._dummy_module, self._dummy_position)
        self._dummy_all_todo_objs = {self._dummy_module: [self._dummy_todo_obj1, self._dummy_todo_obj1, self._dummy_todo_obj2]}
        self._upcoming_week_todos_by_user_summary_generator = UpcomingWeekTodosByUserSummaryGenerator()
        self.maxDiff = None

    def test_generate_summary(self):
        expected_completion_date = str((datetime.today() + timedelta(days=2)).date().strftime("%Y-%m-%d %H:%M:%S"))
        expected_value = {
            self._dummy_user.user_name: [
                [None, self._dummy_msg, self._dummy_module, self._dummy_line_no, expected_completion_date],
                [None, self._dummy_msg, self._dummy_module, self._dummy_line_no, expected_completion_date],
            ]
        }

        self._upcoming_week_todos_by_user_summary_generator.generate_summary(self._dummy_all_todo_objs)

        self.assertEqual(expected_value, self._upcoming_week_todos_by_user_summary_generator.container)


if __name__ == "__main__":
    unittest.main()
