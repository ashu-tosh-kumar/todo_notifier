# TODO Notifier

- [TODO Notifier](#todo-notifier)
  - [Description](#description)
  - [How to use?](#how-to-use)
    - [Method 1: As a pip package](#method-1-as-a-pip-package)
    - [Method 2: Directly cloning from GitHub](#method-2-directly-cloning-from-github)
  - [Technical Details](#technical-details)
    - [Working](#working)
    - [Salient Features](#salient-features)
    - [Other Salient Features](#other-salient-features)

## Description

More often than not, we put some TODO items in code and forget about them. Sometimes, we think of coming back to a TODO item by some date but miss it being too busy with some other development.

TODO Notifier aims to solve this problem. It parses through any project, collects all the todo items and send automated reminders about them *[Upcoming feature]*.

Recommended format to write TODO items**

`TODO {2022-05-22} @user_name msg`

Above format has following components

- `TODO` in capital (though users can make it case insensitive by setting the same in  `config.py`). It need not to be starting word of the line. For a host of valid examples, please check `tests/sample_test_file.py` and `tests/sample_test_file2.py`
- [Optional] TODO is followed a date in `YYYY-MM-DD` format within curly brackets. The respective TODO item is expected to be completed by end of this date
- [Optional] Date is followed by a unique user name accompanied by `@`
- [Optional] User name is followed by the usual message/comment of the respective TODO item

However, the relative position of the `TODO` item, date inside `{}` brackets, username with `@` and message should be as recommended above.

The framework is robust in the sense that if the TODO item misses some data like date and/or message and/or username etc., the respective TODO item will still be picked up by the TODO Notifier. However without relevant information, certain functionalities may not work. For e.g. without date, it cannot know if the TODO item has overshoot its expected date of completion.

## How to use?

### Method 1: As a pip package

Install TODO Notifier by running `pip install todonotifier`

Then you can use below code to try the TODO Notifier.

```python
from todonotifier.config import DefaultConfig
from todonotifier.connect import CONNECT_METHOD, Connect
from todonotifier.driver import run as driver_run

git_url: str = ""  # Placeholder for HTTPS/SSH based git url. It could also be a local folder address
project_dir_name: str = ""  # Placeholder. Must match project name in git repository/local folder

config = DefaultConfig(save_html_reports=True, ignore_todo_case=True)  # Change per need
connect = Connect(connect_method=CONNECT_METHOD.GIT_CLONE, project_dir_name=project_dir_name, url=git_url, branch_name="production")  # If using a local folder address in `git_url`, then change `connect_method` to `CONNECT_METHOD.DRY_RUN_DIR`

driver_run(connect=connect, config=config)  # This would generate (by default) 3 summary files in `.report` folder in current working directory
```

### Method 2: Directly cloning from GitHub

Clone using `git clone https://github.com/ashu-tosh-kumar/todo_notifier.git`

Then you can use the `user_driver.py` file to run it.

Also, if you plan to use it simply by cloning the repository, you can put your custom code in `user_driver.py` as the same will not be updated and is added for end users.

## Technical Details

### Working

- TODO Notifier copies/clones the respective repository into a temporary location to avoid the risk of modifying any file.
- It then reads through all the files in the project and collects all the TODO items
- It then generates the summaries as specified in the configuration
- Finally it sends the notifications (by default via Emails) to respective users and a group as a whole *[Upcoming feature]*.

### Salient Features

- Allows excluding specific folders of the project via absolute address, relative address or regular expression from being scanned. It has a default list of folders that are not scanned: `DEFAULT_EXCLUDE_DIRS` in `constants.py`. But the same can be controlled using the flag `flag_default_exclude_dirs` in `config/DefaultConfig`

- Allows excluding specific files of the project via absolute address, relative address or regular expression from being scanned. It has a default list of files that are not scanned: `DEFAULT_EXCLUDE_FILES` in `constants.py`. But the same can be controlled using the flag `flag_default_exclude_files` in `config/DefaultConfig`

- Provides three default summary generators. Summaries are how TODO Notifier shares the information about TODO items. Each summary is essentially an HTML document that can be easily shared. The default summary generation can be controlled by flag: `flag_default_summary_generators` in `config/DefaultConfig`.
  - Module wise list of all TODO items
  - User wise list of TODO items expired already
  - User wise list of TODO items that are supposed to expire in the upcoming week

- Flag `save_html_reports` can be used to control whether to save the generated summaries as files. If yes, it will store all generated summaries in folder `.report` locally

- Users can write their own summary generators and add pass the same in variable `summary_generators` in `config/DefaultConfig`. Each summary generator is a child of `BaseSummaryGenerator` in `summary_generators.py`

- Provides default implementation of sending notifications via Email as `EmailNotifier` in `notifications.py`. More ways of notifications can be added easily by inheriting from `BaseNotifier`

- Most of the features are configurable via configuration file. Configuration must be a child class of `BaseConfig` in `config.py`. It provides a default configuration class: `DefaultConfig` in `config.py` that can also be configured easily via various flag parameters. But users are free to write another configuration class or simply inherit from `DefaultConfig`

- Provides two ways of dry running the code locally viz. `CONNECT_METHOD.DRY_RUN_FILE` to dry run on a single local file and `CONNECT.DRY_RUN_DIR` to dry run on an entire local directory/project.

- `user_driver.py` provides the single point of access for users. It can be modified accordingly to run the code. This file is added to `.gitignore` and is not expected to be updated and so users can safely modify this file.

### Other Salient Features

- All code in Python 3
- Using following pre-commit hooks to keep code clean and nice during development
  - black
  - flake8
  - isort
  - requirements-txt-fixer
- Almost 100% test coverage for whole repository and we intend to keep it that way
- Integrated GitHub flows to keep repo clean and updated
  - CodeQL
  - OSSAR
  - Python application
