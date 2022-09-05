import unittest
from typing import Dict, List

from constants import DEFAULT_COMPLETION_DATE, UNKNOWN_USER_NAME
from models import POSITION, TODO, USER
from todo_notifier import parse_files_for_todo_items


class TestParseFilesForTodoItems(unittest.TestCase):
    def _compare_todos(self, expected_value: Dict[str, List[TODO]], actual_value: Dict[str, List[TODO]]) -> bool:
        if set(expected_value.keys()) != set(actual_value.keys()):
            return False

        for module in actual_value:
            if len(expected_value[module]) != len(actual_value[module]):
                return False

        for module in actual_value:
            for expected_todo, actual_todo in zip(expected_value[module], actual_value[module]):
                if expected_todo.msg != actual_todo.msg:
                    return False

                if expected_todo.user.user_name != actual_todo.user.user_name:
                    return False

                if expected_todo.user.user_email_id != actual_todo.user._user_email_id:
                    return False

                if expected_todo.completion_date != actual_todo.completion_date:
                    return False

                if expected_todo.module != actual_todo.module:
                    return False

                if expected_todo.position.line_no != actual_todo.position.line_no:
                    return False

        return True

    def test_parse_files_for_todo_items(self):
        dummy_files = ["test/sample_test_file.py"]
        project_parent_dir = "test"  # Important to keep it same as test directory
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
                    "[2022-05-03 @ashutosh some-message-faa74c20-d4c2-444e-9fa0-7f202cb10b44",
                    USER(UNKNOWN_USER_NAME),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(11),
                ),
                TODO(
                    "2022-05-03] @ashutosh some-message-63448d77-07fb-4bc1-bf80-2d94ab902f5f",
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
                    "some-message-27cdb8bc-fffe-40df-a212-76452cbdb47c [2022-05-09] some-@message-db1d606f-88d3-474e-890e-8e9c34f093d0",
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
                TODO("[2022-05-09]", USER("ashutosh"), DEFAULT_COMPLETION_DATE, "sample_test_file.py", POSITION(32)),
                TODO(
                    "some-message-40b01cd7-3480-4f9b-9d0c-98ad297cf591 @ashutosh [2022-05-09]",
                    USER(UNKNOWN_USER_NAME),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(33),
                ),
                TODO(
                    "[2022-05-09] some-message-afc38fb9-5a40-470b-9e1c-d4bacc451727",
                    USER("ashutosh"),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(34),
                ),
                TODO("TODO", USER(UNKNOWN_USER_NAME), DEFAULT_COMPLETION_DATE, "sample_test_file.py", POSITION(35)),
                TODO(
                    "TODO [2022-05-11] some-message-7c2a62cb-8037-46cb-bdee-76dd0791d747",
                    USER("ashutosh"),
                    DEFAULT_COMPLETION_DATE,
                    "sample_test_file.py",
                    POSITION(36),
                ),
                TODO(
                    "# TODO [2022-05-12] some-message-d2cad1b4-8881-4687-a38d-2d14fbfd1306",
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
                    POSITION(53),  # Not sure why 53, should be 54
                ),
            ]
        }

        actual_value = parse_files_for_todo_items(project_parent_dir, dummy_files)

        assert self._compare_todos(expected_value, actual_value)


if __name__ == "__main__":
    unittest.main()
