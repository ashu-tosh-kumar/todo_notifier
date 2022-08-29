import os
import re
from typing import Dict, List

from models import POSITION, TODO, USER
from utils import compute_line_and_pos_given_span


def parse_files_for_todo_items(parent_dir_name: str, files: List[str]) -> Dict[str, List[TODO]]:
    """Parses the list of `files` one by one to collect all todo items

    Args:
        parent_dir_name (str): Parent directory of the project (required to get relative path of files and avoid exposing real paths)
        files (List[str]): List of all files that need to be parsed

    Returns:
        Dict[str, List[TODO]]: Returns a key-value pair where key is relative path of file parsed and value is list of todo objects in that file
    """
    all_todos_objs = {}
    for file in files:
        rel_file_path = os.path.join(parent_dir_name, os.path.relpath(file, parent_dir_name))
        all_todos_objs[rel_file_path] = []
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

                msg = todo_date_username[2]
                user = USER(todo_date_username[1])
                completion_date_str = todo_date_username[0]
                module = rel_file_path
                todo_position = todo_item.span()
                line = compute_line_and_pos_given_span(*todo_position)
                position = POSITION(line)

                todo = TODO(msg, user, completion_date_str, module, position)

                all_todos_objs[file].append(todo)

    return all_todos_objs
