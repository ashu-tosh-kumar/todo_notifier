import os
import tempfile
import unittest

from mock import patch

from connect import CONNECT_METHOD, Connect, ConnectException


class TestConnectException(unittest.TestCase):
    def test_connect_exception_should_exist(self):
        with self.assertRaises(ConnectException):
            raise ConnectException


class TestConnectMethod(unittest.TestCase):
    def test_connect_method_should_have_https(self):
        self.assertIsNotNone(CONNECT_METHOD.HTTPS)

    def test_connect_method_should_have_dry_run(self):
        self.assertIsNotNone(CONNECT_METHOD.DRY_RUN)


class TestConnect(unittest.TestCase):
    @patch("connect.Connect._pull_using_https")
    def test_pull_repository_should_call__pull_using_https_if_set(self, spy__pull_using_https):
        dummy_url = "unittest-url"
        dummy_target_dir = "unittest-target-dir"
        connect = Connect(connect_method=CONNECT_METHOD.HTTPS)

        connect.pull_repository(dummy_url=dummy_url, dummy_target_dir=dummy_target_dir)

        spy__pull_using_https.assert_called_once_with(dummy_url=dummy_url, dummy_target_dir=dummy_target_dir)

    @patch("connect.Connect._pull_for_dry_run")
    def test_pull_repository_should_call__pull_using_dry_run_if_set(self, spy__pull_for_dry_run):
        dummy_test_file = "unittest-test-file"
        dummy_project_dir_name = "unittest-dummy=project-dir-name"
        dummy_target_dir = "unittest-target-dir"
        connect = Connect(connect_method=CONNECT_METHOD.DRY_RUN)

        connect.pull_repository(test_file=dummy_test_file, project_dir_name=dummy_project_dir_name, target_dir=dummy_target_dir)

        spy__pull_for_dry_run.assert_called_once_with(test_file=dummy_test_file, project_dir_name=dummy_project_dir_name, target_dir=dummy_target_dir)

    def test__pull_using_https(self):
        pass

    def test__pull_for_dry_run_should_copy_file_into_temp_dir(self):
        dummy_project_dir_name = "unittest-project-dir-name"
        connect = Connect(connect_method=CONNECT_METHOD.DRY_RUN)

        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as temp_file_dir:
            test_file = os.path.join(temp_file_dir, "unittest-temp-file")
            with open(test_file, "w") as f:
                f.write("unittest-temp-file-content")

            test_file_base_name = os.path.basename(test_file)
            expected_file_path = os.path.join(temp_dir, dummy_project_dir_name, test_file_base_name)

            connect._pull_for_dry_run(test_file=test_file, project_dir_name=dummy_project_dir_name, target_dir=temp_dir)

            assert os.path.isfile(expected_file_path)
