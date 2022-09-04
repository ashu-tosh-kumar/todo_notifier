import os
import re
from typing import Dict, List

from constants import UNKNOWN_USER_NAME
from models import POSITION, TODO, USER
from utils import compute_file_line_no_to_chars_map, compute_line_and_pos_given_span


def parse_files_for_todo_items(project_parent_dir: str, files: List[str]) -> Dict[str, List[TODO]]:
    """Parses the list of `files` one by one to collect all todo items

    Args:
        project_parent_dir (str): Parent directory of the project folder (required to get relative path of files and avoid exposing temporary paths)
        files (List[str]): List of all files that need to be parsed

    Returns:
        Dict[str, List[TODO]]: Returns a key-value pair where key is relative path of file parsed and value is list of todo objects in that file
    """
    all_todos_objs = {}
    for file in files:
        rel_file_path = os.path.relpath(file, project_parent_dir)
        all_todos_objs[rel_file_path] = []
        line_no_to_chars_map = compute_file_line_no_to_chars_map(file)
        with open(file, "r") as f:
            file_content = f.read()
            todo_items = re.finditer(r"TODO.*", file_content, re.MULTILINE)
            for todo_item in todo_items:
                todo_item_group = todo_item.group()
                todo_date_username = re.findall(
                    r"TODO\s*(\[.*\])?\s*(@[^\s]*)?\s*(.*)?",
                    todo_item_group,
                    re.MULTILINE,
                )

                if todo_date_username:
                    todo_date_username = todo_date_username[0]

                msg = ""
                if len(todo_date_username) > 2:
                    msg = todo_date_username[2]

                user = USER(UNKNOWN_USER_NAME)  # By default we assume an unknown user
                if len(todo_date_username) > 1:
                    user = USER(todo_date_username[1][1:] or UNKNOWN_USER_NAME)  # handle empty string

                completion_date_str = ""
                if len(todo_date_username) > 0:
                    completion_date_str = todo_date_username[0]
                    if completion_date_str:
                        completion_date_str = completion_date_str[1:-1]

                module = rel_file_path
                todo_position = todo_item.span()

                line = compute_line_and_pos_given_span(line_no_to_chars_map, todo_position)
                position = POSITION(line)

                todo = TODO(msg, user, completion_date_str, module, position)

                all_todos_objs[rel_file_path].append(todo)

    return all_todos_objs
