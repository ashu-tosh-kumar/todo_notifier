# TODO Notifier

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/todonotifier.svg)](https://pypi.org/project/todonotifier/)
[![Python Support](https://img.shields.io/pypi/pyversions/todonotifier.svg)](https://pypi.org/project/todonotifier/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/todonotifier)](https://pepy.tech/projects/todonotifier)
[![CI](https://img.shields.io/github/actions/workflow/status/ashu-tosh-kumar/todo_notifier/python-app.yml?label=CI)](https://github.com/ashu-tosh-kumar/todo_notifier/actions/workflows/python-app.yml)
[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/ashu-tosh-kumar/todo_notifier?label=openssf%20scorecard)](https://scorecard.dev/viewer/?uri=github.com/ashu-tosh-kumar/todo_notifier)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
<!-- OpenSSF Best Practices: register at https://www.bestpractices.dev/en/projects/new then add: [![OpenSSF Best Practices](https://www.bestpractices.dev/projects/PROJECT_ID/badge)](https://www.bestpractices.dev/projects/PROJECT_ID) -->
<!-- [![GitHub stars](https://img.shields.io/github/stars/ashu-tosh-kumar/todo_notifier.svg)](https://github.com/ashu-tosh-kumar/todo_notifier/stargazers) -->

**Find every TODO in your code, see who owns it and how old it is, and fail CI when one expires.**

[Documentation](https://ashu-tosh-kumar.github.io/todo_notifier/) •
[Quickstart](https://ashu-tosh-kumar.github.io/todo_notifier/quickstart/) •
[Command line](https://ashu-tosh-kumar.github.io/todo_notifier/cli/) •
[Configuration](https://ashu-tosh-kumar.github.io/todo_notifier/reference/configuration/) •
[CI](https://ashu-tosh-kumar.github.io/todo_notifier/ci/) •
[Notifications](https://ashu-tosh-kumar.github.io/todo_notifier/notifications/) •
[Python API](https://ashu-tosh-kumar.github.io/todo_notifier/python-api/) •
[Contributing](#contributing)

<!-- Regenerate the GIF with `vhs assets/demo.tape` (see the header of the tape). PyPI renders neither relative image paths nor relative links, so this
     README uses absolute URLs for both (the image is served from `main`, the release branch, and shows once a release is merged there). -->
<img width="720" alt="Terminal recording: todonotifier scan, scan --fail-on expired with its exit code 1, and scan --format github" src="https://raw.githubusercontent.com/ashu-tosh-kumar/todo_notifier/main/assets/demo.gif">

</div>

TODO Notifier is a **TODO deadline reminder** and **FIXME tracker**: it finds `TODO`, `FIXME`, `HACK` and `XXX` comments, gives each one an owner (from
`@user`, `TODO(user)` or `git blame`) and a due date, flags every **overdue TODO**, and tells your team in the terminal, in CI, and by Slack, Teams,
webhook or email. Use it as a lightweight **technical debt tracker** that fails the build when a TODO has expired. It needs no config to start.

## Three commands

```bash
pipx install todonotifier                  # install it in its own environment (pip install todonotifier works too)
todonotifier scan .                        # every TODO with its owner and due date
todonotifier scan . --fail-on expired      # exit 1 if a TODO's {date} has passed: put this in CI
```

```text
$ todonotifier scan .
LOCATION      TAG    OWNER  DUE                      MESSAGE
src/api.py:2  TODO   carol  2030-01-15 due in 1179d  Cache the lookup
src/api.py:5  HACK   bob    2027-01-22 due in 90d    Think about naming
src/app.py:2  TODO   alice  2026-04-01 overdue 206d  Remove the legacy path
src/old.py:1  FIXME  alice  2026-04-10 stale 197d    Rewrite this module

4 TODOs · 1 overdue · 1 stale · 0 unowned
```

Write TODOs the way you already do. Add an owner and a date when you want a deadline: `# TODO(carol) {2026-12-31}: Cache the lookup`.
Undated TODOs get a default due date 90 days after `git blame` says they were added, so they turn *stale*; a TODO whose `{date}` has passed is
*overdue*. The [5-minute Quickstart](https://ashu-tosh-kumar.github.io/todo_notifier/quickstart/) takes you from install to a CI check and a pre-commit hook.

## Features

- **Command line tool:** zero config; table, JSON, GitHub annotations, SARIF and Markdown output; `--fail-on` for CI; `--since` for pull requests
- **Owners and ages from `git blame`,** or written in the comment (`@user`, `TODO(user)`); a default due date for undated TODOs
- **GitHub Action:** annotations, a job summary, a sticky pull request comment, `fail-on` and a weekly digest
  ([`integrations/github-action`](https://github.com/ashu-tosh-kumar/todo_notifier/blob/main/integrations/github-action/README.md))
- **pre-commit hook:** stop a commit that touches an overdue TODO
- **Slack, Microsoft Teams, webhook and email digests**
- **Many languages:** comment-aware detection for 37 file extensions, so strings and docstrings are not reported
- **Config file:** `.todonotifier.toml` or `[tool.todonotifier]` in `pyproject.toml`
- **Python API:** `scan()` returns structured results; custom report generators and notifiers
- **Private:** nothing leaves your machine unless you configure a notifier

## Documentation

The docs are at **<https://ashu-tosh-kumar.github.io/todo_notifier/>**:

| | |
|---|---|
| [Quickstart (5 minutes)](https://ashu-tosh-kumar.github.io/todo_notifier/quickstart/) | install, scan, config, GitHub Action, pre-commit |
| [TODO syntax](https://ashu-tosh-kumar.github.io/todo_notifier/syntax/) | tags, `{date}`, `@owner`, `TAG(owner):`, overdue versus stale, languages |
| [Command line](https://ashu-tosh-kumar.github.io/todo_notifier/cli/) and [flags](https://ashu-tosh-kumar.github.io/todo_notifier/reference/cli/) | commands, formats, exit codes |
| [Configuration](https://ashu-tosh-kumar.github.io/todo_notifier/reference/configuration/) | every config key, generated from the code |
| [CI integrations](https://ashu-tosh-kumar.github.io/todo_notifier/ci/) and [pre-commit](https://ashu-tosh-kumar.github.io/todo_notifier/pre-commit/) | GitHub Action, GitLab CI, generic CI, hooks |
| [Notifications](https://ashu-tosh-kumar.github.io/todo_notifier/notifications/) | Slack, Teams, email and webhook setup |
| [Python API](https://ashu-tosh-kumar.github.io/todo_notifier/python-api/) and [API reference](https://ashu-tosh-kumar.github.io/todo_notifier/api/) | embed a scan, custom generators and notifiers |
| [FAQ](https://ashu-tosh-kumar.github.io/todo_notifier/faq/) | shallow clones, monorepos, performance, false positives, privacy |

**How it compares:** Ruff's `TD` rules lint the format of TODO comments, todo-to-issue turns them into issues, and TODO Notifier tracks deadlines and
owners and gates CI; they work well together ([comparison table](https://ashu-tosh-kumar.github.io/todo_notifier/comparison/)).

## Install

```bash
pipx install todonotifier        # the command line tool, in its own environment
pip install todonotifier         # or into the current environment: gives you the Python API too
```

Python 3.10 or newer (3.9 users stay on release 1.x). From a checkout: `pip install .`.

<!-- release-note: delete this line once todonotifier 2.1.0 is on PyPI and v2.1.0 is tagged (RELEASING.md) -->
> **Release status:** this README describes 2.1.0. Until it is published, `pipx install todonotifier` gives you 1.x, which has no command line tool: use
> `pipx install git+https://github.com/ashu-tosh-kumar/todo_notifier`, and a commit SHA instead of `v2.1.0` for the hook and the action.

## Contributing

We welcome contributions: bug reports, ideas, docs and code. The full guide is in [CONTRIBUTING.md](https://github.com/ashu-tosh-kumar/todo_notifier/blob/main/CONTRIBUTING.md): development setup with
Poetry on Python 3.10+, running the checks (tests with 100% coverage, black, isort, flake8, pre-commit hooks), building the docs, commit style, and how
to add a language's comment syntax or a notifier.

- **Bug reports and feature requests**: [open an issue](https://github.com/ashu-tosh-kumar/todo_notifier/issues/new/choose)
- **Questions and ideas**: [GitHub Discussions](https://github.com/ashu-tosh-kumar/todo_notifier/discussions)
- **First contribution**: look for issues labelled [good first issue](https://github.com/ashu-tosh-kumar/todo_notifier/labels/good%20first%20issue)
- **Security**: see [SECURITY.md](https://github.com/ashu-tosh-kumar/todo_notifier/blob/main/SECURITY.md)

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/ashu-tosh-kumar/todo_notifier/blob/main/LICENSE) file for details.

## Links

- [PyPI Package](https://pypi.org/project/todonotifier/)
- [Documentation](https://ashu-tosh-kumar.github.io/todo_notifier/)
- [Setup Guide](https://medium.com/@at-k/streamline-your-todos-with-todo-notifier-for-python-projects-6f95c03a2d34) (the article on Medium; the docs above are the up to date guide)
- [Issue Tracker](https://github.com/ashu-tosh-kumar/todo_notifier/issues)

## Changelog

<!-- --8<-- [start:changelog] -->

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
  (`todonotifier.settings_file.resolve_settings`, see [Configuration](https://ashu-tosh-kumar.github.io/todo_notifier/reference/configuration/)). Command line
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

- Added chat and webhook notifications (see [Notifications](https://ashu-tosh-kumar.github.io/todo_notifier/notifications/)): `todonotifier.digest` builds a channel-neutral digest of a
  `ScanResult` (totals, then Overdue, Stale and Due this week grouped by owner, top N each with "...and N more", deep links) and renders it as
  text or Markdown. New notifiers `SlackWebhookNotifier` (Block Kit), `TeamsWebhookNotifier` (Workflows, Adaptive Card) and `WebhookNotifier`
  (JSON), all on `urllib` with a 10 s timeout, 2 retries on 5xx/429 and no URLs, headers or bodies in logs or errors (`NotificationError`).
  `BaseNotifier.notify_result(result, reports)` (default: calls `notify(reports)`, so existing notifiers are unchanged), `EmailNotifier`
  gets `starttls`, `username`, `from_env()` and a digest email, and `build_notifiers()` creates notifiers from the config file's
  `[notify.*]` tables.

- Added the `todonotifier` command line tool (also `python -m todonotifier`), see [Command line](https://ashu-tosh-kumar.github.io/todo_notifier/cli/): `scan`, `report`, `notify` and `init`,
  with flags for tags, extensions, blame, default due days, `--since GIT_REF` (only TODOs on changed lines), `--fail-on`
  (`none`/`expired`/`stale`/`any`), `--format` (`table`, `json`, `github` annotations, `markdown`, `sarif`, `html`) and `--output`. Exit codes:
  0 OK, 1 `--fail-on` met, 2 usage or config error, 3 unexpected error. The JSON output has a JSON Schema,
  `todonotifier/schemas/scan_result.schema.json`. New modules `todonotifier.cli` and `todonotifier.formatters`; `git_meta.changed_lines`
  and `git_meta.filter_git_listed`. Passing many files to `scan()` (pre-commit) now takes one `git ls-files` call instead of two per file.
  `utils.store_html` returns the path it wrote and writes UTF-8. Development: `jsonschema` is a new dev dependency.

- Phase 0 review fixes: `scan . | head -1` no longer fails with exit 3 (a closed output ends quietly); PATH arguments can be mixed with
  options; the HTML reports (`todonotifier report`, emails) list explicit dates only as expired or upcoming (`TodoItem.to_legacy()` gives
  default due dates the no-date sentinel); `notify --since REF` sends nothing when no TODO is on a changed line; `todonotifier init` no longer
  creates a config whose own comments are reported as TODOs; Teams cards neutralise Markdown instead of backslash-escaping it; a minified
  one-line file or a file with thousands of TODOs is scanned in linear time (it took minutes); `generated_at` keeps the time of day;
  `--default-due-days` is limited to 100 years; "dubious ownership" of a repository is explained; an unreadable file is one error line;
  credentials in a clone URL are not logged by `Connect`; `.pre-commit-config.yaml` matches CI.

- Added pre-commit hooks (`.pre-commit-hooks.yaml`, see [pre-commit](https://ashu-tosh-kumar.github.io/todo_notifier/pre-commit/)): `todonotifier` (`scan --fail-on expired --no-blame`) and `todonotifier-strict`
  (`scan --fail-on incomplete --no-blame`). New `--fail-on incomplete` (a TODO without an owner annotation or an explicit date; also a `fail_on`
  value in the config file), and a `--blame` flag that overrides an earlier `--no-blame` (the last one wins), so `args` of a hook can turn blame on.
  Files named on the command line now obey `exclude_dirs` as well as `exclude_files`, and when they are all inside the current directory the config
  file is looked up from there (pre-commit passes repo-relative paths).

- Release and project housekeeping: CI runs on Python 3.10 to 3.14 with `black`, `isort`, `flake8`, 100% coverage
  and a self-check (`todonotifier scan . --fail-on expired`); `.github/workflows/release.yml` publishes tagged
  releases to PyPI with Trusted Publishing and creates the GitHub Release; this repository's own config is in
  `[tool.todonotifier]`; the legacy `user_driver.py` moved to `examples/python_api_example.py`; the committed
  `.report/` output was removed and is git-ignored.

- Discoverability and contributor on-ramp: richer PyPI metadata (description, keywords, classifiers, Changelog, Documentation and Issue
  Tracker links); a [comparison](https://ashu-tosh-kumar.github.io/todo_notifier/comparison/) with other TODO tools; fixed badge row (PyPI version and Downloads badges); `CONTRIBUTING.md` (the development setup moved
  there from the README), GitHub issue forms, a pull request template and a Discussions/security contact page.

- Added the GitHub Action (`integrations/github-action`, see [CI integrations](https://ashu-tosh-kumar.github.io/todo_notifier/ci/)): a composite action with `mode: pr` (annotations, job summary, outputs, an
  optional sticky pull request comment, `fail-on`) and `mode: digest` (full scan, Slack, Teams or webhook digest, HTML reports as an artifact). It scans once
  (`scan --format json`) and renders the annotations, summary, outputs and comment from that JSON with a small script that uses the library; `fail-on` is
  applied last, with the rule of the command line, so a failing check still has its summary and outputs. Inputs reach scripts through environment
  variables only, actions are pinned by commit SHA, the shallow-clone warning of `git_meta` becomes a workflow warning, and `safe.directory` is set. A self-test
  workflow (`.github/workflows/action-selftest.yml`) runs the action on fixtures. New: `todonotifier notify --slack-webhook-env NAME`,
  `--teams-webhook-env NAME` and `--webhook-url-env NAME` add a notifier from an environment variable without a config file, and
  `todonotifier.cli.fail_on_message(result, fail_on)` is public (the rule behind `--fail-on`).

- Documentation site (MkDocs Material, <https://ashu-tosh-kumar.github.io/todo_notifier/>, sources in `site_src/`) with a 5-minute Quickstart, the TODO
  syntax, CI integrations (GitHub Action, GitLab CI), pre-commit, notifications, the Python API, a comparison and an FAQ; the pdoc API reference moved to
  `/api/`. The configuration and command line references are generated from the code (`scripts/gen_docs_reference.py`), and CI fails when they are
  stale. The README is now a short landing page. `todonotifier init` and its error messages link to the docs instead of the README. The docs are an
  optional Poetry group: `poetry install --with docs`.

- Phase 1 review fixes: the GitHub Action's `default-due-days` no longer overrides `default_due_days` of the config file (its default is empty now, which means
  "config file, else 90"), fetches the base commit of a shallow pull request checkout, and says when `digest` mode has no webhook to send to; `@user` and
  `@org/team` in a TODO message no longer notify anyone when the Markdown digest is posted as a pull request comment; scanning a path on another drive than the
  current directory (Windows) no longer fails; the README uses absolute links and image URL, which PyPI needs.

- Final review fix: the file paths of `--format sarif` are percent-encoded (a SARIF `uri` is a URI reference, so a `#` or a space in a file name broke the location).

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
<!-- --8<-- [end:changelog] -->

---

<div align="center">

**Made with ❤️ for developers who care about their TODOs**

[⭐ Star us on GitHub](https://github.com/ashu-tosh-kumar/todo_notifier) •
[🐛 Report Issues](https://github.com/ashu-tosh-kumar/todo_notifier/issues) •
[💬 Discussions](https://github.com/ashu-tosh-kumar/todo_notifier/discussions)

</div>
