import os
from glob import glob
from typing import List


def get_files_in_dir(path: str, extension: str, exclude_subdirs: list = [], exclude_files: list = []) -> List[str]:
    """ Provides a list of files in the give directory `path` and its subdirectories

    Args:
        path (str): Path of the directory
        extension (str): Extension of file that needs to be looked for e.g. "py" (without dot and quotations)
        exclude_subdirs (list, optional): Sub directoris of `parent_dir_name` that shouldn't be considered
            exclude_files (list, optional): Files in directory `parent_dir_name` or its sub-directories that shouldn't be considered
    """
    all_files = []
    file_extension = f"*.{extension}"
    exclude_subdirs = set(exclude_subdirs)
    exclude_files = set(exclude_files)

    for dir_path_name_file_tuple in os.walk(path):
        dir_name = os.path.basename(dir_path_name_file_tuple[0])

        if dir_name not in exclude_subdirs:
            file = glob(os.path.join(
                dir_path_name_file_tuple[0], file_extension))
            file_name = os.path.basename(file)

            if file_name not in exclude_files:
                all_files.append(file)

    return all_files
