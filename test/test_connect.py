import os
import tempfile
import unittest
from unittest.mock import patch

from connect import CONNECT_METHOD, Connect, ConnectException


class TestConnectException(unittest.TestCase):
    def test_connect_exception_should_exist(self):
        with self.assertRaises(ConnectException):
            raise ConnectException


class TestConnectMethod(unittest.TestCase):
    def test_connect_method_should_have_https(self):
        self.assertIsNotNone(CONNECT_METHOD.HTTPS)

    def test_connect_method_should_have_dry_run_file(self):
        self.assertIsNotNone(CONNECT_METHOD.DRY_RUN_FILE)

    def test_connect_method_should_have_dry_run_dir(self):
        self.assertIsNotNone(CONNECT_METHOD.DRY_RUN_DIR)


class TestConnect(unittest.TestCase):
    def test_project_dir_name_should_return_project_name(self):
        dummy_project_dir_name = "unittest-project-dir-name"
        connect = Connect(connect_method=CONNECT_METHOD.HTTPS, project_dir_name=dummy_project_dir_name, url="")

        actual_value = connect.project_dir_name

        assert dummy_project_dir_name == actual_value

    def test___str___should_return_string_representation_of_connect(self):
        dummy_url = "unittest-url"
        dummy_target_dir = "unittest-target-dir"
        connect = Connect(connect_method=CONNECT_METHOD.HTTPS, project_dir_name=dummy_target_dir, url=dummy_url)
        expected_value = f"{repr(connect)} connect_method: {CONNECT_METHOD.HTTPS} project_dir_name: {dummy_target_dir} url: {dummy_url}"

        actual_value = str(connect)

        assert expected_value == actual_value

    @patch("connect.Connect._pull_using_https")
    def test_pull_repository_should_call__pull_using_https_if_set(self, spy__pull_using_https):
        dummy_url = "unittest-url"
        dummy_target_dir = "unittest-target-dir"
        connect = Connect(connect_method=CONNECT_METHOD.HTTPS, project_dir_name=dummy_target_dir, url=dummy_url)

        connect.pull_repository(target_dir=dummy_target_dir)

        spy__pull_using_https.assert_called_once_with(dummy_target_dir)

    @patch("connect.Connect._pull_file_for_dry_run")
    def test_pull_repository_should_call__pull_file_using_dry_run_if_set(self, spy__pull_for_dry_run):
        dummy_test_file = "unittest-test-file"
        dummy_project_dir_name = "unittest-dummy-project-dir-name"
        dummy_target_dir = "unittest-target-dir"
        connect = Connect(connect_method=CONNECT_METHOD.DRY_RUN_FILE, project_dir_name=dummy_project_dir_name, url=dummy_test_file)

        connect.pull_repository(target_dir=dummy_target_dir)

        spy__pull_for_dry_run.assert_called_once_with(dummy_target_dir)

    @patch("connect.Connect._pull_dir_for_dry_run")
    def test_pull_repository_should_call__pull_dir_using_dry_run_if_set(self, spy__pull_dir_for_dry_run):
        dummy_test_dir = "unittest-test-dir"
        dummy_project_dir_name = "unittest-dummy-project-dir-name"
        dummy_target_dir = "unittest-target-dir"
        connect = Connect(connect_method=CONNECT_METHOD.DRY_RUN_DIR, project_dir_name=dummy_project_dir_name, url=dummy_test_dir)

        connect.pull_repository(target_dir=dummy_target_dir)

        spy__pull_dir_for_dry_run.assert_called_once_with(dummy_target_dir)

    @patch("connect.Connect._pull_using_https")
    def test_pull_repository_should_raise_connect_exception_if_unsupported_connect_method_passed(self, stub__pull_using_https):
        connect = Connect(connect_method="unittest-connect-method", project_dir_name="", url="")

        with self.assertRaises(ConnectException):
            connect.pull_repository("")

    @patch("connect.Connect._pull_using_https")
    def test_pull_repository_should_raise_connect_exception_if_any_exception_in_connecting(self, stub__pull_using_https):
        stub__pull_using_https.side_effect = Exception("unittest-connect-via-https-exception")
        connect = Connect(connect_method=CONNECT_METHOD.HTTPS, project_dir_name="", url="")

        with self.assertRaises(ConnectException):
            connect.pull_repository("")

    def test__pull_using_https(self):
        dummy_url = "unittest-url"
        dummy_target_dir = "unittest-target-dir"
        connect = Connect(connect_method=CONNECT_METHOD.DRY_RUN_FILE, project_dir_name="", url=dummy_url)

        connect._pull_using_https(dummy_target_dir)

    def test__pull_file_for_dry_run_should_copy_file_into_temp_dir(self):
        dummy_project_dir_name = "unittest-project-dir-name"

        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as temp_file_dir:
            test_file = os.path.join(temp_file_dir, "unittest-temp-file")
            with open(test_file, "w") as f:
                f.write("unittest-temp-file-content")

            test_file_base_name = os.path.basename(test_file)
            expected_file_path = os.path.join(temp_dir, dummy_project_dir_name, test_file_base_name)

            connect = Connect(connect_method=CONNECT_METHOD.DRY_RUN_FILE, project_dir_name=dummy_project_dir_name, url=test_file)
            connect._pull_file_for_dry_run(target_dir=temp_dir)

            assert os.path.isfile(expected_file_path)

    def test__pull_dir_for_dry_run_should_copy_directory_into_temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir1, tempfile.TemporaryDirectory() as temp_dir2:
            test_file = os.path.join(temp_dir2, "unittest-temp-file")
            with open(test_file, "w") as f:
                f.write("unittest-temp-file-content")

            expected_dir_path = os.path.join(temp_dir1, temp_dir2)
            expected_file_path = os.path.join(temp_dir1, os.path.basename(temp_dir2), "unittest-temp-file")

            connect = Connect(connect_method=CONNECT_METHOD.DRY_RUN_DIR, project_dir_name="", url=temp_dir2)
            connect._pull_dir_for_dry_run(target_dir=temp_dir1)

            assert os.path.isdir(expected_dir_path)
            assert os.path.isfile(expected_file_path)


if __name__ == "__main__":
    unittest.main()
