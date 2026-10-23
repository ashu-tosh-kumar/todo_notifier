# Phase 0: Core and CLI

**Goal:** a new user goes from `pipx install todonotifier` to a useful report in under 5
minutes, with no Python script to write. TODO ownership and dates are filled in automatically
where possible, and teams get reminders in Slack or Teams instead of only SMTP email.

**Release:** `v2.1.0`. Non-breaking, except that it requires Python ≥ 3.10 (D1).
⚠️ Estimated effort: 1 to 2 weeks.

**Exit criteria**
- `todonotifier scan .` works on any git repo with zero configuration.
- `todonotifier scan --fail-on expired` can gate CI.
- Settings can live in `[tool.todonotifier]` in `pyproject.toml`.
- TODOs without `@user` get an owner from `git blame`.
- The false-positive defects listed in [README.md](README.md#known-defects-to-fix-early-verified-on-main) are fixed.
- `v2.1.0` is published on PyPI.

Read [README.md](README.md) first for the dependency graph, shared agent rules and open
decisions.

---

## 0.1 Foundation: in-place scanning, structured results, settings schema

**Size:** M · **Hard dependencies:** none · **Blocks:** 0.2, 0.3, 0.4, 0.6 (hard) and 0.5 (soft)

This is the keystone. It gives every other workstream a stable, side-effect-free API to build
on, and it is also the scan engine that the Phase 3 SaaS worker will import.

### Why
- `driver.run()` mixes scanning, HTML writing and notifying, so nothing can reuse "just scan".
- `DRY_RUN_DIR` copies the whole project into a temp dir before scanning.
- `TODO` objects are not serializable, and "no date" is stored as the sentinel
  `9999-12-25` (`constants.DEFAULT_COMPLETION_DATE`).

### Scope
1. **`todonotifier/settings.py` (new):** a `ScanSettings` dataclass that is the single
   source of truth for every option the CLI and config file will expose. Fields, with defaults
   that keep today's behavior:
   - `paths: List[str]` (default `["."]`)
   - `extensions: List[str]` (default `["py"]`; 0.4 adds the common-languages preset)
   - `tags: List[str]` (default `["TODO"]`; 0.4 widens it)
   - `ignore_case: bool` (default `False`)
   - `exclude_dirs` and `exclude_files` (same shape as `BaseConfig`)
   - `require_comment: bool` (default `False`; implemented in 0.4)
   - `use_git_blame: bool` (default `False`; implemented in 0.3)
   - `default_due_days: Optional[int]` (default `None` in `ScanSettings` and `from_config`;
     the CLI and config-file default of `90` is applied in 0.2 and 0.6; implemented in 0.3;
     see "D4 design" in [README.md](README.md#d4-design-default-due-dates-without-noisy-ci))
   - `respect_gitignore: bool` (default `False`; implemented in 0.4)
   - `repo_web_url: Optional[str]` and `commit_sha: Optional[str]` (used for deep links)

   Also add `ScanSettings.from_config(config: BaseConfig)` so the existing `driver.run` can be
   expressed through the new API.
2. **`todonotifier/scanner.py` (new):** `scan(settings: ScanSettings) -> ScanResult`. It is a
   pure function: it scans files in place, writes nothing, sends nothing and leaves no temp
   dirs behind.
3. **`ScanResult` and `TodoItem`** (in `todonotifier/models.py` or a new
   `todonotifier/results.py`):
   - `TodoItem` fields: `file` (relative path), `line`, `tag`, `message`, `author`,
     `author_source` (`"annotation"`, `"git_blame"` or `"unknown"`), `due_date: date | None`
     (`None` instead of the sentinel), `due_source` (`"explicit"`, `"default"` or `"none"`),
     `created_date: date | None` (filled by 0.3), `is_overdue` (explicit date passed),
     `is_stale` (default date passed), `days_past_due`, `web_url: str | None`.
   - `ScanResult` fields: `items`, `scanned_files`, `root`, `generated_at`, `schema_version`
     (start at `1`), plus helpers: `overdue()`, `stale()`, `due_within(days)`, `by_author()`,
     `by_file()`.
   - Both must support `to_dict()` / `from_dict()` and a JSON round-trip.
   - Provide `TodoItem.from_legacy(todo: TODO)` and the reverse, so the existing summary
     generators keep working without changes.
4. **`ConnectMethod.LOCAL` (new):** scans a directory in place with no copy. Keep
   `DRY_RUN_DIR` as it is for backwards compatibility.
5. **Refactor `driver.run`** to `ScanSettings.from_config` → `scan` → existing summary
   generators, storage and notifier. Public behavior must stay unchanged.
6. **Python 3.10 minimum (D1):** set `python = "^3.10"` in `pyproject.toml`, refresh
   `poetry.lock`, and add the changelog note "Requires Python ≥ 3.10. Python 3.9 users stay on
   2.0.x." (The CI matrix change is in 0.7.)
7. **Generator state bug:** write a test that calls `run()` twice with the same config. If rows
   duplicate, reset generator state at the start of each run without breaking custom
   generators. One option is a `reset()` method on `BaseSummaryGenerator` that does nothing by
   default and is overridden by the three built-in generators.

### Acceptance criteria
- `scan()` on `tests/sample_test_file.py` and `tests/sample_test_file2.py` returns the same
  TODO set (message, user, date, line) as the current `parse_files_for_todo_items`.
- Every existing test passes without modification.
- `ScanResult` survives a `json.dumps(result.to_dict())` → `from_dict` round-trip unchanged.
- `scan()` creates no files and no temp directories (assert in the test).
- Calling `driver.run()` twice does not duplicate report rows.

### Tests
`tests/test_scanner.py`, `tests/test_settings.py`, plus additions to `tests/test_driver.py` and
`tests/test_models.py`.

---

## 0.2 Config file support

**Size:** S–M · **Hard dependencies:** 0.1 · **Blocks:** 0.7 · **Soft dependency for:** 0.6

### Scope
1. **`todonotifier/settings_file.py` (new):** loads settings from:
   - `[tool.todonotifier]` in `pyproject.toml`, or
   - `.todonotifier.toml` (same keys at top level).

   Discovery: start at the scan path and walk up to the git root (or the filesystem root if
   there is no git repo). The first file found wins. An explicit path (CLI `--config`)
   overrides discovery.
2. **Precedence:** CLI flags > config file > CLI/config-file defaults > `ScanSettings`
   defaults. The CLI/config-file defaults are where the D4 and D5 choices apply:
   `default_due_days = 90`, `extensions = "common"`, the wider tag list,
   `respect_gitignore = true` and `use_git_blame = true`. Implement this as
   `resolve_settings(cli_overrides: Dict[str, Any], config_path: Optional[str]) -> ScanSettings`.
3. **Validation:** unknown keys and wrong types fail with a clear message naming the key and
   the file (for example `Unknown key 'tagz' in pyproject.toml [tool.todonotifier]. Did you mean 'tags'?`).
4. **Notifier settings** live under `[tool.todonotifier.notify.<name>]` and reference
   environment variable **names**, never secret values. Example keys:
   `slack_webhook_env = "TODO_SLACK_WEBHOOK"` and `smtp_password_env = "TODO_SMTP_PASSWORD"`.
   This schema is shared with 0.5, so agree on key names with the 0.5 PR.
5. **TOML parsing:** use `tomllib` on Python 3.11+ and add the conditional dependency
   `tomli = { version = "^2.0", python = "<3.11" }`. TOML only, no YAML (avoids a PyYAML
   dependency).
6. A documented example config in the README (1.3 later moves it into the docs site).

### Acceptance criteria
- A precedence test matrix covers defaults only, file only, CLI only, and file plus CLI.
- An invalid key or type exits with a helpful error (the CLI maps it to exit code 2 in 0.6).
- If no config file exists, defaults are used and no error is raised.

### Tests
`tests/test_settings_file.py` with temp directories containing `pyproject.toml` and
`.todonotifier.toml` fixtures.

---

## 0.3 Git-aware ownership and TODO age

**Size:** M · **Hard dependencies:** 0.1 · **Blocks:** 0.7 (and Phase 3, hard) · **Soft dependency for:** 1.1

### Why
Today, ownership exists only if developers type `@user`. `git blame` gives an owner and a
creation date for free. The creation date is also the basis for TODO-age metrics, which are a
key SaaS feature.

### Scope
1. **`todonotifier/git_meta.py` (new):** for each file that has TODOs, run **one**
   `git blame --porcelain <file>` (not one call per line). Parse the author name, author email
   and author time for the TODO lines. Use `subprocess` with list arguments, or GitPython,
   which is already a dependency.
2. Fill in `TodoItem.author` (with `author_source="git_blame"`) only when there is no `@user`
   annotation. Always fill in `created_date` when blame is available.
3. **Default due dates (D4):** if `default_due_days` is set and a TODO has no `{date}`, set
   `due_date = created_date + default_due_days` and `due_source = "default"`. If there is no
   `created_date` (no blame), leave `due_source = "none"`. An explicit `{date}` always wins.
   `default_due_days = 0` disables defaults. Follow "D4 design" in
   [README.md](README.md#d4-design-default-due-dates-without-noisy-ci) exactly: default
   dates mark items as *stale*, never as *overdue*.
4. **Author aliases:** an optional `[tool.todonotifier.authors]` table mapping emails to handles
   (for example `"a@x.com" = "ashu"`), used for display and later for Slack mentions.
5. **Graceful degradation, with a warning logged once per run:**
   - not a git repo, or `git` not installed → skip blame;
   - **shallow clone** (`git rev-parse --is-shallow-repository` returns `true`) → warn that
     authors and dates may be wrong and suggest `fetch-depth: 0`. This matters because
     GitHub Actions checks out with depth 1 by default;
   - uncommitted lines (all-zero commit hash) → author unknown, `created_date` = today.
6. **Performance:** run blame calls in parallel with a bounded `ThreadPoolExecutor`
   (for example 8 workers). Skip blame for files with no TODOs.

### Acceptance criteria
- In a temporary test repo with two authors and fixed commit dates, the author and
  `created_date` are correct for each TODO.
- An `@user` annotation always wins over the blame result.
- With `default_due_days=90`, a TODO committed 100 days ago with no date is `is_stale=True`
  and `is_overdue=False`. One committed 10 days ago is neither.
- Shallow, non-git and uncommitted cases are covered by tests and do not crash.
- A scan of a repo with about 1,000 files and about 100 TODOs, with blame on, takes less than
  2× the time without blame. ⚠️ This is a target, not a measured baseline. Record the actual
  numbers in the PR.

### Tests
`tests/test_git_meta.py`, which creates the repo with `git init` in a temp dir inside the test.

---

## 0.4 Tags, languages and detection accuracy

**Size:** M · **Hard dependencies:** 0.1 · **Blocks:** 0.7

### Scope
1. **Fix the false positives** (verified, see the defects table in [README.md](README.md)):
   - Match tags on word boundaries (`\bTODO\b`), so `todonotifier` and `TODO_REGEX_PATTERN`
     no longer match, including when `ignore_case` is on.
   - Optional `require_comment`: the tag must come after a comment marker for the file's
     language. Add `todonotifier/languages.py` mapping extensions to markers, for example
     `#` for py/sh/rb/yaml, `//` and `/* */` for js/ts/java/go/c/cpp/cs/kt/swift/rs/php,
     `--` for sql/lua and `<!-- -->` for html/md. For unknown extensions, fall back to
     matching anywhere.
   - Write regression tests **first**, based on the three lines in the defects table.
2. **Configurable tags:** default `["TODO", "FIXME", "HACK", "XXX"]` for the CLI and config file.
   The library's `DefaultConfig` keeps `TODO` only, for backwards compatibility. Store the
   matched tag in `TodoItem.tag`. The existing `{date}` and `@user` syntax works after any tag.
3. **Language presets (D5, decided):** `extensions = "common"` expands to a curated list
   (py, js, jsx, ts, tsx, java, kt, go, rs, rb, php, c, h, cpp, hpp, cs, swift, scala, sh, sql,
   yaml, yml, toml, html, css, scss, md). The CLI and config-file default is `common`.
   `DefaultConfig` keeps `["py"]`.
4. **`respect_gitignore`:** when inside a git repo, list files with
   `git ls-files --cached --others --exclude-standard` instead of walking the tree. This skips
   `node_modules` and `venv` for free and is faster. On by default in the CLI.
5. **Robustness:** skip binary files (NUL byte in the first 8 KB) and read with
   `errors="replace"`. Keep the existing streaming path for files over 10 MB.

### Acceptance criteria
- The three false-positive lines from the defects table produce no TODOs.
- Fixture files in at least 6 languages produce the expected items, and a TODO inside a
  string literal is ignored when `require_comment=True`.
- `node_modules/` content is ignored by default in a git repo that gitignores it.
- Existing tests still pass with the library defaults.

### Tests
`tests/test_todo_notifier.py` (extended), `tests/test_languages.py`, and fixtures in
`tests/fixtures/languages/`.

---

## 0.5 Chat and webhook notifiers plus the digest

**Size:** M · **Hard dependencies:** none (it codes against the `ScanResult` interface from 0.1) · **Blocks:** 0.7 · **Soft dependency for:** 1.1

### Scope
1. **Rich notifications without breaking the old API:** add an optional
   `BaseNotifier.notify_result(result: ScanResult, reports: List[Tuple[str, str]])`. The
   default implementation calls the existing `notify(reports)`, so custom notifiers keep
   working.
2. **`todonotifier/digest.py` (new):** builds a channel-neutral digest from a `ScanResult`:
   - totals (open, overdue, stale, due in 7 days, new since the last commit range if known);
   - top N overdue items, then top N stale items, as separate sections grouped by owner, each with a deep link
     (`{repo_web_url}/blob/{commit_sha}/{file}#L{line}`) when both values are known.
3. **New notifiers** in `todonotifier/notifier.py`:
   - `SlackWebhookNotifier`: incoming-webhook payload with Block Kit sections. Truncate long
     lists with "...and N more".
   - `TeamsWebhookNotifier`: Teams webhook via Workflows. ⚠️ Microsoft has been retiring Office
     365 connectors in favor of Workflows. Check the current Microsoft docs for the payload
     format before implementing.
   - `WebhookNotifier`: POSTs `ScanResult.to_dict()` as JSON to any URL (for Discord bridges,
     Zapier and internal tools).
   - `EmailNotifier` improvements: optional STARTTLS on port 587, and a
     `from_env(prefix="TODO_SMTP_")` constructor.
4. **HTTP:** standard-library `urllib.request` only, with a 10 s timeout, 2 retries with backoff
   on 5xx and 429, and no secrets in logs or exceptions.
5. **Config keys:** agree on the `[tool.todonotifier.notify.*]` key names with 0.2 and
   document them.

### Acceptance criteria
- Payload snapshot tests for Slack, Teams and the generic webhook, with network calls mocked.
- Old-style `EmailNotifier(...)` and custom `BaseNotifier` subclasses work without changes.
- Webhook URLs and passwords never appear in log output (assert with `assertLogs`).

### Tests
`tests/test_notifier.py` (extended) and `tests/test_digest.py`.

---

## 0.6 Command-line interface

**Size:** M–L · **Hard dependencies:** 0.1 · **Soft dependencies:** 0.2, 0.3, 0.4 · **Blocks:** 0.7, 1.1, 1.2

### Scope
1. **Entry points:** `[tool.poetry.scripts] todonotifier = "todonotifier.cli:main"`, plus
   `todonotifier/__main__.py` so `python -m todonotifier` works. Use `argparse` (no new
   dependency). `main(argv: Optional[List[str]] = None) -> int` must be testable without a
   subprocess.
2. **Commands**
   - `todonotifier scan [PATH ...]`: scan and print results. Positional paths may be files,
     because pre-commit passes the staged file list.
   - `todonotifier report [--out DIR]`: write the existing HTML reports (default `.report/`).
   - `todonotifier notify`: scan, then send to every notifier configured in the config file.
   - `todonotifier init`: append a commented starter `[tool.todonotifier]` section to
     `pyproject.toml`, or create `.todonotifier.toml`. Never overwrite an existing section.
   - `todonotifier --version`
3. **Flags shared by scan, report and notify:** `--config PATH`, `--tags`, `--ext`,
   `--ignore-case`, `--no-blame`, `--default-due-days N` (CLI default `90`, `0` disables),
   `--since GIT_REF`, `--fail-on {none,expired,stale,any}` (default `none`; `expired` counts
   explicit dates only, `stale` adds default dates, per D4), `--format`, `--output FILE`,
   `-q/--quiet`, `-v/--verbose`. Flags map to `cli_overrides` in
   `resolve_settings` (from 0.2). Until 0.2 merges, call a stub that returns defaults plus
   overrides.
4. **`--since GIT_REF`:** report only TODOs on lines added or changed relative to `GIT_REF`
   (parse `git diff --unified=0 GIT_REF`). This powers PR checks in 1.1. Put the helper in
   `todonotifier/git_meta.py` and coordinate with 0.3.
5. **`todonotifier/formatters.py` (new)** with these output formats:
   - `table` (default): aligned columns, colored only when stdout is a TTY and `NO_COLOR` is
     unset, plus a summary line;
   - `json`: `ScanResult.to_dict()` including `schema_version`;
   - `github`: GitHub workflow commands (`::warning file=…,line=…::message`, using `::error`
     for overdue items) so TODOs appear as PR annotations;
   - `sarif` (stretch goal): SARIF 2.1.0 for GitHub code scanning;
   - `html`: delegates to the existing summary generators.
6. **Exit codes** (documented in `--help` and the README): `0` OK, `1` the `--fail-on`
   condition was met, `2` usage or config error, `3` unexpected runtime error.

### Acceptance criteria
- In a fresh virtualenv, `pipx install .` then `todonotifier scan .` on this repo prints a
  table in under 30 s with no config.
- `--fail-on expired` returns 1 when a TODO with a passed **explicit** date exists and 0
  otherwise. In particular, it returns 0 for a repo whose only problems are stale TODOs
  without dates. `--fail-on stale` returns 1 for those.
- `--format json` output validates against the documented schema, and `--format github`
  output matches the GitHub workflow-command syntax.
- `todonotifier scan file1.py file2.py` scans only those files.
- `--since HEAD~1` reports only TODOs on changed lines.

### Tests
`tests/test_cli.py` (calls `main([...])` and checks the exit code, using `capsys`) and
`tests/test_formatters.py` (snapshot tests).

---

## 0.7 Release v2.1.0 and housekeeping

**Size:** S–M · **Hard dependencies:** 0.2, 0.3, 0.4, 0.5, 0.6 · **Blocks:** 1.1, 1.2, 1.3

### Scope
1. **CI cleanup** in `.github/workflows/python-app.yml`: install dependencies once per job
   (they are currently installed three times), switch to a version matrix
   (3.10 to 3.14, per D1; replace the current `build3_9` job), add `black --check` and
   `isort --check-only`, report coverage, and upgrade `actions/setup-python` to the current
   major version. Move `.github/workflows/docs.yml` off Python 3.9 as well.
2. **Publish workflow** `.github/workflows/release.yml`: on a `v*` tag, build with Poetry and
   publish to PyPI with **Trusted Publishing** (OIDC, no API token), then create a GitHub
   Release with the changelog section. The maintainer must configure the trusted publisher on
   PyPI once. Document this step in the PR.
3. **README:** replace the Quick Start with the CLI flow (install → `scan` → `init` → CI).
   Move the Python API examples under "Python API". Reconcile the changelog: it currently says
   "v2.0.0 (Unreleased)", so check what is actually on PyPI.
4. **Repo hygiene:** remove the committed `.report/` files and gitignore the folder. Delete
   `user_driver.py` or mark it as a legacy example.
5. Bump `version` in `pyproject.toml`, tag `v2.1.0`, publish, and verify with
   `pipx install todonotifier==2.1.0` in a clean environment.

### Acceptance criteria
- CI is green on every Python version in the matrix.
- `pipx install todonotifier==2.1.0 && todonotifier --version` works from PyPI.
- A GitHub Release exists with notes.
