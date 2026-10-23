# TODO Notifier

<div align="center">

[![PyPI version](https://badge.fury.io/py/todonotifier.svg)](https://badge.fury.io/py/todonotifier)
[![Python Support](https://img.shields.io/pypi/pyversions/todonotifier.svg)](https://pypi.org/project/todonotifier/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://pepy.tech/badge/todonotifier)](https://pepy.tech/project/todonotifier)
[![CI](https://img.shields.io/github/actions/workflow/status/ashu-tosh-kumar/todo_notifier/python-app.yml?label=CI)](https://github.com/ashu-tosh-kumar/todo_notifier/actions/workflows/python-app.yml)
[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/ashu-tosh-kumar/todo_notifier?label=openssf%20scorecard)](https://scorecard.dev/viewer/?uri=github.com/ashu-tosh-kumar/todo_notifier)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
<!-- OpenSSF Best Practices: register at https://www.bestpractices.dev/en/projects/new then add: [![OpenSSF Best Practices](https://www.bestpractices.dev/projects/PROJECT_ID/badge)](https://www.bestpractices.dev/projects/PROJECT_ID) -->
<!-- [![GitHub stars](https://img.shields.io/github/stars/ashu-tosh-kumar/todo_notifier.svg)](https://github.com/ashu-tosh-kumar/todo_notifier/stargazers) -->

**Find every TODO in your code, see who owns it and how old it is, and fail CI when one expires.**

[Quick Start](#quick-start) •
[Command line](#command-line) •
[Configuration](#configuration-file) •
[Notifications](#notifications) •
[Python API](#python-api) •
[Documentation](https://ashu-tosh-kumar.github.io/todo_notifier/) •
[Contributing](#contributing)

<img width="600" alt="TODO Notifier Demo"
src="https://github.com/ashu-tosh-kumar/todo_notifier/assets/37182127/73f4b642-f4ac-4462-a2d7-0fe8f5836aca">

</div>

## Features

- **Command Line Tool** - `todonotifier scan .` works with zero config: table, JSON, GitHub
  annotations, SARIF and Markdown output, `--fail-on` for CI and `--since` for pull requests
- **Smart TODO Detection** - Automatically discovers TODO items across your entire
  codebase
- **Date-based Tracking** - Set completion dates and get notified about overdue items
- **User Assignment** - Assign TODOs to specific team members
- **Multiple Report Types** - Module-wise, user-wise, and deadline-based summaries
- **Email Notifications** - Automated email reports with HTML formatting
- **Chat Notifications** - Slack, Microsoft Teams and webhook digests
- **Flexible Configuration** - Extensive customization options for different workflows
- **Multiple Integration Methods** - Works with Git repositories, local directories, or
  single files
- **Export Options** - Save reports as HTML files for sharing and archiving

## Quick Start

1. **Install** the command line tool in its own environment (`pip install todonotifier` also works and gives you the
   [Python API](#python-api)):

   ```bash
   pipx install todonotifier
   ```

2. **Scan** your code. It needs no config: it finds `TODO`, `FIXME`, `HACK` and `XXX` in comments of the common languages,
   skips what `.gitignore` excludes, and asks `git blame` who wrote each line and when.

   ```text
   $ todonotifier scan .
   LOCATION          TAG   OWNER  DUE                     MESSAGE
   src/app.py:10     TODO  alice  2026-04-01 overdue 30d  Remove the legacy path
   src/old.py:3      TODO  alice  2026-01-01 stale 120d   Rewrite this module
   src/api.py:80     TODO  carol  2026-05-03 due in 2d    Cache the lookup
   src/misc.py:1     TODO  -      -                       Think about naming

   4 TODOs · 1 overdue · 1 stale · 1 unowned
   ```

3. **Configure** (optional): write a commented starter config, then edit it (see [Configuration file](#configuration-file)).

   ```bash
   todonotifier init
   ```

4. **Run it in CI** and fail the build when a TODO has expired, with annotations on the pull request. A minimal GitHub
   Actions workflow (`fetch-depth: 0` is needed for `git blame`):

   ```yaml
   name: TODOs
   on: [push, pull_request]
   permissions:
     contents: read
   jobs:
     todos:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v7
           with:
             fetch-depth: 0
         - uses: actions/setup-python@v6
           with:
             python-version: "3.12"
         - run: pip install todonotifier
         - run: todonotifier scan . --fail-on expired --format github
   ```

   An undated TODO becomes **stale** 90 days after it was added; a TODO whose `{date}` has passed is **overdue**.
   `--fail-on expired` fails on overdue TODOs only. See [Command line](#command-line) for all flags and formats.

## Command line

`todonotifier scan .` needs no config (see [Quick Start](#quick-start)). It scans the common languages (see "Configuration file"), skips what
`.gitignore` excludes, only counts tags inside comments, and asks `git blame` who wrote each line and when. An
undated TODO becomes **stale** 90 days after it was added; a TODO whose `{date}` has passed is **overdue**.

Colors are used only when stdout is a terminal, `NO_COLOR` is unset and there is no `--output`.

### Commands

| Command | What it does |
|---|---|
| `todonotifier scan [PATH ...]` | Scan and print the TODOs (default path `.`, or the `paths` of the config file). Paths may be files, e.g. the staged files from pre-commit. |
| `todonotifier report [PATH ...] [--out DIR]` | Write the HTML reports (module-wise, expired by user, upcoming week) to `DIR` (default `.report`) and print their paths. Same as `scan --format html`. |
| `todonotifier notify [PATH ...]` | Scan, then send the digest to every notifier of the config file (Slack, Teams, webhook, email, see "Notifications"). All notifiers are tried and every failure is printed. |
| `todonotifier init [--pyproject \| --standalone]` | Append a commented `[tool.todonotifier]` section to `pyproject.toml` (if it exists and has none), else create `.todonotifier.toml`. Never overwrites anything. |
| `todonotifier --version` | Print the version. |

`python -m todonotifier ...` does the same as the `todonotifier` command. The exit codes are listed under [Exit codes](#exit-codes).

### Flags

`scan`, `report` and `notify` share these. A flag beats the config file, which beats the built-in defaults.

| Flag | Meaning |
|---|---|
| `--config PATH` | Use this config file instead of looking for `.todonotifier.toml` / `pyproject.toml` |
| `--tags TODO,FIXME` | Comma separated tags (default `TODO,FIXME,HACK,XXX`) |
| `--ext py,js` | Comma separated file extensions; `common` is the preset of common languages (default) |
| `--ignore-case` | Match tags case insensitively |
| `--no-blame` | Do not run `git blame`: no authors, ages or default due dates |
| `--default-due-days N` | An undated TODO turns stale `N` days after it was added (default 90, `0` disables) |
| `--no-require-comment` | Also report tags that are not inside a comment |
| `--no-gitignore` | Also scan files that `.gitignore` excludes |
| `--since GIT_REF` | Only report TODOs on lines added or changed since `GIT_REF` (e.g. `HEAD~1`, `origin/main`). Needs a git repository; new files count in full |
| `--fail-on {none,expired,stale,any}` | Exit with 1 if such a TODO exists (default `none`, or `fail_on` of the config file). `expired`: an explicit `{date}` has passed. `stale`: also default due dates. `any`: any TODO. Judged after `--since` |
| `--format {table,json,github,markdown,sarif,html}` | Output format (default `table`; `html` for `report`; `notify` prints nothing unless given) |
| `--output FILE` | Write the result to `FILE` instead of stdout (for `html`: the directory for the report files) |
| `-q`, `--quiet` / `-v`, `--verbose` | Log errors only / debug logs and tracebacks. Logs go to stderr, results to stdout |

### Output formats

- `table`: aligned columns and a summary line (shown above).
- `json`: `ScanResult.to_dict()`, documented by the JSON Schema
  [`todonotifier/schemas/scan_result.schema.json`](todonotifier/schemas/scan_result.schema.json) (draft 2020-12, shipped
  in the package; `todonotifier.formatters.SCHEMA_PATH` is its path). Dates are ISO strings, "no due date" is `null`.
  New optional properties can appear without a version change; incompatible changes bump `schema_version`.
- `github`: [workflow commands](https://docs.github.com/actions/reference/workflow-commands-for-github-actions) that GitHub
  shows as annotations on the pull request. Overdue TODOs are errors, stale ones and those due within 7 days are warnings,
  the rest are notices. Paths are relative to the repository root, even if you scan a subdirectory.
- `markdown`: the digest of the "Notifications" section, e.g. for `$GITHUB_STEP_SUMMARY`.
- `sarif`: SARIF 2.1.0 for GitHub code scanning (one rule per tag, same levels as `github`).
- `html`: the three built-in reports as files.

```text
$ todonotifier scan . --format github --since origin/main
::error file=src/app.py,line=10,title=TODO overdue by 30d::Remove the legacy path (@alice, due 2026-04-01)
::warning file=src/old.py,line=3,title=TODO stale by 120d::Rewrite this module (@alice, default due 2026-01-01)
::notice file=src/misc.py,line=1,title=TODO::Think about naming
4 TODOs: 1 overdue, 1 stale, 1 unowned
```

In a GitHub Actions step (`fetch-depth: 0` is needed for `git blame` and `--since`):

```yaml
- uses: actions/checkout@v4
  with: { fetch-depth: 0 }
- run: pipx install todonotifier
- run: todonotifier scan . --format github --since origin/${{ github.base_ref }} --fail-on expired
```

GitHub shows at most 10 error, 10 warning and 10 notice annotations per step, so `--since` keeps pull requests readable.

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
# Count a tag only when it is inside a comment (see "TODO Format"). (ScanSettings default: false)
require_comment = true
# Skip files ignored by git (inside a git repository, the files are listed with
# `git ls-files --cached --others --exclude-standard`; elsewhere the tree is walked).
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

## Notifications

`ScanResult` (see "Structured Scan Results") can be turned into a **digest** and sent to Slack, Microsoft Teams, any webhook or email.
The digest (`todonotifier.digest.build_digest`) has these totals: open, overdue, stale, due this week, unowned and, when known, new TODOs.
Below them come three sections, **Overdue**, **Stale** and **Due this week**, each grouped by owner (most items first, unowned last) with the
most overdue item first and a deep link when the repository URL and commit are known. "Overdue" means an explicit `{date}` has passed, "Stale"
means a default due date has passed (see `default_due_days`). Each section shows at most `max_items` TODOs (default 10) and ends with
"...and N more".

```python
import os

from todonotifier.digest import build_digest, render_markdown, render_text
from todonotifier.notifier import SlackWebhookNotifier
from todonotifier.scanner import scan
from todonotifier.settings import ScanSettings

result = scan(ScanSettings(paths=["src"], use_git_blame=True, default_due_days=90))
print(render_text(build_digest(result, top_n=5)))  # also render_markdown(...) for a GitHub step summary

SlackWebhookNotifier(os.environ["TODO_SLACK_WEBHOOK"]).notify_result(result, reports=[])
```

Rules shared by all HTTP notifiers: the standard library only (`urllib`), a 10 s timeout, 2 retries with exponential backoff (1 s, 2 s) on HTTP 5xx,
429 (a numeric `Retry-After` is honoured, up to 30 s) and network errors, and no retry on other 4xx errors. When delivery finally fails a
`NotificationError` is raised. Only `https://` URLs are accepted (`http://` only for `localhost` and `127.0.0.1`, for tests). A webhook URL is a
secret: it, the request headers and the response body never appear in logs or exception messages (logs say, for example,
`Slack webhook POST failed with HTTP 500 (attempt 2/3)`). Keep them in environment variables, and name the variable in the config file.

Notifiers are also created from the config file with `todonotifier.notifier.build_notifiers(project_config.notify)`, which skips tables with
`enabled = false` and reads the secrets from the environment variables named by the `*_env` keys (a missing variable raises `NotifierConfigError`,
which names the variable and never a value). The keys of each table are listed in "Configuration file".

### Slack

1. Create an [incoming webhook](https://api.slack.com/messaging/webhooks) for the channel and store its URL in a secret, e.g. `TODO_SLACK_WEBHOOK`.
2. Add the table to your config (or use `SlackWebhookNotifier(url, max_items=10)` in Python):

```toml
[tool.todonotifier.notify.slack]
webhook_env = "TODO_SLACK_WEBHOOK"
max_items = 10
```

The message is a Block Kit message: a header, a section with the totals, and one section per digest group, with `<url|file:line>` links and a
plain `text` fallback for notifications. It respects Slack's limits (3000 characters per section, 50 blocks) and says how many TODOs did not fit.

### Microsoft Teams

⚠️ **Verify against the current Microsoft documentation.** Microsoft is retiring the Office 365 connectors in favour of Power Automate Workflows,
and the format may change.

1. In the channel, create a workflow from the template "Post to a channel when a webhook request is received" (trigger "When a Teams webhook
   request is received") and copy its URL into a secret, e.g. `TODO_TEAMS_WEBHOOK`.
2. Add the table:

```toml
[tool.todonotifier.notify.teams]
webhook_env = "TODO_TEAMS_WEBHOOK"
max_items = 10
```

It posts `{"type": "message", "attachments": [{"contentType": "application/vnd.microsoft.card.adaptive", ...}]}` with an Adaptive Card (version
1.4) made of `TextBlock`s and a `FactSet`. Teams limits a message to about 28 KB, so keep `max_items` modest.

### Generic webhook

POSTs `{"event": "todonotifier.scan", "result": <ScanResult.to_dict()>, "digest": {"open": ..., "overdue": ..., "stale": ..., "due_soon": ...,
"unowned": ...}}` as JSON, for Discord bridges, Zapier, n8n or internal tools. `headers_env` names a variable that holds a JSON object of extra
headers, e.g. `{"Authorization": "Bearer ..."}`; the headers are not forwarded if the server redirects.

```toml
[tool.todonotifier.notify.webhook]
url_env = "TODO_WEBHOOK_URL"
headers_env = "TODO_WEBHOOK_HEADERS"
```

### Email

`EmailNotifier(sender_email, password, host, port, receivers)` keeps working as before (SSL, usually port 465, `notify(reports)` sends the HTML
reports). New: `starttls=True` connects on a plain port (usually 587) and upgrades with STARTTLS, `username=` is the login if it is not the sender,
and `EmailNotifier.from_env()` reads the settings from the environment:

| Variable (prefix `TODO_SMTP_`) | Meaning |
|---|---|
| `HOST`, `SENDER`, `RECIPIENTS` (comma separated), `PASSWORD` | required |
| `PORT` | optional, default 587 with `STARTTLS`, else 465 |
| `USERNAME` | optional, default: the sender |
| `STARTTLS` | optional, `1`/`true`/`yes`/`on`, default off |

With `notify_result`, the email has the digest (a plain text part and an HTML part, escaped) and the generated HTML reports below it. In the
config file, `smtp_port` defaults the same way (587 with `starttls = true`, else 465):

```toml
[tool.todonotifier.notify.email]
smtp_host = "smtp.example.com"
smtp_port = 587
starttls = true
sender = "todo@example.com"
recipients = ["team@example.com"]
username_env = "TODO_SMTP_USER"       # optional
password_env = "TODO_SMTP_PASSWORD"
```

### Custom notifiers

`BaseNotifier.notify_result(result, reports)` is called with the `ScanResult` next to the reports. Its default implementation calls
`notify(reports)`, so notifiers written for earlier versions keep working. Subclass `DigestNotifier` (it provides `max_items`, `new_count` and
`make_digest(result)`) to build your own digest based notifier.

## TODO Format

TODO Notifier supports a flexible format for TODO items in your code:

```python
# Full format with all components
# TODO {2024-12-31} @john_doe Implement user authentication

# Date only
# TODO {2024-12-31} Add error handling

# User only
# TODO @jane_smith Review this logic

# Owner in parentheses (Google style), the same as @user
# TODO(jane_smith): Review this logic
# FIXME(jane_smith) {2024-12-31} Handle the empty case

# Other tags work the same way
# FIXME: Crashes on empty input
# HACK @john_doe {2024-12-31} Remove after the migration

# Simple TODO
# TODO Fix this bug
```

**Format Components:**

- `TODO` - The tag. `TODO` by default; set `tags` (for example `["TODO", "FIXME", "HACK", "XXX"]`)
  to look for more. Tags are matched as whole words, so `TODO_LIST`, `TODOS` and `todonotifier`
  are not tags, but `TODO:` and `TODO(` are. `ignore_case` also matches `todo` and `Todo`.
- `(owner)` - Optional owner right after the tag, the same as `@owner`
- `{YYYY-MM-DD}` - Optional completion date
- `@username` - Optional assignee
- `:` - One optional colon after the tag, owner, date or user is dropped from the message,
  so `# TODO: fix this` has the message `fix this`
- `message` - Optional description

`scan()` (and the command line) read the full format above. `driver.run` keeps the original
format, in which `TODO(owner)` and the colon stay part of the message. Only the word-boundary
fix applies to both.

**Supported Languages:**
Works with any programming language that supports comments. With `require_comment` a tag counts
only when it is inside a comment, which TODO Notifier knows for these extensions: `py`, `sh`, `rb`,
`yaml`, `yml`, `toml` (`#`), `js`, `jsx`, `ts`, `tsx`, `java`, `kt`, `go`, `c`, `h`, `cpp`, `hpp`, `cs`,
`swift`, `rs`, `php`, `scala`, `scss` (`//` and `/* */`), `css` (`/* */`), `sql`, `lua` (`--`) and
`html`, `md` (`<!-- -->`). Files with another extension are searched everywhere.

`require_comment` is a heuristic, not a parser (see the `todonotifier.languages` docstring for the
limits). A tag in a string, such as `print("TODO list")`, is ignored; so is a tag in a docstring,
since a docstring is a string. Code fences in Markdown are skipped. It is on by default in the
command line and config file, and off in the library (`ScanSettings`, `DefaultConfig`).

## Exit codes

| Code | Meaning |
|---|---|
| `0` | OK |
| `1` | The `--fail-on` condition was met (for `notify`, this wins over a failed notification) |
| `2` | Usage or config error: a bad flag or config file, a path that does not exist, an unknown `--since` ref or no git repository for it, no notifier configured |
| `3` | Unexpected runtime error (the traceback is shown with `-v`), or a notification could not be delivered |

Errors are one line on stderr, for example `todonotifier: error: Unknown key 'tagz' in pyproject.toml [tool.todonotifier]. Did you mean 'tags'?`.

## Python API

Before the command line tool existed, TODO Notifier was a Python library, and that API is still supported. Use it to
embed a scan in your own program (`scan()` returns structured results) or to run the original `driver.run` with
custom summary generators and notifiers. `examples/python_api_example.py` is a legacy example script that you can
copy and edit.

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

class PagerNotifier(BaseNotifier):
    def notify(self, summary):
        # `summary` is a list of (report name, report html) pairs
        pass

    def notify_result(self, result, reports):
        # Optional: `result` is the ScanResult. The default calls `self.notify(reports)`
        pass
```

Slack, Teams, webhook and email notifiers are built in, see "Notifications".

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
`todonotifier/config.py`. Note that `BaseConfig` requires `file_extensions` since v2.1.0 (the first release after 1.4.0).

```python
from todonotifier.config import BaseConfig

class CustomConfig(BaseConfig):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Further Custom configuration code
```

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
- **Notification System**: Extensible notification framework (Email, Slack, Teams and webhook included)

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

### v2.1.0

- **Requires Python ≥ 3.10. Python 3.9 users stay on 1.x** (1.4.0 is the last release for 3.9).
- **2.0.0 was never released to PyPI** (the latest release before this one is 1.4.0). Its changes are part of this
  release, and so are its breaking changes, which are listed first. Upgrading from 1.x, read them.
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
- Added git-aware ownership and TODO age (`todonotifier.git_meta`, used by `scan()` when
  `ScanSettings.use_git_blame` is on; off by default in the library). One `git blame` per file
  that has TODOs, run in parallel, fills `TodoItem.author` (`author_source="git_blame"`, only
  when there is no `@user`, mapped through `author_aliases`) and `created_date`. With
  `default_due_days`, an undated TODO gets `due_date = created_date + days` and
  `due_source="default"`, so it becomes *stale*, never *overdue*. The repository URL and
  commit (for `web_url` deep links) are detected from `GITHUB_SERVER_URL`/`GITHUB_REPOSITORY`/
  `GITHUB_SHA` or the `origin` remote (credentials are always stripped). If `git` is missing, the
  path is not a repository or the clone is shallow, the scan still works and logs one warning
  (for shallow clones: use `fetch-depth: 0`). Uncommitted lines have no author and are dated today.

- Fixed false positives in the TODO parser (it affects `driver.run` too). A tag is now matched on
  word boundaries, so `from todonotifier.config import X` with `ignore_todo_case=True` and
  `TODO_REGEX_PATTERN = ...` are no longer reported as TODOs.
- Added configurable tags, language-aware comment detection and `.gitignore` support to `scan()`:
  `ScanSettings.tags` (`TODO` by default, `FIXME`/`HACK`/`XXX` on the command line), reported in
  `TodoItem.tag` (and the new `models.TODO.tag`, default `"TODO"`);
  `ScanSettings.require_comment` (a tag must come after a comment marker of the file's language, or
  be inside a block comment; `todonotifier.languages.COMMENT_SYNTAX`; on by default in the command
  line and config file) and `ScanSettings.respect_gitignore` (`git ls-files` inside a git repository).
  `parse_files_for_todo_items` takes optional `tags` and `require_comment`. `TAG(owner)` is accepted
  as an owner and one colon after the tag, owner, date or user is dropped (`# TODO(ashu): fix`).
  Binary files are skipped, text is read as UTF-8 with `errors="replace"`, and `.git` is excluded by
  default.

- Added chat and webhook notifications (see "Notifications"): `todonotifier.digest` builds a channel-neutral digest of a
  `ScanResult` (totals, then Overdue, Stale and Due this week grouped by owner, top N each with "...and N more", deep links) and renders it as
  text or Markdown. New notifiers `SlackWebhookNotifier` (Block Kit), `TeamsWebhookNotifier` (Workflows, Adaptive Card) and `WebhookNotifier`
  (JSON), all on `urllib` with a 10 s timeout, 2 retries on 5xx/429 and no URLs, headers or bodies in logs or errors (`NotificationError`).
  `BaseNotifier.notify_result(result, reports)` (default: calls `notify(reports)`, so existing notifiers are unchanged), `EmailNotifier`
  gets `starttls`, `username`, `from_env()` and a digest email, and `build_notifiers()` creates notifiers from the config file's
  `[notify.*]` tables.

- Added the `todonotifier` command line tool (also `python -m todonotifier`), see "Command line": `scan`, `report`, `notify` and `init`,
  with flags for tags, extensions, blame, default due days, `--since GIT_REF` (only TODOs on changed lines), `--fail-on`
  (`none`/`expired`/`stale`/`any`), `--format` (`table`, `json`, `github` annotations, `markdown`, `sarif`, `html`) and `--output`. Exit codes:
  0 OK, 1 `--fail-on` met, 2 usage or config error, 3 unexpected error. The JSON output has a JSON Schema,
  `todonotifier/schemas/scan_result.schema.json`. New modules `todonotifier.cli` and `todonotifier.formatters`; `git_meta.changed_lines`
  and `git_meta.filter_git_listed`. Passing many files to `scan()` (pre-commit) now takes one `git ls-files` call instead of two per file.
  `utils.store_html` returns the path it wrote and writes UTF-8. Development: `jsonschema` is a new dev dependency.

- Release and project housekeeping: CI runs on Python 3.10 to 3.14 with `black`, `isort`, `flake8`, 100% coverage
  and a self-check (`todonotifier scan . --fail-on expired`); `.github/workflows/release.yml` publishes tagged
  releases to PyPI with Trusted Publishing and creates the GitHub Release; this repository's own config is in
  `[tool.todonotifier]`; the legacy `user_driver.py` moved to `examples/python_api_example.py`; the committed
  `.report/` output was removed and is git-ignored.

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
