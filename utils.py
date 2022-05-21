import os
import re
from typing import List

from exceptions import InCompatibleTypesException


def _ignore_dir_or_file(dir_or_file_path: str, exclude_dirs_or_files: dict) -> bool:
    """ Checks and returns bool about whether a directory should be excluded based on rules in `exclude_dirs_or_files`

    Args:
        dir_or_file_path (str): Path of the directory.file that needs to be checked
        exclude_dirs_or_files (dict): Directories/Files that shouldn't be considered

    Returns:
        bool: True if `dir_or_file_path` should be ignored based on rules in `exclude_dirs_or_files` else False
    """
    dir_name = os.path.basename(dir_or_file_path)

    for pattern in exclude_dirs_or_files.get("PATTERN", []):
        if bool(re.match(pattern, dir_or_file_path)):
            return True

    if dir_name in exclude_dirs_or_files.get("NAME", []):
        return True

    if dir_or_file_path in exclude_dirs_or_files.get("ABS_PATH", []):
        return True

    return False


def get_files_in_dir(dir_path: str, extension: str, exclude_subdirs: dict, exclude_files: dict) -> List[str]:
    """ Provides a list of files in the give directory `path` and its subdirectories

    Args:
        dir_path (str): Path of the directory
        extension (str): Extension of file that needs to be looked for e.g. "py" (without dot and quotations)
        exclude_subdirs (dict): Sub directories of `parent_dir_name` that shouldn't be considered
        exclude_files (dict): Files in directory `parent_dir_name` or its sub-directories that shouldn't be considered
    """
    all_files = []
    file_extension = f"*.{extension}"

    for sub_dir_or_file in os.listdir(dir_path):
        sub_dir_or_file_path = os.path.join(dir_path, sub_dir_or_file)

        if os.path.isdir(sub_dir_or_file_path):
            if not _ignore_dir_or_file(sub_dir_or_file_path, exclude_subdirs):
                sub_dir_all_files = get_files_in_dir(
                    sub_dir_or_file_path, extension, exclude_subdirs, exclude_files)
                all_files.extend(sub_dir_all_files)
        elif os.path.isfile(sub_dir_or_file_path):
            if not _ignore_dir_or_file(sub_dir_or_file_path, exclude_files) and sub_dir_or_file_path.endswith(file_extension):
                all_files.append(sub_dir_or_file)

    return all_files


def recursive_update(base_dict: dict, new_dict: dict) -> None:
    """ Performs recursive update of dictionary `base_dict` from contents of dictionary `new_dict`

    Args:
        base_dict (dict): Base dictionary that needs to be updated
        new_dict (dict): Dictionary from which `base_dict` needs to be updated with

    Raises:
        InCompatibleTypesException: Raised if type of same key in `base_dict` and `new_dict` is different
    """
    for key in new_dict:
        if key in base_dict:
            if type(base_dict[key]) is dict and type(new_dict[key]) is dict:
                recursive_update(base_dict[key], new_dict[key])
            elif type(base_dict[key]) == type(new_dict[key]):
                base_dict[key] = new_dict[key]
            else:
                raise InCompatibleTypesException(
                    f"Different types passed: {type(base_dict[key])}, {type(new_dict[key])} for recursive update")
        else:
            base_dict[key] = new_dict[key]


def compute_file_line_no_to_chars_map(file: str) -> dict:
    """ Takes a file location and returns a dict representing number of characters in each line no.

    Line numbers are 1-indexed

    Args:
        file (str): Location of file

    Returns:
        dict: Dictionary mapping line no. ot no. of characters in that line in `file`
    """
    line_no_to_chars_map = {}
    with open(file, "r") as f:
        for line_no, line in enumerate(f.readlines()):
            line_no_to_chars_map[line_no + 1] = len(line)


def compute_line_and_pos_given_span(line_no_to_chars_map: dict, start_idx: int) -> int:
    """ Computes line no. given absolute start position in file and `line_no_to_chars_map` mapping of line no. to no. of characters in that line

    Args:
        line_no_to_chars_map (dict): Dictionary mapping line no. ot no. of characters in that line in `file`
        start_idx (int): Absolute start position in file as returned from `re.span()`

    Returns:
        int: Line no. of the character at `start_idx` in file `file`
    """
    curr_count = 0
    for line_no in range(len(line_no_to_chars_map)):
        curr_count += line_no_to_chars_map[line_no + 1]
        if curr_count >= start_idx:
            todo_line_no = line_no + 1
            break

    return todo_line_no
