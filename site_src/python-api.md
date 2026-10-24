# Python API

Before the command line tool existed, TODO Notifier was a Python library, and that API is still supported. Use it to **embed a scan** in your own
program (`scan()` returns structured results), or to run the original `driver.run` with custom summary generators and notifiers. Install it with
`pip install todonotifier` (it needs Python 3.10 or newer). The full reference of every class and function is the
[API reference](api/index.html).

The library keeps its own, more conservative defaults than the command line: `ScanSettings()` scans only `.py` files, with git blame, `.gitignore` and
`require_comment` off. See [Configuration](reference/configuration.md) for both columns.

## Scan and use the result

`scan` is a pure function: it scans in place, writes and sends nothing, and returns a `ScanResult` that round-trips through JSON.

```python
import json

from todonotifier.scanner import scan
from todonotifier.settings import ScanSettings

result = scan(ScanSettings(paths=["src"], extensions=["py"], tags=["TODO", "FIXME"], use_git_blame=True, default_due_days=90))

for item in result.overdue():
    print(item.file, item.line, item.author, item.due_date, item.message)

print(len(result.stale()), "stale;", len(result.due_within(7)), "due this week")
by_owner = result.by_author()                       # dict: owner -> list of TodoItem (unowned under "JANE_DOE")
payload = json.dumps(result.to_dict())              # a JSON-serializable dict
```

`ScanSettings` is the schema of every scan option; its fields are the keys of the [config file](reference/configuration.md). To get the same settings the
command line would use, with a config file applied:

```python
from todonotifier.settings_file import resolve_settings

settings = resolve_settings({"tags": ["TODO"]}, start="src")   # CLI-style overrides win; None means "not given"
```

`scan()` raises `ScanException` if there are no paths or a path does not exist. Pass `today=date(...)` for deterministic results in tests.

### What a `TodoItem` has

