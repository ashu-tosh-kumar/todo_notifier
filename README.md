# TODO Notifier

<div align="center">

[![PyPI version](https://badge.fury.io/py/todonotifier.svg)](https://badge.fury.io/py/todonotifier)
[![Python Support](https://img.shields.io/pypi/pyversions/todonotifier.svg)](https://pypi.org/project/todonotifier/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://pepy.tech/badge/todonotifier)](https://pepy.tech/project/todonotifier)
[![CI](https://img.shields.io/github/actions/workflow/status/ashu-tosh-kumar/todo_notifier/python-app.yml?label=CI)](https://github.com/ashu-tosh-kumar/todo_notifier/actions/workflows/python-app.yml)\n[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/ashu-tosh-kumar/todo_notifier?label=openssf%20scorecard)](https://scorecard.dev/viewer/?uri=github.com/ashu-tosh-kumar/todo_notifier)\n[![Code style: black](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/psf/black)\n[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
<!-- OpenSSF Best Practices: register at https://www.bestpractices.dev/en/projects/new then add: [![OpenSSF Best Practices](https://www.bestpractices.dev/projects/PROJECT_ID/badge)](https://www.bestpractices.dev/projects/PROJECT_ID) -->
<!-- [![GitHub stars](https://img.shields.io/github/stars/ashu-tosh-kumar/todo_notifier.svg)](https://github.com/ashu-tosh-kumar/todo_notifier/stargazers) -->

**Automated TODO tracking and notifications for your codebase**

Never forget a TODO again! Automatically parse, track, and get notified about TODO items
in your code.

[Installation](#installation) •
[Quick Start](#quick-start) •
[Documentation](https://ashu-tosh-kumar.github.io/todo_notifier/) •
[Contributing](#contributing)

<img width="600" alt="TODO Notifier Demo"
src="https://github.com/ashu-tosh-kumar/todo_notifier/assets/37182127/73f4b642-f4ac-4462-a2d7-0fe8f5836aca">

</div>

## Features

- **Smart TODO Detection** - Automatically discovers TODO items across your entire
  codebase
- **Date-based Tracking** - Set completion dates and get notified about overdue items
- **User Assignment** - Assign TODOs to specific team members
- **Multiple Report Types** - Module-wise, user-wise, and deadline-based summaries
- **Email Notifications** - Automated email reports with HTML formatting
- **Flexible Configuration** - Extensive customization options for different workflows
- **Multiple Integration Methods** - Works with Git repositories, local directories, or
  single files
- **Export Options** - Save reports as HTML files for sharing and archiving

## Installation

```bash
pip install todonotifier
```

## Quick Start

### Basic Usage

```python
from todonotifier.config import DefaultConfig
from todonotifier.connect import ConnectMethod, Connect
from todonotifier.driver import run as driver_run

# Configure for a Git repository
git_url = "https://github.com/your-username/your-repo.git"
# Suggested to keep same as project name
project_name = "your-project"

connect = Connect(
    connect_method=ConnectMethod.GIT_CLONE,
    project_dir_name=project_name,
    url=git_url,
    branch_name="main"
)

config = DefaultConfig(
    save_html_reports=True,
    ignore_todo_case=True
)

# Generate TODO reports
# It will generate 3 files by default in folder .report under the current working directory.
driver_run(connect=connect, config=config)
```

### With Email Notifications

```python
from todonotifier.notifier import EmailNotifier

# Set up email notifications
notifier = EmailNotifier(
    sender_email="your-email@gmail.com",
    password="your-app-password",
    host="smtp.gmail.com",
    port=465,
    receivers=["team@company.com"]
)

config = DefaultConfig(
    save_html_reports=True,
    ignore_todo_case=True,
    notifier=notifier
)
```

### Examples

#### Local Directory Scanning

```python
from todonotifier.config import DefaultConfig
from todonotifier.connect import ConnectMethod, Connect
from todonotifier.driver import run as driver_run

# Scan a local project directory
connect = Connect(
    connect_method=ConnectMethod.DRY_RUN_DIR,
    project_dir_name="my-project",
    url="/path/to/your/project"
)

driver_run(connect=connect, config=DefaultConfig())
```

To scan the directory in place, without copying it into a temporary directory, use
`ConnectMethod.LOCAL` instead of `DRY_RUN_DIR`.

#### Structured Scan Results

`scan` is a pure function: it scans in place, writes and sends nothing, and returns a
`ScanResult` that round-trips through JSON.

```python
import json
from todonotifier.scanner import scan
from todonotifier.settings import ScanSettings

result = scan(ScanSettings(paths=["src"], extensions=["py"]))
for item in result.overdue():
    print(item.file, item.line, item.author, item.message)

payload = json.dumps(result.to_dict())
```

#### Single File Analysis

```python
from todonotifier.connect import ConnectMethod, Connect

# Analyze a single file
connect = Connect(
    connect_method=ConnectMethod.DRY_RUN_FILE,
    project_dir_name="single-file",
    url="/path/to/your/file.py"
)
```

### Advanced Configuration

```python
from todonotifier.config import DefaultConfig
# Import it from where it's implemented
from my_summary import CustomSummaryGenerator

config = DefaultConfig(
    # Exclude specific directories
    exclude_dirs={"regex": [r".*/__pycache__/.*", r".*/\.git/.*"]},
    
    # Exclude specific files
    exclude_files={"regex": [r".*\.pyc$", r".*\.log$"]},
    
    # Scan these file extensions (without leading dot). Defaults to ["py"]
    file_extensions=["py", "js", "ts"],

    # Custom settings
    ignore_todo_case=True,
    save_html_reports=True,
    generate_html=True,
    
    # Add custom summary generators
    summary_generators=[CustomSummaryGenerator()],
    flag_default_summary_generators=True
)
```

## Generated Reports

TODO Notifier generates three types of reports as `.html` files by default if
`save_html_reports=True` was set in configuration. All reports generated are stored in
the `.report` directory in the current working directory.

### 1. **Module-wise Summary**

Lists all TODO items organized by file/module for easy code navigation.

### 2. **Expired TODOs by User**

Highlights overdue TODO items assigned to each team member.

### 3. **Upcoming Week TODOs**

Shows TODO items due within the next 7 days.

### Accessing Report Data Programmatically

```python
# After running driver_run(), access the generated data
summary_generators = config.summary_generators

for generator in summary_generators:
    print(f"Report: {generator.name}")
    print(f"HTML: {generator.html}")
    print(f"Data: {generator.container}")
```

### Report Storage

- **HTML Files**: Saved to `.report/` directory when `save_html_reports=True`
- **Email**: Automatically sent when `notifier` is configured
- **Programmatic Access**: Available through summary generator objects

## TODO Format

TODO Notifier supports a flexible format for TODO items in your code:

```python
# Full format with all components
# TODO {2024-12-31} @john_doe Implement user authentication

# Date only
# TODO {2024-12-31} Add error handling

# User only  
# TODO @jane_smith Review this logic

# Simple TODO
# TODO Fix this bug
```

**Format Components:**

- `TODO` - The keyword (case-insensitive option available)
- `{YYYY-MM-DD}` - Optional completion date
- `@username` - Optional assignee
- `message` - Optional description

**Supported Languages:**
Works with any programming language that supports comments (Python, JavaScript, Java,
C++, etc.)

## 🔧 Architecture

### How It Works

1. **Repository Access**: Safely clones/accesses your repository in a temporary location
2. **File Scanning**: Recursively scans all files for TODO patterns using regex
3. **Data Processing**: Parses TODO items extracting dates, assignees, and messages  
4. **Report Generation**: Creates customizable HTML reports and data structures
5. **Notifications**: Sends email notifications with formatted reports

### Key Components

- **Connect Layer**: Handles different source types (Git, local directory, single file)
- **Configuration System**: Flexible settings for scanning, filtering, and reporting
- **Summary Generators**: Pluggable report generators with HTML output
- **Notification System**: Extensible notification framework (Email included)

## Configuration file

Scan options can live in your project instead of on the command line. TODO Notifier reads
`[tool.todonotifier]` from `pyproject.toml`, or a `.todonotifier.toml` file with the same
keys at the top level (drop the `tool.todonotifier` prefix from the table names).

**Discovery:** starting at the scan path (its directory, if it is a file), it walks up to
the git root (or the filesystem root). In each directory `.todonotifier.toml` is checked
first, then `pyproject.toml` (only if it has a `[tool.todonotifier]` table). The first file
found wins. An explicit path overrides discovery. With no file, the defaults apply.

**Precedence**, highest first: command line flags, config file, the command line and config
file defaults (shown below), then the `ScanSettings` defaults. The library API (`ScanSettings()`,
`DefaultConfig`) keeps its own, more conservative defaults.

Unknown keys and wrong types fail with a message naming the key and the file, for example
`Unknown key 'tagz' in pyproject.toml [tool.todonotifier]. Did you mean 'tags'?`.

```toml
# pyproject.toml. Every key is optional; the values shown are the defaults of the command
# line and the config file, unless a comment says otherwise.
[tool.todonotifier]
# Files and directories to scan, relative to THIS file. (ScanSettings default: ["."])
paths = ["src", "tests"]
# File extensions without the dot. "common" expands to py, js, jsx, ts, tsx, java, kt, go,
# rs, rb, php, c, h, cpp, hpp, cs, swift, scala, sh, sql, yaml, yml, toml, html, css, scss
# and md. It can be mixed with others: extensions = ["common", "proto"]
extensions = "common"
# Tags to look for.
tags = ["TODO", "FIXME", "HACK", "XXX"]
# Match tags case insensitively. (default: false)
ignore_case = false
# Count a tag only when it is inside a comment. (default: false)
require_comment = false
# Skip files ignored by git.
respect_gitignore = true
# Fill missing authors and creation dates from git blame.
use_git_blame = true
# An undated TODO becomes stale this many days after it was added. 0 turns this off.
default_due_days = 90
# With commit_sha, builds links to each TODO in the report. (default: unset)
repo_web_url = "https://github.com/your-org/your-repo"
commit_sha = "0123456789abcdef"
# When the command line should exit non-zero: "none", "expired", "stale" or "any".
fail_on = "none"

# Exclusions are ADDED to the built-in ones (DEFAULT_EXCLUDE_DIRS / DEFAULT_EXCLUDE_FILES).
# Each table takes the lists name, pattern (regular expressions) and abs_path.
[tool.todonotifier.exclude_dirs]
name = ["generated", "vendor"]
pattern = [".*_cache"]
[tool.todonotifier.exclude_files]
name = ["legacy.py"]

# Maps git author emails to the handle shown in reports.
[tool.todonotifier.authors]
"ashu@example.com" = "ashu"

# Notifications. Config files never hold secrets: every `*_env` key is the NAME of an
# environment variable, and a key such as `webhook`, `url`, `password` or `token` is rejected.
# Every notifier also takes `enabled` (default: true).
[tool.todonotifier.notify.slack]
webhook_env = "TODO_SLACK_WEBHOOK"   # required
max_items = 20                        # optional

[tool.todonotifier.notify.teams]
webhook_env = "TODO_TEAMS_WEBHOOK"   # required
max_items = 20                        # optional

[tool.todonotifier.notify.webhook]
url_env = "TODO_WEBHOOK_URL"          # required
headers_env = "TODO_WEBHOOK_HEADERS"  # optional: variable holding a JSON object of extra headers

[tool.todonotifier.notify.email]
smtp_host = "smtp.example.com"        # required
smtp_port = 587                       # optional
sender = "todo@example.com"           # required
recipients = ["team@example.com"]     # required
username_env = "TODO_SMTP_USER"       # optional
password_env = "TODO_SMTP_PASSWORD"   # required
starttls = true                       # optional
```

From Python:

```python
from todonotifier.settings_file import resolve_settings

settings = resolve_settings({"tags": ["TODO"]}, start="src")  # CLI-style overrides win; None means "not given"
```

## Customization

### Custom Summary Generators

Users can write their own summary generators and add pass the same in variable
`summary_generators` in configuration. Each summary generator is a child of
`BaseSummaryGenerator` in `summary_generators.py`.

```python
from todonotifier.summary_generators import BaseSummaryGenerator
from todonotifier.models import TODO

class CustomGenerator(BaseSummaryGenerator):
    def __init__(self):
        super().__init__("Custom Summary", {})
    
    def generate_summary(self, all_todos_objs: dict[str, list[TODO]]):
        # Your custom logic here
        pass
    
    def generate_html(self):
        # Generate HTML representation
        pass
```

### Custom Notifications

```python
from todonotifier.notifier import BaseNotifier

class SlackNotifier(BaseNotifier):
    def notify(self, summary):
        # Send to Slack webhook
        pass
```

### File/Directory Filtering

TODO Notifier allows excluding specific folders of the project via absolute address,
relative address or regular expression from being scanned. It has a default list of
folders that are not scanned: `DEFAULT_EXCLUDE_DIRS` in `constants.py`. But the same can
be controlled using the flag `flag_default_exclude_dirs` in configuration.

It also allows excluding specific files of the project via absolute address, relative
address or regular expression from being scanned. It has a default list of files that
are not scanned: `DEFAULT_EXCLUDE_FILES` in `constants.py`. But the same can be
controlled using the flag `flag_default_exclude_files` in configuration.

```python
from todonotifier.config import DefaultConfig

config = DefaultConfig(
    exclude_dirs={
        "absolute": ["/path/to/exclude"],
        "relative": ["node_modules", ".git"],
        "regex": [r".*__pycache__.*"]
    },
    exclude_files={
        "regex": [r".*\.pyc$", r".*\.log$"]
    }
)
```

### File Extensions

By default only `.py` files are scanned. Use `file_extensions` (without the leading dot)
to scan other file types:

```python
from todonotifier.config import DefaultConfig

config = DefaultConfig(file_extensions=["py", "js", "ts"])
```

### Custom Configuration Class

Most of the features are configurable while instantiating configuration class. But users
are free to write another configuration class or simply inherit from `DefaultConfig`.
However, configuration class should be a child of `BaseConfig` in
`todonotifier/config.py`. Note that `BaseConfig` requires `file_extensions` since v2.0.0.

```python
from todonotifier.config import BaseConfig

class CustomConfig(BaseConfig):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Further Custom configuration code
```

## Contributing

We welcome contributions! Here's how you can help:

### Development Setup

```bash
# Clone the repository
git clone https://github.com/ashu-tosh-kumar/todo_notifier.git
cd todo_notifier

# Setup a virtual environment
pyenv virtualenv 3.10 todonotifier

# Install dependencies
pip install poetry  # not limited poetry version as of now
poetry install --with dev

# Set pre-commit hook
pre-commit install

# Run tests
pytest tests
```

### Ways to Contribute

- **Bug Reports**: Open an issue with details and reproduction steps
- **Feature Requests**: Suggest new features or improvements
- **Documentation**: Improve docs, examples, or tutorials
- **Code**: Submit pull requests for bug fixes or features

### Guidelines

- Follow the existing code style (Black, isort, flake8)
- Add tests for new functionality
- Update documentation for new features
- Keep commits focused and descriptive

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for
details.

## Links

- [PyPI Package](https://pypi.org/project/todonotifier/)
- [Documentation](https://ashu-tosh-kumar.github.io/todo_notifier/)
- [Setup
  Guide](https://medium.com/@at-k/streamline-your-todos-with-todo-notifier-for-python-projects-6f95c03a2d34)
- [Issue Tracker](https://github.com/ashu-tosh-kumar/todo_notifier/issues)

## Changelog

### v2.1.0 (Unreleased)

- **Requires Python ≥ 3.10. Python 3.9 users stay on 2.0.x.**
- Added `todonotifier.scanner.scan(settings)`, a side-effect-free scan that works in place
  and returns a structured, JSON-serializable `ScanResult` (`todonotifier.results`) made of
  `TodoItem`s. "No date" is `due_date=None` instead of the `9999-12-25` sentinel.
- Added `todonotifier.settings.ScanSettings`, the schema of every scan option, with
  `ScanSettings.from_config(config)` to convert an existing `BaseConfig`.
- Added `ConnectMethod.LOCAL`, which scans a directory in place without copying it.
  `DRY_RUN_DIR` is unchanged.
- Added `BaseSummaryGenerator.reset()` (does nothing by default; the built-in generators
  clear their container). `driver.run` calls it before generating, so reusing a config
  (including the shared `default_config`) across runs no longer duplicates report rows.
- Added config file support: `[tool.todonotifier]` in `pyproject.toml` or `.todonotifier.toml`,
  found by walking up from the scan path to the git root
  (`todonotifier.settings_file.resolve_settings`, see "Configuration file"). Command line
  flags beat the file, which beats the new command line defaults (all common languages,
  `TODO`/`FIXME`/`HACK`/`XXX`, git blame and `.gitignore` on, 90-day default due date).
  Notifier settings reference environment variable names, never secrets. Added
  `ScanSettings.author_aliases` and `todonotifier.languages` (the `"common"` extension preset).
  New dependency: `tomli` on Python 3.10 (`tomllib` is used on 3.11+).

### v2.0.0 (Unreleased)

- **Breaking Change**: `BaseConfig.__init__` has a new required argument
  `file_extensions` (list of extensions without the leading dot). Custom subclasses of
  `BaseConfig` that call `super().__init__()` must now pass it. `DefaultConfig` is
  unaffected and defaults to `["py"]`.
- **Breaking Change**: `todonotifier.utils.get_files_in_dir` now takes `extensions:
  List[str]` instead of `extension: str`.
- **Behavior Change**: HTML reports are now rendered with Jinja2 templates (new runtime
  dependency `jinja2`) with autoescaping, so characters like `<`, `>` and `&` in TODO
  messages are escaped. Whitespace in the generated HTML also differs.
- Added `file_extensions` config option to scan files other than `.py`
- Files larger than 10 MB are parsed line by line instead of being loaded into memory
- Unparseable completion dates now log a warning with module and line number
- The library no longer calls `logging.basicConfig` on the root logger; only the
  `todonotifier` logger is configured (see `todonotifier/log.py`)

### v1.4.0

- **Breaking Change**: Renamed `CONNECT_METHOD` in `todonotifier.connect` to
  `ConnectMethod`.
- Added accessibility captions to HTML reports
- Security improvements and package upgrades
- Code quality improvements

### v1.3.2

- Updated minimum Python version to 3.9+
- Migrated from setup.py to Poetry
- Package dependency updates

### v1.3.1

- Critical bug fixes (recommended minimum version)

### <v1.3.1

Unfortunately, didn't maintain that.

---

<div align="center">

**Made with ❤️ for developers who care about their TODOs**

[⭐ Star us on GitHub](https://github.com/ashu-tosh-kumar/todo_notifier) •
[🐛 Report Issues](https://github.com/ashu-tosh-kumar/todo_notifier/issues) •
[💬 Discussions](https://github.com/ashu-tosh-kumar/todo_notifier/discussions)

</div>
