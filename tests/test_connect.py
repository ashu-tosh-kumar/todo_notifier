import os
import tempfile
import unittest
from unittest.mock import patch

from todonotifier.connect import Connect, ConnectException, ConnectMethod


class TestConnectException(unittest.TestCase):
    def test_connect_exception_should_exist(self):
        with self.assertRaises(ConnectException):
            raise ConnectException


class TestConnectMethod(unittest.TestCase):
    def test_connect_method_should_have_git_clone(self):
        self.assertIsNotNone(ConnectMethod.GIT_CLONE)

    def test_connect_method_should_have_dry_run_file(self):
        self.assertIsNotNone(ConnectMethod.DRY_RUN_FILE)

    def test_connect_method_should_have_dry_run_dir(self):
        self.assertIsNotNone(ConnectMethod.DRY_RUN_DIR)

    def test_connect_method_should_have_local(self):
        self.assertIsNotNone(ConnectMethod.LOCAL)


class TestConnect(unittest.TestCase):
    def test_project_dir_name_should_return_project_name(self):
        dummy_project_dir_name = "unittest-project-dir-name"
        connect = Connect(connect_method=ConnectMethod.GIT_CLONE, project_dir_name=dummy_project_dir_name, url="")

        actual_value = connect.project_dir_name

        assert dummy_project_dir_name == actual_value

    def test___str___should_return_string_representation_of_connect(self):
        dummy_url = "unittest-url"
        dummy_target_dir = "unittest-target-dir"
        connect = Connect(connect_method=ConnectMethod.GIT_CLONE, project_dir_name=dummy_target_dir, url=dummy_url)
        expected_value = f"{repr(connect)} connect_method: {ConnectMethod.GIT_CLONE} project_dir_name: {dummy_target_dir} url: {dummy_url}"

        actual_value = str(connect)

        assert expected_value == actual_value

    def test___str___should_not_show_credentials_of_the_url(self):
        for url, shown in (
            ("https://user:s3cret-token@github.com/org/repo.git", "https://***@github.com/org/repo.git"),
            ("https://s3cret-token@github.com/org/repo.git", "https://***@github.com/org/repo.git"),
            ("git@github.com:org/repo.git", "git@github.com:org/repo.git"),  # No scheme: the user name of an ssh address is no secret
            ("https://github.com/org/repo@v1", "https://github.com/org/repo@v1"),  # An @ after the host is not a credential
            ("/local/dir", "/local/dir"),
        ):
            connect = Connect(connect_method=ConnectMethod.GIT_CLONE, project_dir_name="p", url=url)

            self.assertTrue(str(connect).endswith(f" url: {shown}"), str(connect))
            self.assertNotIn("s3cret", str(connect))

    @patch("todonotifier.connect.Connect._pull_using_git_clone")
    def test_pull_repository_should_call__pull_using_git_clone_if_set(self, spy__pull_using_https):
        dummy_url = "unittest-url"
        dummy_target_dir = "unittest-target-dir"
        connect = Connect(connect_method=ConnectMethod.GIT_CLONE, project_dir_name=dummy_target_dir, url=dummy_url)

        connect.pull_repository(target_dir=dummy_target_dir)

        spy__pull_using_https.assert_called_once_with(dummy_target_dir, branch_name=None)

    @patch("todonotifier.connect.Connect._pull_file_for_dry_run")
    def test_pull_repository_should_call__pull_file_using_dry_run_if_set(self, spy__pull_for_dry_run):
        dummy_test_file = "unittest-test-file"
        dummy_project_dir_name = "unittest-dummy-project-dir-name"
        dummy_target_dir = "unittest-target-dir"
        connect = Connect(connect_method=ConnectMethod.DRY_RUN_FILE, project_dir_name=dummy_project_dir_name, url=dummy_test_file)

        connect.pull_repository(target_dir=dummy_target_dir)

        spy__pull_for_dry_run.assert_called_once_with(dummy_target_dir)

    @patch("todonotifier.connect.Connect._pull_dir_for_dry_run")
    def test_pull_repository_should_call__pull_dir_using_dry_run_if_set(self, spy__pull_dir_for_dry_run):
        dummy_test_dir = "unittest-test-dir"
        dummy_project_dir_name = "unittest-dummy-project-dir-name"
        dummy_target_dir = "unittest-target-dir"
        connect = Connect(connect_method=ConnectMethod.DRY_RUN_DIR, project_dir_name=dummy_project_dir_name, url=dummy_test_dir)

        connect.pull_repository(target_dir=dummy_target_dir)

        spy__pull_dir_for_dry_run.assert_called_once_with(dummy_target_dir)

    def test_connect_method_should_return_the_connect_method(self):
        connect = Connect(connect_method=ConnectMethod.LOCAL, project_dir_name="", url="")

        self.assertEqual(ConnectMethod.LOCAL, connect.connect_method)

    def test_source_path_should_return_the_absolute_path_of_url(self):
        connect = Connect(connect_method=ConnectMethod.LOCAL, project_dir_name="", url="unittest-relative-dir/")

        self.assertEqual(os.path.join(os.getcwd(), "unittest-relative-dir"), connect.source_path)

    def test_pull_repository_with_local_should_validate_without_copying(self):
        with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as target_dir:
            with open(os.path.join(source_dir, "a.py"), "w") as f:
                f.write("# TODO x\n")
            connect = Connect(connect_method=ConnectMethod.LOCAL, project_dir_name="unittest-project", url=source_dir)

            with patch("todonotifier.connect.copytree") as spy_copytree, patch("todonotifier.connect.copy") as spy_copy:
                connect.pull_repository(target_dir=target_dir)

            spy_copytree.assert_not_called()
            spy_copy.assert_not_called()
            self.assertEqual([], os.listdir(target_dir))
            self.assertEqual(["a.py"], os.listdir(source_dir))

    def test_pull_repository_with_local_should_raise_connect_exception_if_url_is_not_a_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            connect = Connect(connect_method=ConnectMethod.LOCAL, project_dir_name="", url=os.path.join(temp_dir, "missing"))

            with self.assertRaises(ConnectException):
                connect.pull_repository(target_dir=temp_dir)

    @patch("todonotifier.connect.Connect._pull_using_git_clone")
    def test_pull_repository_should_raise_connect_exception_if_unsupported_connect_method_passed(self, stub__pull_using_https):
        connect = Connect(connect_method="unittest-connect-method", project_dir_name="", url="")

        with self.assertRaises(ConnectException):
            connect.pull_repository("")

    @patch("todonotifier.connect.Connect._pull_using_git_clone")
    def test_pull_repository_should_raise_connect_exception_if_any_exception_in_connecting(self, stub__pull_using_https):
        stub__pull_using_https.side_effect = Exception("unittest-connect-via-git-clone-exception")
        connect = Connect(connect_method=ConnectMethod.GIT_CLONE, project_dir_name="", url="")

        with self.assertRaises(ConnectException):
            connect.pull_repository("")

    # NOTE: This test runs over internet
    def test__pull_using_git_clone_should_pull_git_repository(self):
        dummy_url = "https://github.com/ashu-tosh-kumar/Interesting-ML-Models.git"
        dummy_project_dir_name = "interesting-ml-models"

        with tempfile.TemporaryDirectory() as temp_dir:
            expected_dir_path = temp_dir

            connect = Connect(connect_method=ConnectMethod.GIT_CLONE, project_dir_name=dummy_project_dir_name, url=dummy_url)
            connect._pull_using_git_clone(target_dir=temp_dir)

            assert os.path.isdir(expected_dir_path)

    # NOTE: This test runs over internet
    def test__pull_using_git_clone_should_pull_git_repository_with_given_branch(self):
        dummy_url = "https://github.com/ashu-tosh-kumar/Interesting-ML-Models.git"
        dummy_project_dir_name = "interesting-ml-models"
        dummy_branch_name = "main"

        with tempfile.TemporaryDirectory() as temp_dir:
            expected_dir_path = temp_dir

            connect = Connect(connect_method=ConnectMethod.GIT_CLONE, project_dir_name=dummy_project_dir_name, url=dummy_url)
            repo = connect._pull_using_git_clone(target_dir=temp_dir, branch_name=dummy_branch_name)

            assert os.path.isdir(expected_dir_path)
            assert dummy_branch_name == repo.active_branch.name

    def test__pull_file_for_dry_run_should_copy_file_into_temp_dir(self):
        dummy_project_dir_name = "unittest-project-dir-name"

        with tempfile.TemporaryDirectory() as temp_dir, tempfile.TemporaryDirectory() as temp_file_dir:
            test_file = os.path.join(temp_file_dir, "unittest-temp-file")
            with open(test_file, "w") as f:
                f.write("unittest-temp-file-content")

            test_file_base_name = os.path.basename(test_file)
            expected_file_path = os.path.join(temp_dir, dummy_project_dir_name, test_file_base_name)

            connect = Connect(connect_method=ConnectMethod.DRY_RUN_FILE, project_dir_name=dummy_project_dir_name, url=test_file)
            connect._pull_file_for_dry_run(target_dir=temp_dir)

            assert os.path.isfile(expected_file_path)

    def test__pull_dir_for_dry_run_should_copy_directory_into_temp_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir1, tempfile.TemporaryDirectory() as temp_dir2:
            test_file = os.path.join(temp_dir2, "unittest-temp-file")
            with open(test_file, "w") as f:
                f.write("unittest-temp-file-content")

            expected_dir_path = os.path.join(temp_dir1, temp_dir2)
            expected_file_path = os.path.join(temp_dir1, os.path.basename(temp_dir2), "unittest-temp-file")

            connect = Connect(connect_method=ConnectMethod.DRY_RUN_DIR, project_dir_name="", url=temp_dir2)
            connect._pull_dir_for_dry_run(target_dir=temp_dir1)

            assert os.path.isdir(expected_dir_path)
            assert os.path.isfile(expected_file_path)


if __name__ == "__main__":
    unittest.main()