| Field | Meaning |
|---|---|
| `file`, `line` | POSIX path relative to `ScanResult.root`, and the 1-indexed line |
| `tag`, `message` | The matched tag (as spelled in `tags`) and the text after the tag, owner and date |
| `author`, `author_source` | The owner, and where it came from: `annotation` (written in the comment), `git_blame` or `unknown` |
| `due_date`, `due_source` | The due date, and `explicit` (written as `{date}`), `default` (computed) or `none` |
| `created_date` | The day the line was added, from git blame |
| `is_overdue`, `is_stale`, `days_past_due` | Status against the day of `generated_at`: [overdue and stale](syntax.md#overdue-versus-stale) |
| `web_url` | A deep link to the line, when the repository URL and commit are known |

## The JSON output

`todonotifier scan --format json` prints `ScanResult.to_dict()`. It is described by a JSON Schema (draft 2020-12) that ships in the package as
`todonotifier/schemas/scan_result.schema.json` (`todonotifier.formatters.SCHEMA_PATH` is its path). New optional properties can appear without a version
change; incompatible changes bump `schema_version`.

??? abstract "scan_result.schema.json"

    ```json
    --8<-- "todonotifier/schemas/scan_result.schema.json"
    ```

Read it back with `ScanResult.from_dict(json.loads(text))`, which rejects a `schema_version` newer than the library knows.

## Digests and notifiers from Python

```python
import os

from todonotifier.digest import build_digest, render_markdown, render_text
from todonotifier.notifier import SlackWebhookNotifier
from todonotifier.scanner import scan
from todonotifier.settings import ScanSettings

result = scan(ScanSettings(paths=["src"], use_git_blame=True, default_due_days=90))
print(render_text(build_digest(result, top_n=5)))       # also render_markdown(...) for a GitHub step summary

SlackWebhookNotifier(os.environ["TODO_SLACK_WEBHOOK"]).notify_result(result, reports=[])
```

Notifiers are also created from the config file with `todonotifier.notifier.build_notifiers(project_config.notify)`, which skips tables with
`enabled = false` and reads the secrets from the environment variables named by the `*_env` keys. See [Notifications](notifications.md).

## `driver.run`: reports from a repository

`driver.run` is the original pipeline: it clones or copies a source into a temporary directory, parses it, builds the HTML reports (module-wise,
expired by user, upcoming week) and optionally sends them by email. It keeps the original TODO format, in which `TODO(owner)` and the colon stay part of
the message.

```python
from todonotifier.config import DefaultConfig
from todonotifier.connect import Connect, ConnectMethod
from todonotifier.driver import run as driver_run

connect = Connect(
    connect_method=ConnectMethod.GIT_CLONE,
    project_dir_name="your-project",          # suggested: the same as the project name
    url="https://github.com/your-username/your-repo.git",
    branch_name="main",
)
config = DefaultConfig(save_html_reports=True, ignore_todo_case=True)

# Writes three HTML files to the folder .report under the current working directory
driver_run(connect=connect, config=config)
```

`ConnectMethod` says where the source is:

| Method | Source |
|---|---|
| `GIT_CLONE` | A git URL (HTTPS or SSH), cloned into a temporary directory. `branch_name` matters only here |
| `DRY_RUN_DIR` | A local directory, copied into a temporary directory |
| `LOCAL` | A local directory, scanned in place (nothing is copied) |
| `DRY_RUN_FILE` | A single file. `project_dir_name` must be empty |

`examples/python_api_example.py` in the repository is a script to copy and edit.

### Configuring the scan

```python
from todonotifier.config import DefaultConfig

config = DefaultConfig(
    exclude_dirs={"absolute": ["/path/to/exclude"], "relative": ["node_modules", ".git"], "regex": [r".*__pycache__.*"]},
    exclude_files={"regex": [r".*\.pyc$", r".*\.log$"]},
    file_extensions=["py", "js", "ts"],      # without the leading dot, defaults to ["py"]
    ignore_todo_case=True,
    save_html_reports=True,
)
```

There is a built-in list of directories and files that are never scanned (`DEFAULT_EXCLUDE_DIRS` and `DEFAULT_EXCLUDE_FILES` in `constants.py`);
the flags `flag_default_exclude_dirs` and `flag_default_exclude_files` switch them off.

A config class of your own should be a child of `BaseConfig` (in `todonotifier/config.py`), or simply inherit from `DefaultConfig`. `BaseConfig`
requires `file_extensions` since v2.1.0.

### The generated reports

With `save_html_reports=True` the three reports are stored in `.report/`: the **module-wise summary** (TODOs by file), the **expired TODOs by user**
and the **upcoming week**. Only explicit `{date}`s count as expired or upcoming: a TODO whose *default* due date has passed is stale, and these reports
do not list it. After `driver_run()` the data is also available from the generator objects:

```python
for generator in config.summary_generators:
    print(generator.name, generator.html, generator.container)
```

## Custom summary generators

Write your own report by subclassing `BaseSummaryGenerator` and passing it in `summary_generators`:

```python
from todonotifier.config import DefaultConfig
from todonotifier.models import TODO
from todonotifier.summary_generators import BaseSummaryGenerator


class CustomGenerator(BaseSummaryGenerator):
    def __init__(self):
        super().__init__("Custom Summary", {})

    def generate_summary(self, all_todos_objs: dict[str, list[TODO]]):
        ...  # fill self.container from the TODOs of every file

    def generate_html(self):
        ...  # render self.container to HTML


config = DefaultConfig(summary_generators=[CustomGenerator()], flag_default_summary_generators=True)
```

`generate_summary` and `generate_html` are the two methods to write, and `reset()` (called before each run) clears your state if you override it.

## Custom notifiers

A notifier receives the reports, and optionally the `ScanResult`:

```python
from todonotifier.notifier import BaseNotifier


class PagerNotifier(BaseNotifier):
    def notify(self, summary):
        # `summary` is a list of (report name, report html) pairs
        ...

    def notify_result(self, result, reports):
        # Optional: `result` is the ScanResult. The default calls self.notify(reports)
        ...
```

Subclass `DigestNotifier` instead to get `max_items`, `new_count` and `make_digest(result)` for a digest based notifier. Pass your notifier as
`DefaultConfig(notifier=PagerNotifier())` for `driver.run`. Slack, Teams, webhook and email notifiers are built in, see
[Notifications](notifications.md). Never log a webhook URL or a secret from a notifier.

For the built-in email notifier with `driver.run`:

```python
from todonotifier.notifier import EmailNotifier

notifier = EmailNotifier(sender_email="you@example.com", password="app-password", host="smtp.example.com", port=465, receivers=["team@example.com"])
config = DefaultConfig(save_html_reports=True, notifier=notifier)
```

Read the password from an environment variable in real code (`EmailNotifier.from_env()` does).
