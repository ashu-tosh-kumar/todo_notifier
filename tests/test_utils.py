import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from todonotifier.constants import DEFAULT_EXCLUDE_DIRS, DEFAULT_EXCLUDE_FILES
from todonotifier.utils import (
    InCompatibleTypesException,
    _ignore_dir_or_file,
    compute_file_line_no_to_chars_map,
    compute_line_and_pos_given_span,
    generate_summary,
    get_files_in_dir,
    recursive_update,
    store_html,
)


class TestInCompatibleTypesException(unittest.TestCase):
    def test_incompatible_types_exception_should_exist(self):
        with self.assertRaises(InCompatibleTypesException):
            raise InCompatibleTypesException


class TestIgnoreDirOrFile(unittest.TestCase):
    @patch("todonotifier.utils.os")
    def test__ignore_dir_or_file_should_correctly_ignore_file_patterns(self, stub_os):
        test_data = [
            # file to test, expected value
            ("unittest.py[cod]", True),
            ("unittest.py.class", True),
            ("unittest.so", True),
            ("unittest.manifest", True),
            ("unittest.spec", True),
            ("unittest.coverage", True),
            ("unittest.coverage.unittest", True),
            ("unittest.cache", True),
            ("nosetests.xml", True),
            ("coverage.xml", True),
            ("unittest.mo", True),
            ("unittest.pot", True),
            ("unittest.log", True),
            ("unittest.sage.py", True),
            ("/some-file", True),
        ]
        stub_os.path.basename = lambda x: x
        DEFAULT_EXCLUDE_FILES["ABS_PATH"].append("/some-file")

        for pattern, expected_value in test_data:
            actual_value = _ignore_dir_or_file(pattern, DEFAULT_EXCLUDE_FILES)
            self.assertEqual(expected_value, actual_value)

    @patch("todonotifier.utils.os")
    def test__ignore_dir_or_file_should_correctly_ignore_file_names(self, stub_os):
        stub_os.path.basename = lambda x: x

        for pattern in DEFAULT_EXCLUDE_FILES["NAME"]:
            self.assertEqual(True, _ignore_dir_or_file(pattern, DEFAULT_EXCLUDE_FILES))

    @patch("todonotifier.utils.os")
    def test__ignore_dir_or_file_should_correctly_ignore_file_path(self, stub_os):
        stub_os.path.basename = lambda x: x

        for pattern in DEFAULT_EXCLUDE_FILES["ABS_PATH"]:
            self.assertEqual(True, _ignore_dir_or_file(pattern, DEFAULT_EXCLUDE_FILES))

    @patch("todonotifier.utils.os")
    def test__ignore_dir_or_file_should_not_ignore_correct_files(self, stub_os):
        test_data = [
            # file to test, expected value
            ("unittest.py", False),
            ("test_unittest.py", False),
        ]
        stub_os.path.basename = lambda x: x

        for pattern, expected_value in test_data:
            self.assertEqual(expected_value, _ignore_dir_or_file(pattern, DEFAULT_EXCLUDE_FILES))

    @patch("todonotifier.utils.os")
    def test__ignore_dir_or_file_should_correctly_ignore_dir_patterns(self, stub_os):
        test_data = [
            # file to test, expected value
            ("unittest.egg-info", True),
            (".egg-info", True),
            ("unittest.cover", True),
            (".cover", True),
            ("unittest.py,cover", True),
            (".py,cover", True),
        ]
        stub_os.path.basename = lambda x: x

        for pattern, expected_value in test_data:
            self.assertEqual(expected_value, _ignore_dir_or_file(pattern, DEFAULT_EXCLUDE_DIRS))

    @patch("todonotifier.utils.os")
    def test__ignore_dir_or_file_should_correctly_ignore_dir_names(self, stub_os):
        stub_os.path.basename = lambda x: x

        for pattern in DEFAULT_EXCLUDE_DIRS["NAME"]:
            self.assertEqual(True, _ignore_dir_or_file(pattern, DEFAULT_EXCLUDE_DIRS))

    @patch("todonotifier.utils.os")
    def test__ignore_dir_or_file_should_correctly_ignore_dir_path(self, stub_os):
        stub_os.path.basename = lambda x: x

        for pattern in DEFAULT_EXCLUDE_DIRS["ABS_PATH"]:
            self.assertEqual(True, _ignore_dir_or_file(pattern, DEFAULT_EXCLUDE_DIRS))

    @patch("todonotifier.utils.os")
    def test__ignore_dir_or_file_should_not_ignore_correct_dirs(self, stub_os):
        test_data = [
            # file to test, expected value
            ("unittest", False),
            ("test", False),
            ("src", False),
        ]
        stub_os.path.basename = lambda x: x

        for pattern, expected_value in test_data:
            self.assertEqual(expected_value, _ignore_dir_or_file(pattern, DEFAULT_EXCLUDE_DIRS))


