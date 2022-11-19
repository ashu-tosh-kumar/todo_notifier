from todonotifier.config import BaseConfig, DefaultConfig
from todonotifier.connect import CONNECT_METHOD, Connect
from todonotifier.driver import run as driver_run
from todonotifier.notifier import EmailNotifier


def run():
    """Main starting point of the TODO application to be modified by end users per their need

    This script can be modified to add a for loop for multiple projects

    This file/function after initial code commit should be added in `.gitignore` so that users
    can safely update the TODO application by simply pulling the latest changes
    """
    git_url: str = "tests/sample_test_file.py"  # Placeholder for HTTPS/SSH based git url
    project_dir_name: str = ""  # Placeholder. Generaly same as project name and must be empty for `CONNECT_METHOD.DRY_RUN_FILE`
    sender_email = ""
    password = ""
    receivers = []
    notifier = EmailNotifier(sender_email, password, receivers)
    config: BaseConfig = DefaultConfig(save_html_reports=True, ignore_todo_case=True, notifier=notifier)  # Change per need
    connect = Connect(
        connect_method=CONNECT_METHOD.DRY_RUN_FILE, project_dir_name=project_dir_name, url=git_url, branch_name="production"
    )  # branch is not important for `DRY_RUN_FILE` and `DRY_RUN_DIR`

    driver_run(connect=connect, config=config)


if __name__ == "__main__":
    run()
