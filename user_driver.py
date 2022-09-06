from config import BaseConfig, DefaultConfig
from connect import CONNECT_METHOD
from driver import run as driver_run


def run():
    """Main starting point of the TODO application to be modified by end users per their need

    This file/function after initial code commit should be added in `.gitignore` so that users
    can safely update the TODO application by simply pulling the latest changes
    """
    git_url: str = ""  # Placeholder for HTTPS based git url
    project_dir_name: str = ""  # Placeholder. Must match project name in git repository
    config: BaseConfig = DefaultConfig(connect_method=CONNECT_METHOD.HTTPS, save_html_reports=False)  # Change per need
    connect_kwargs = dict(git_url=git_url, project_dir_name=project_dir_name)

    driver_run(connect_kwargs=connect_kwargs, config=config)


if __name__ == "__main__":
    run()