class TestGetFilesInDir(unittest.TestCase):
    def test_get_files_in_dir_should_give_all_files_in_dir(self):
        dummy_extension = "py"

        with tempfile.TemporaryDirectory() as temp_dir:
            files = [os.path.join(temp_dir, f"file{idx}.{dummy_extension}") for idx in range(5)]
            expected_value = set(files)
            files.append(os.path.join(temp_dir, "diff_file.diff_extension"))
            for file in files:
                with open(file, "w") as f:
                    f.write("unittest-content")

            nested_dir = os.path.join(temp_dir, "nested_dir")
            os.mkdir(nested_dir)
            nested_files = [os.path.join(nested_dir, f"file{idx}.{dummy_extension}") for idx in range(5)]
            expected_value = expected_value.union(nested_files)
            nested_files.append(os.path.join(nested_dir, "diff_file.diff_extension"))
            for file in nested_files:
                with open(file, "w") as f:
                    f.write("unittest-nested-content")

            actual_value = set(get_files_in_dir(temp_dir, dummy_extension, {}, {}))
            self.assertEqual(expected_value, actual_value)

    @patch("todonotifier.utils._ignore_dir_or_file")
    def test_get_files_in_dir_should_not_throw_exception_if_caught_any(self, stub__ignore_dir_or_file):
        dummy_extension = "py"
        stub__ignore_dir_or_file.side_effect = [False, Exception("unittest-ignore-dir-or-file-exception")]

        with tempfile.TemporaryDirectory() as temp_dir:
            files = [os.path.join(temp_dir, f"file{idx}.{dummy_extension}") for idx in range(2)]
            for file in files:
                with open(file, "w") as f:
                    f.write("unittest-content")

            actual_value = set(get_files_in_dir(temp_dir, dummy_extension, {}, {}))
            self.assertEqual(1, len(actual_value))


class RecursiveUpdate(unittest.TestCase):
    def test_recursive_update_should_update_dict_recursively(self):
        dummy_base_dict = {"key1": "value1", "key2": "value2", "key3": [1, 2], "key4": {"key41": "value41", "key42": "value42"}}
        dummy_new_dict = {"key2": "value22", "key3": [3, 4], "key4": {"key41": "value42", "key43": "value43"}}
        expected_value = {"key1": "value1", "key2": "value22", "key3": [3, 4], "key4": {"key41": "value42", "key42": "value42", "key43": "value43"}}

        recursive_update(dummy_base_dict, dummy_new_dict)

        self.assertEqual(expected_value, dummy_base_dict)

    def test_recursive_update_should_raise_exception_for_incompatible_types(self):
        dummy_base_dict = {"key1": "value1"}
        dummy_new_dict = {"key1": [1]}

        with self.assertRaises(InCompatibleTypesException):
            recursive_update(dummy_base_dict, dummy_new_dict)


class TestComputeFileLineNoToCharsMap(unittest.TestCase):
    def test_compute_file_line_no_to_chars_map_should_correctly_map_chars_in_lines(self):
        dummy_file_content = """Dummy file\ncontent\nfor \nunittests"""
        expected_value = {1: 11, 2: 8, 3: 5, 4: 9}

        with tempfile.TemporaryDirectory() as temp_dir:
            dummy_file = "unittest-file.py"
            dummy_file_path = os.path.join(temp_dir, dummy_file)
            with open(dummy_file_path, "w") as f:
                f.write(dummy_file_content)

            actual_value = compute_file_line_no_to_chars_map(dummy_file_path)

            self.assertEqual(expected_value, actual_value)


class TestComputeLineAndPosGivenSpan(unittest.TestCase):
    def test_compute_line_and_pos_given_span(self):
        dummy_line_no_to_chars_map = {1: 11, 2: 8, 3: 5, 4: 9}  # """Dummy file\ncontent\nfor \nunittests"""
        dummy_span = (12, -1)  # we care of only of first value
        expected_value = 2

        actual_value = compute_line_and_pos_given_span(dummy_line_no_to_chars_map, dummy_span)

        self.assertEqual(expected_value, actual_value)


