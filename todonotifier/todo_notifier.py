"""This module contains the core logic of the application
"""

import logging
import os
import re
from typing import Dict, List

from todonotifier.constants import UNKNOWN_USER_NAME
from todonotifier.models import POSITION, TODO, USER
from todonotifier.utils import (
    compute_file_line_no_to_chars_map,
    compute_line_and_pos_given_span,
)

# logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TODO_REGEX_PATTERN = r"TODO\s*(\{.*\})?\s*(@[^\s]*)?\s*(.*)?"

# File size threshold for switching to streaming parser (10 MB)
STREAMING_THRESHOLD_BYTES = 10 * 1024 * 1024


def _parse_todo_from_match(todo_item_group: str, flags: int, rel_file_path: str, line_no: int) -> TODO:
    """Helper function to parse a TODO object from a regex match

    Args:
        todo_item_group (str): The matched TODO string
        flags (int): Regex flags to use
        rel_file_path (str): Relative path of the file
        line_no (int): Line number where TODO was found

    Returns:
        TODO: Parsed TODO object
    """
    todo_date_username = re.findall(TODO_REGEX_PATTERN, todo_item_group, flags=flags)

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

    position = POSITION(line_no)
    return TODO(msg, user, completion_date_str, rel_file_path, position)


def _parse_file_streaming(file: str, rel_file_path: str, ignore_todo_case: bool) -> List[TODO]:
    """Parse a file line-by-line using streaming approach for large files

    Args:
        file (str): Absolute path to the file
        rel_file_path (str): Relative path of the file
        ignore_todo_case (bool): Whether to ignore case when matching TODO

    Returns:
        List[TODO]: List of TODO objects found in the file
    """
    todos = []
    flags = re.MULTILINE
    if ignore_todo_case:
        flags |= re.IGNORECASE

    try:
        with open(file, "r") as f:
            for line_no, line in enumerate(f, start=1):
                if re.search(r"TODO", line, flags=flags):
                    try:
                        todo = _parse_todo_from_match(line.strip(), flags, rel_file_path, line_no)
                        todos.append(todo)
                    except Exception:
                        logger.exception(f"Error parsing TODO on line {line_no} in file: {file}")
    except Exception:
        logger.exception(f"Error in streaming parse of file: {file}")

    return todos


def _parse_file_in_memory(file: str, rel_file_path: str, ignore_todo_case: bool) -> List[TODO]:
    """Parse a file by loading it entirely into memory (original approach)

    Args:
        file (str): Absolute path to the file
        rel_file_path (str): Relative path of the file
        ignore_todo_case (bool): Whether to ignore case when matching TODO

    Returns:
        List[TODO]: List of TODO objects found in the file
    """
    todos = []
    try:
        line_no_to_chars_map = compute_file_line_no_to_chars_map(file)
        with open(file, "r") as f:
            file_content = f.read()

            flags = re.MULTILINE
            if ignore_todo_case:
                flags |= re.IGNORECASE

            todo_items = re.finditer(r"TODO.*", file_content, flags=flags)
            for todo_item_idx, todo_item in enumerate(todo_items):
                try:
                    todo_item_group = todo_item.group()
                    todo_position = todo_item.span()
                    line_no = compute_line_and_pos_given_span(line_no_to_chars_map, todo_position)

                    todo = _parse_todo_from_match(todo_item_group, flags, rel_file_path, line_no)
                    todos.append(todo)
                except Exception:
                    logger.exception(f"Error in parsing todo item: {todo_item}, idx: {todo_item_idx}")
    except Exception:
        logger.exception(f"Error in parsing todo items in file: {file}")

    return todos


def parse_files_for_todo_items(project_parent_dir: str, files: List[str], ignore_todo_case: bool) -> Dict[str, List[TODO]]:
    """Parses the list of `files` one by one to collect all todo items

    Uses streaming parser for files larger than STREAMING_THRESHOLD_BYTES, otherwise loads file into memory.

    Args:
        project_parent_dir (str): Parent directory of the project folder (required to get relative path of files and avoid exposing temporary paths)
        files (List[str]): List of all files that need to be parsed
        ignore_todo_case (bool): Boolean whether to look for case insensitive todo items like todo, Todo etc.

    Returns:
        Dict[str, List[TODO]]: Returns a key-value pair where key is relative path of file parsed and value is list of todo objects in that file
    """
    all_todos_objs = {}
    for file in files:
        try:
            rel_file_path = os.path.relpath(file, project_parent_dir)
            file_size = os.path.getsize(file)

            # Choose parsing strategy based on file size
            if file_size > STREAMING_THRESHOLD_BYTES:
                logger.info(f"Using streaming parser for large file ({file_size / (1024 * 1024):.2f} MB): {file}")
                todos = _parse_file_streaming(file, rel_file_path, ignore_todo_case)
            else:
                todos = _parse_file_in_memory(file, rel_file_path, ignore_todo_case)

            all_todos_objs[rel_file_path] = todos
        except Exception:
            logger.exception(f"Error in parsing todo items in file: {file}")
            all_todos_objs[rel_file_path] = []

    return all_todos_objs
