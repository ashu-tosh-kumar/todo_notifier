import unittest
from datetime import datetime, timedelta

from todonotifier.models import POSITION, TODO, USER
from todonotifier.summary_generators import (
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
                [self._dummy_user_name, self._dummy_msg, self._dummy_line_no, "2022-09-22"],
                [self._dummy_user_name, self._dummy_msg, self._dummy_line_no, "2022-09-22"],
            ]
        }

        self._by_module_summary_generator.generate_summary(self._dummy_all_todo_objs)

        self.assertEqual(expected_value, self._by_module_summary_generator.container)

    def test_generate_html(self):
        self._by_module_summary_generator._container = {
            self._dummy_module: [
                [self._dummy_user_name, self._dummy_msg, self._dummy_line_no, "2022-09-22"],
            ]
        }
        expected_value = f"""
            <h3>TODOs for module {self._dummy_module}</h3>
            <p>
                
            <table>
            <tr>
                <th>User Name</th>
                <th>Message</th>
                <th>Line No.</th>
                <th>Completion Date</th>
            </tr>
            
                <tr>
                    <td>{self._dummy_user_name}</td>
                    <td>{self._dummy_msg}</td>
                    <td>{self._dummy_line_no}</td>
                    <td>{"2022-09-22"}</td>
                </tr>
                
            </table>
            
            </p><br>
            """  # noqa: W293

        self._by_module_summary_generator.generate_html()

        self.assertEqual(expected_value, self._by_module_summary_generator.html)


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
                [self._dummy_msg, self._dummy_module, self._dummy_line_no, "2020-09-22"],
                [self._dummy_msg, self._dummy_module, self._dummy_line_no, "2020-09-22"],
            ]
        }

        self._expired_todos_by_user_summary_generator.generate_summary(self._dummy_all_todo_objs)

        self.assertEqual(expected_value, self._expired_todos_by_user_summary_generator.container)

    def test_generate_html(self):
        self._expired_todos_by_user_summary_generator._container = {
            self._dummy_user.user_name: [
                [self._dummy_msg, self._dummy_module, self._dummy_line_no, "2020-09-22"],
            ]
        }
        expected_value = f"""
            <h3>Expired TODOs for {self._dummy_user.user_name}</h3>
            <p>
                
            <table>
            <tr>
                <th>Message</th>
                <th>Module</th>
                <th>Line No.</th>
                <th>Completion Date</th>
            </tr>
            
                    <tr>
                        <td>{self._dummy_msg}</td>
                        <td>{self._dummy_module}</td>
                        <td>{self._dummy_line_no}</td>
                        <td>{"2020-09-22"}</td>
                    </tr>
                    
            </table>
            
            </p><br>
            """  # noqa: W293

        self._expired_todos_by_user_summary_generator.generate_html()

        self.assertEqual(expected_value, self._expired_todos_by_user_summary_generator.html)


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

    def test_generate_summary(self):
        expected_completion_date = str((datetime.today() + timedelta(days=2)).date().strftime("%Y-%m-%d"))
        expected_value = {
            self._dummy_user.user_name: [
                [self._dummy_msg, self._dummy_module, self._dummy_line_no, expected_completion_date],
                [self._dummy_msg, self._dummy_module, self._dummy_line_no, expected_completion_date],
            ]
        }

        self._upcoming_week_todos_by_user_summary_generator.generate_summary(self._dummy_all_todo_objs)

        self.assertEqual(expected_value, self._upcoming_week_todos_by_user_summary_generator.container)

    def test_generate_html(self):
        expected_completion_date = str((datetime.today() + timedelta(days=2)).date().strftime("%Y-%m-%d"))
        self._upcoming_week_todos_by_user_summary_generator._container = {
            self._dummy_user.user_name: [
                [self._dummy_msg, self._dummy_module, self._dummy_line_no, expected_completion_date],
            ]
        }
        expected_value = f"""
            <h3>Upcoming TODOs for {self._dummy_user.user_name}</h3>
            <p>
                
            <table>
            <tr>
                <th>Message</th>
                <th>Module</th>
                <th>Line No.</th>
                <th>Completion Date</th>
            </tr>
            
                    <tr>
                        <td>{self._dummy_msg}</td>
                        <td>{self._dummy_module}</td>
                        <td>{self._dummy_line_no}</td>
                        <td>{expected_completion_date}</td>
                    </tr>
                    
            </table>
            
            </p><br>
            """  # noqa: W293

        self._upcoming_week_todos_by_user_summary_generator.generate_html()

        self.assertEqual(expected_value, self._upcoming_week_todos_by_user_summary_generator.html)


if __name__ == "__main__":
    unittest.main()