class TestGenerateSummary(unittest.TestCase):
    def test_generate_summary_should_call_all_summary_generators(self):
        dummy_all_todos_objs = {"unittest-key": []}
        spy_summary_generator1 = Mock()
        spy_summary_generator2 = Mock()
        spy_summary_generator3 = Mock()

        generate_summary(dummy_all_todos_objs, [spy_summary_generator1, spy_summary_generator2, spy_summary_generator3], False)

        spy_summary_generator1.generate_summary.assert_called_once_with(dummy_all_todos_objs)
        spy_summary_generator2.generate_summary.assert_called_once_with(dummy_all_todos_objs)
        spy_summary_generator3.generate_summary.assert_called_once_with(dummy_all_todos_objs)

    def test_generate_summary_should_generate_html_for_all_summary_generators(self):
        dummy_all_todos_objs = {"unittest-key": []}
        spy_summary_generator1 = Mock()
        spy_summary_generator2 = Mock()
        spy_summary_generator3 = Mock()

        generate_summary(dummy_all_todos_objs, [spy_summary_generator1, spy_summary_generator2, spy_summary_generator3], True)

        spy_summary_generator1.generate_html.assert_called_once_with()
        spy_summary_generator2.generate_html.assert_called_once_with()
        spy_summary_generator3.generate_html.assert_called_once_with()

    def test_generate_summary_should_call_all_summary_generators_and_not_throw_any_caught_exception(self):
        dummy_all_todos_objs = {"unittest-key": []}
        spy_summary_generator1 = Mock()
        spy_summary_generator2 = Mock()
        spy_summary_generator2.generate_summary.side_effect = Exception("unittest-summary-generator2-exception")
        spy_summary_generator3 = Mock()

        generate_summary(dummy_all_todos_objs, [spy_summary_generator1, spy_summary_generator2, spy_summary_generator3], False)

        spy_summary_generator1.generate_summary.assert_called_once_with(dummy_all_todos_objs)
        spy_summary_generator3.generate_summary.assert_called_once_with(dummy_all_todos_objs)

    def test_generate_summary_should_generate_html_for_all_summary_generators_and_not_throw_any_caught_exception(self):
        dummy_all_todos_objs = {"unittest-key": []}
        spy_summary_generator1 = Mock()
        spy_summary_generator2 = Mock()
        spy_summary_generator2.generate_html.side_effect = Exception("unittest-summary-generator2-exception")
        spy_summary_generator3 = Mock()

        generate_summary(dummy_all_todos_objs, [spy_summary_generator1, spy_summary_generator2, spy_summary_generator3], True)

        spy_summary_generator1.generate_html.assert_called_once_with()
        spy_summary_generator3.generate_html.assert_called_once_with()


class TestStoreHtml(unittest.TestCase):
    def test_store_html_should_store_html_file_passed_without_extension(self):
        dummy_html = "<div>unittest-html</div>"
        dummy_report_name = "unittest-report"

        with tempfile.TemporaryDirectory() as temp_dir:
            store_html(dummy_html, dummy_report_name, temp_dir)
            expected_file = os.path.join(temp_dir, f"{dummy_report_name}.html")

            self.assertTrue(os.path.isfile(expected_file))

    def test_store_html_should_store_html_file_passed_with_extension(self):
        dummy_html = "<div>unittest-html</div>"
        dummy_report_name = "unittest-report.html"

        with tempfile.TemporaryDirectory() as temp_dir:
            store_html(dummy_html, dummy_report_name, temp_dir)
            expected_file = os.path.join(temp_dir, dummy_report_name)

            self.assertTrue(os.path.isfile(expected_file))

    def test_store_html_should_store_html_file_passed_with_extension_and_no_target_folder(self):
        dummy_html = "<div>unittest-html</div>"
        dummy_report_name = "unittest-report.html"

        with tempfile.TemporaryDirectory() as temp_dir:
            init_dir = os.getcwd()
            os.chdir(temp_dir)
            store_html(dummy_html, dummy_report_name)
            os.chdir(init_dir)
            expected_file = os.path.join(temp_dir, ".report", dummy_report_name)

            self.assertTrue(os.path.isfile(expected_file))


if __name__ == "__main__":
    unittest.main()
