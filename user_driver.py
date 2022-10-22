from config import BaseConfig, DefaultConfig
from connect import CONNECT_METHOD, Connect
from driver import run as driver_run


def run():
    """Main starting point of the TODO application to be modified by end users per their need

    This script can be modified to add a for loop for multiple projects

    This file/function after initial code commit should be added in `.gitignore` so that users
    can safely update the TODO application by simply pulling the latest changes
    """
    git_url: str = ""  # Placeholder for HTTPS/SSH based git url
    project_dir_name: str = ""  # Placeholder. Must match project name in git repository.
    config: BaseConfig = DefaultConfig(save_html_reports=True, ignore_todo_case=True)  # Change per need
    connect = Connect(connect_method=CONNECT_METHOD.GIT_CLONE, project_dir_name=project_dir_name, url=git_url)

    driver_run(connect=connect, config=config)


if __name__ == "__main__":
    run()
