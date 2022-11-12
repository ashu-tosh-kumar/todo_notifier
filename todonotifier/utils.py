import logging
import os
import re
from typing import Dict, List, Tuple

from todonotifier.models import TODO
from todonotifier.summary_generators import BaseSummaryGenerator

# logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class InCompatibleTypesException(Exception):
    """Raised when two different types of data is passed for recursive update of a dictionary

    E.g. {"a": []} and {"a": {}}, Here value of key "a" is of type list and dict which are not same
    """

    pass


def _ignore_dir_or_file(dir_or_file_path: str, exclude_dirs_or_files: dict) -> bool:
    """Checks and returns bool about whether a directory should be excluded based on rules in `exclude_dirs_or_files`

    Args:
        dir_or_file_path (str): Path of the directory.file that needs to be checked
        exclude_dirs_or_files (dict): Directories/Files that shouldn't be considered

    Returns:
        bool: True if `dir_or_file_path` should be ignored based on rules in `exclude_dirs_or_files` else False
    """
    dir_name = os.path.basename(dir_or_file_path)

    for pattern in exclude_dirs_or_files.get("PATTERN", []):
        if bool(re.match(pattern, dir_name)):
            return True

    if dir_name in exclude_dirs_or_files.get("NAME", []):
        return True

    if dir_or_file_path in exclude_dirs_or_files.get("ABS_PATH", []):
        return True

    return False


def get_files_in_dir(dir_path: str, extension: str, exclude_subdirs: dict, exclude_files: dict) -> List[str]:
    """Provides a list of files in the give directory `path` and its subdirectories

    Args:
        dir_path (str): Path of the directory
        extension (str): Extension of file that needs to be looked for e.g. "py" (without dot and quotations)
        exclude_subdirs (dict): Sub directories of `parent_dir_name` that shouldn't be considered
        exclude_files (dict): Files in directory `parent_dir_name` or its sub-directories that shouldn't be considered
    """
    all_files = []
    file_extension = f".{extension}"

    for sub_dir_or_file in os.listdir(dir_path):
        try:
            sub_dir_or_file_path = os.path.join(dir_path, sub_dir_or_file)

            if os.path.isdir(sub_dir_or_file_path):
                if not _ignore_dir_or_file(sub_dir_or_file_path, exclude_subdirs):
                    sub_dir_all_files = get_files_in_dir(sub_dir_or_file_path, extension, exclude_subdirs, exclude_files)
                    all_files.extend(sub_dir_all_files)
            elif os.path.isfile(sub_dir_or_file_path):
                if sub_dir_or_file_path.endswith(file_extension) and not _ignore_dir_or_file(sub_dir_or_file_path, exclude_files):
                    all_files.append(sub_dir_or_file_path)
        except Exception:
            logger.exception(f"Error in getting files in directory: {sub_dir_or_file}")

    return all_files


def recursive_update(base_dict: dict, new_dict: dict) -> None:
    """Performs in-place recursive update of dictionary `base_dict` from contents of dictionary `new_dict`

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
            elif type(base_dict[key]) == type(new_dict[key]):  # noqa
                base_dict[key] = new_dict[key]
            else:
                raise InCompatibleTypesException(f"Different types passed: {type(base_dict[key])}, {type(new_dict[key])} for recursive update")
        else:
            base_dict[key] = new_dict[key]


def compute_file_line_no_to_chars_map(file: str) -> Dict[int, int]:
    """Takes a file location and returns a dict representing number of characters in each line no.

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

    return line_no_to_chars_map


def compute_line_and_pos_given_span(line_no_to_chars_map: dict, span: Tuple[int, int]) -> int:
    """Computes line no. given absolute start position in file and `line_no_to_chars_map` mapping of line no. to no. of characters in that line

    Args:
        line_no_to_chars_map (dict): Dictionary mapping line no. to no. of characters in that line in `file`
        span (Tuple[int, int]): Span value as returned by `re.span()`

    Returns:
        int: Line no. of the character at `start_idx` in file `file`. First line is considered as
    """
    curr_count = 0
    for line_no in range(len(line_no_to_chars_map)):
        curr_count += line_no_to_chars_map[line_no + 1]
        if curr_count >= span[0]:
            todo_line_no = line_no + 1
            break

    return todo_line_no


def generate_summary(all_todos_objs: Dict[str, List[TODO]], summary_generators: List[BaseSummaryGenerator], generate_html: bool) -> None:
    """Function to generate multiple kind of summaries from given list of todo items

    It allows users to pass a function/callable. It will call each summary generator `callable` and pass it with
    the `all_todos_objs`. The respective callable function can read the passed todo objects and save relevant information
    in their containers accessible via `{callable}.container`

    Args:
        all_todos_objs (Dict[str, List[TODO]]): Key-value pair where key is relative path of file parsed and value is list of todo objects in that file
        summary_generators (List[BaseSummaryGenerator]): List of summary generators objects
        generate_html (bool): Boolean to control whether to generate the html report for the respective summary generator
    """
    for summary_generator_class_instance in summary_generators:
        try:
            summary_generator_class_instance.generate_summary(all_todos_objs)
            if generate_html:
                summary_generator_class_instance.generate_html()
        except Exception:
            logger.exception(f"Error in generating summary from: {summary_generator_class_instance}")


def store_html(html: str, report_name: str, target_dir: str = None) -> None:
    """Function to store html report into files in location `target_dir`

    Args:
        html (str): HTML content of the report
        report_name (str): Name with which `html` content needs to be stored into a file with/without extension. Default extension is `.html`
        target_dir (str, optional): Target location(absolute path) where file needs to be stored. Defaults to folder `.reports` in current location.
    """
    default_folder_name = ".report"
    if not target_dir:
        target_dir = os.path.join(os.getcwd(), default_folder_name)
        if not os.path.isdir(target_dir):
            os.mkdir(target_dir)

    report_name_lst = report_name.split(".")
    if len(report_name_lst) > 1:
        extension = report_name_lst[-1]
        report_name = "".join(report_name_lst[:-1])
        report_name += f".{extension}"
    else:
        report_name += ".html"

    file_path = os.path.join(target_dir, report_name)

    with open(file_path, "w") as f:
        f.write(html)
