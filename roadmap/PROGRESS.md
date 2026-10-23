# Roadmap execution progress

This file is the hand-off point for any agent (or person) continuing the roadmap work. Update it
at the end of every workstream, in the same branch as the work.

## How the work is laid out

- **Scope of this run:** Phases 0, 1 and 2, executed sequentially (no parallel agents, to save
  credits). Phase 3 is out of scope.
- **Stacked PRs.** Base branch is `development` (the integration branch; `main` is the release
  branch). Each workstream is one branch and one PR, stacked on the previous one:

  ```text
  development
   └─ claude/serene-hopper-qkult2   (roadmap docs + this file)
       └─ roadmap/0.1-foundation
           └─ roadmap/0.2-config-file
               └─ ... (one branch per workstream, in the order of the table below)
  ```

- **Live status lives at the tip of the stack.** The newest `roadmap/*` branch has the most
  recent copy of this file. To resume: `git fetch origin`, check out the newest `roadmap/*`
  branch listed below, read this file, and continue with the first row that is not ✅.
- **Local env:** `uv python install 3.10`, then
  `poetry env use $(uv python find 3.10) && poetry install --with dev`. Checks before every
  push: `poetry run pytest`, `black --check .`, `isort --check-only .`,
  `flake8 . --config ./tox.ini`, plus coverage of new code.

## Status

Implementation agents follow [AGENT-BRIEF.md](AGENT-BRIEF.md).


| # | Workstream | Branch | PR | Status | Notes |
|---|---|---|---|---|---|
| - | Roadmap docs + progress file | `claude/serene-hopper-qkult2` | [#165](https://github.com/ashu-tosh-kumar/todo_notifier/pull/165) | ✅ done | Merged latest `development` |
| 0.1 | Foundation | `roadmap/0.1-foundation` | [#166](https://github.com/ashu-tosh-kumar/todo_notifier/pull/166) | ✅ done | See "Notes per workstream" below |
| 0.2 | Config file | `roadmap/0.2-config-file` | [#167](https://github.com/ashu-tosh-kumar/todo_notifier/pull/167) | ✅ done | See "Notes per workstream" below |
| 0.3 | Git blame ownership and age | `roadmap/0.3-git-blame` | [#168](https://github.com/ashu-tosh-kumar/todo_notifier/pull/168) | ✅ done | See "Notes per workstream" below |
| 0.4 | Tags, languages, detection accuracy | `roadmap/0.4-detection` | [#169](https://github.com/ashu-tosh-kumar/todo_notifier/pull/169) | ✅ done | See "Notes per workstream" below |
| 0.5 | Chat and webhook notifiers + digest | `roadmap/0.5-notifiers` | [#170](https://github.com/ashu-tosh-kumar/todo_notifier/pull/170) | ✅ done | See "Notes per workstream" below |
| 0.6 | CLI | `roadmap/0.6-cli` | [#171](https://github.com/ashu-tosh-kumar/todo_notifier/pull/171) | ✅ done | See "Notes per workstream" below |
| 0.7 | Release prep v2.1.0 + CI housekeeping | `roadmap/0.7-release` | [#172](https://github.com/ashu-tosh-kumar/todo_notifier/pull/172) | ✅ done | Tag and publish pending maintainer, see [RELEASING.md](../RELEASING.md) and "Notes per workstream" below |
| P0 | Phase 0 review | `roadmap/p0-review` | [#173](https://github.com/ashu-tosh-kumar/todo_notifier/pull/173) | ✅ done | [Phase 0 review notes](#phase-0-review): requirement table, 7 known issues and 13 new findings fixed, what was left |
| 1.4 | Discoverability quick wins | `roadmap/1.4-discoverability` | [#174](https://github.com/ashu-tosh-kumar/todo_notifier/pull/174) | ✅ done | See "Notes per workstream" (1.4); maintainer GitHub settings checklist there |
| 1.2 | pre-commit hook | `roadmap/1.2-pre-commit` | [#175](https://github.com/ashu-tosh-kumar/todo_notifier/pull/175) | ✅ done | See "Notes per workstream" (1.2); decisions A60 to A63 |
| 1.1 | GitHub Action (seed in this repo) | `roadmap/1.1-github-action` | | 🟡 in progress | See decision A3 |
| 1.3 | Docs site and 5-minute guide | `roadmap/1.3-docs` | | ⬜ todo | |
| 1.5 | Launch content drafts + metrics baseline | `roadmap/1.5-launch` | | ⬜ todo | Posting is a maintainer step |
| P1 | Phase 1 review | | | ⬜ todo | |
| 2.0 | Name and brand checks (automatable part) | `roadmap/2.0-name-checks` | | ⬜ todo | |
| 2.1 | Landing page and waitlist (draft) | `roadmap/2.1-landing-page` | | ⬜ todo | |
| 2.2 | Interview kit | `roadmap/2.2-interviews` | | ⬜ todo | |
| 2.3 | GO / NO-GO decision template | `roadmap/2.3-decision` | | ⬜ todo | Decision is the maintainer's |
| P2 | Phase 2 review + final review | | | ⬜ todo | |

Legend: ✅ done · 🟡 in progress · ⬜ todo · ⛔ blocked (needs the maintainer)

## Decisions made without the maintainer (please review)

The maintainer was unavailable during this run, so these calls were made on a best-effort
product and engineering basis. Each one is easy to reverse.

| ID | Decision | Why |
|---|---|---|
| A1 | Stack the PRs on `development`, not `main`. | `development` is ahead of `main` and is where feature PRs land (`main` only receives release merges). |
| A2 | Workstream order: 0.1 → 0.2 → 0.3 → 0.4 → 0.5 → 0.6 → 0.7, then 1.4 → 1.2 → 1.1 → 1.3 → 1.5, then 2.0 → 2.1 → 2.2 → 2.3. | Respects every hard dependency in `roadmap/README.md` while running one agent at a time. 1.3 runs after 1.1 and 1.2 so the docs can describe them as built. |
| A3 | The GitHub Action (1.1) is built in `integrations/github-action/` of this repo instead of a new `todonotifier-action` repo. | This session cannot create repositories, and D2 should not be changed silently. The folder is self-contained so the maintainer can copy it to the root of the new repo. Until then it already works as `uses: ashu-tosh-kumar/todo_notifier/integrations/github-action@<ref>`. |
| A4 | 0.7 prepares the release (version bump, changelog, CI, release workflow) but does not tag or publish. | Publishing to PyPI and creating tags are irreversible, outward-facing actions, and PyPI Trusted Publishing must first be configured by the maintainer. |
| A5 | Phase 2 deliverables that are not library code (name research, landing page draft, interview kit, decision template) live under `roadmap/`. | D3: nothing SaaS-specific goes into the library. Keeping them in `roadmap/` keeps them reviewable without touching the package. |
| A6 | Development and tests run on Python 3.10 (the new minimum, D1). | Catches accidental use of 3.11+ features, and exercises the `tomli` fallback path. |
| A7 | 0.2 API: `find_config_file(start)`, `load_config(config_path, start)`, `resolve_settings(cli_overrides, config_path, start)` and `resolve_project_config(...)` (returns `ProjectConfig` with `settings`, `fail_on`, `notify`, `source`), in `settings_file.py`. Precedence: CLI overrides > file > CLI/config-file defaults > `ScanSettings` defaults; a `None` override means "not given". Errors are `ConfigError`. | The roadmap signature plus what the 0.6 CLI needs (`fail_on`, `notify`). |
| A8 | `CLI_DEFAULTS` (one dict in `settings_file.py`): `default_due_days=90`, `extensions="common"`, `tags=[TODO, FIXME, HACK, XXX]`, `respect_gitignore=True`, `use_git_blame=True`. Library defaults are unchanged. | D4/D5, without changing the library API. |
| A9 | `languages.py` with `COMMON_EXTENSIONS` and `expand_extensions` (`"common"` as a string or list element; de-duplicated, ordered, dots stripped). | 0.4 extends this module with comment markers. |
| A10 | Accepted keys are all `ScanSettings` fields except `author_aliases`, plus `fail_on`, `notify`, `authors`. Config-file `paths` are relative to the config file; CLI paths are left as given. | Matches how people read a config file. |
| A11 | `[tool.todonotifier.authors]` (email to handle) fills the new `ScanSettings.author_aliases`. Emails are lower-cased on load. | 0.3 uses it; it must look emails up lower-case. |
| A12 | Notifier schema under `[tool.todonotifier.notify.<name>]` for `slack`, `teams`, `webhook`, `email` (keys listed in the `settings_file.py` docstring and the README). `*_env` keys name env vars (validated as variable names; values are never read, stored or echoed). Literal-secret keys are rejected with a hint. Every table has `enabled` (default true), added to the validated dict. | Shared with 0.5. |
| A13 | `tomli = { version = "^2.0", python = "<3.11" }`; `tomllib` on 3.11+. | Decision 7 of the 0.2 brief; the lock only moved `tomli` into the main group. |
| A14 | `default_due_days = 0` means "off" (stored as `None`), because TOML has no null. | `ScanSettings.default_due_days=None` needs a config spelling. |
| A15 | `exclude_dirs` / `exclude_files` in the file or CLI overrides are **added** to the built-in exclusions (tables `name`, `pattern`, `abs_path`, any case), never replacing them. | Replacing would silently re-scan `venv` and friends. |
| A16 | An explicit `--config` path to a `pyproject.toml` without `[tool.todonotifier]` is an error; any other explicit file name is read with top-level keys. A broken `pyproject.toml` met during discovery is an error too. | Fail loudly rather than silently ignore the user's file. |
| A17 | Warning texts of `git_meta` are module constants (`WARNING_GIT_NOT_INSTALLED`, `WARNING_NOT_A_GIT_REPO`, `WARNING_SHALLOW_CLONE`) logged at WARNING once per `scan()`. Uncommitted lines are an INFO message (`INFO_UNCOMMITTED`, one per scan), not a warning. | Uncommitted lines are normal in pre-commit and local runs; warning every time would be noise. |
| A18 | Repo web URL and commit SHA are detected (`GITHUB_*` env vars, then `origin` / `HEAD`) per value, only when `ScanSettings.repo_web_url` / `commit_sha` is None and `use_git_blame` is on. With blame on, `web_url` is always rebuilt from the repo-relative path. Non-hosted remotes (local paths, `file://`) give no URL. | Deep links with zero config; correct when scanning a subdirectory. |
| A19 | Blame is limited to the TODO lines with repeated `-L n,n` (whole-file blame above 200 TODO lines in one file). `blame_file(root, rel_path, lines=None, today=None)`; `blame_files(root, rel_paths, max_workers=8, lines_by_file=None, today=None)`. Only the repository containing the scan root is used: files in a nested repo or submodule are treated as uncommitted. | Measured: `-L` is 25% faster on 1,500-line files. |
| A20 | If blame has no author name, the author email is used; items on uncommitted lines keep `author=None`, `author_source="unknown"` but get `created_date=today` and a default due date (D4 only withholds it when blame is unavailable). `GITHUB_SHA` is used only if it is a 40 or 64 digit hex string. | Matches the brief; avoids garbage in deep links. |
| A21 | `TAG(owner)` (Google style, Ruff TD002) is accepted as an owner annotation equal to `@owner` (`author_source="annotation"`), and one `:` between the tag, owner, date or user and the message is dropped. This "extended syntax" is a keyword-only `extended_syntax` argument of `parse_files_for_todo_items`, on in `scan()` and off in `driver.run` and for direct callers. | `class TODO:` in `tests/sample_test_file.py` is asserted to give the message `:`; dropping the colon changes it to an empty message. Off keeps the legacy path byte-compatible. An owner must start with a letter, so `TODO(#123)` or `TODO(crbug.com/1)` stay in the message. If both `(owner)` and `@user` are present, the owner in parentheses wins. |
| A22 | `CLI_DEFAULTS` gets `require_comment = True` (the library default stays False). | Precision on first run matters more than recall for adoption, and Markdown prose or fenced samples (or strings) should not be reported. Users can set `require_comment = false`. |
| A23 | The matched tag is reported as spelled in `tags` (so `todo` is reported as `TODO` with `ignore_case`). Only one item per line: the first tag (inside a comment, when required) wins and the rest of the line is its message. | Stable grouping by tag; the existing one-item-per-line rule. |
| A24 | With `require_comment`, text in strings (including Python docstrings and other multi-line strings) is not a comment, so TODOs in docstrings are not reported. Markdown fenced code is skipped entirely. A `#` in YAML and shell counts only at the line start or after whitespace. The item text stops at the end of the comment (`*/`, `-->` are not in messages). | Pragmatic precision rules, documented in the `languages.py` docstring. Extra extensions beyond the spec were added to the syntax table (`pyi`, `bash`, `mjs`, `cjs`, `kts`, `cc`, `cxx`, `hh`, `htm`), and `#` for php, `/* */` for sql and `--[[ ]]` for lua. |
| A25 | `respect_gitignore` runs one `git ls-files -z --cached --others --exclude-standard` per scan directory (cwd = that directory) and one with a pathspec per individually named file; results are intersected with extensions and exclusions (including `ABS_PATH`). Outside a repository, or if git fails or times out (60 s), the tree is walked. `.git` is in `DEFAULT_EXCLUDE_DIRS`. Skipped binary files do not appear in `scanned_files`. | Matches the spec; binary files were never "scanned". |
| A26 | `notify_result(result, reports)` keeps exactly two parameters. The "new TODOs" count (from `--since`) is passed through the public attribute `DigestNotifier.new_count`, which 0.6 sets on each notifier before sending. | A third parameter would break custom subclasses that override `notify_result` with two. |
| A27 | `DigestNotifier` (public base: `max_items`, `new_count`, `make_digest`) is the base of `EmailNotifier` and the three HTTP notifiers. `EmailNotifier` gets keyword arguments `starttls`, `username` and `max_items` at the end of its signature. | Config has `username_env` (login differs from the sender) and email needs a digest size. Old positional calls are unchanged. |
| A28 | Errors: `NotificationError(Exception)` for delivery failures and `NotifierConfigError(ValueError)` for bad notifier settings (missing env var, invalid URL or header). Messages name env var names, never values. 0.6 should map `NotifierConfigError` to exit code 2 and decide whether a `NotificationError` fails the run. | Distinguishes "your config is wrong" from "the network failed". |
| A29 | Defaults without a port: `smtp_port` / `PORT` is 587 with STARTTLS, else 465. `EmailNotifier.from_env` requires HOST, SENDER, RECIPIENTS, PASSWORD and treats an empty value as missing. The webhook notifier's `headers_env` must hold a JSON object of strings and is required to be set if the key is named. | Sensible defaults; fail loudly when the user named a variable that is not there. |
| A30 | The digest recomputes overdue/stale/days past due from `due_date`/`due_source` against `today` (default: the date of `generated_at`), instead of trusting the stored flags. "Due this week" is today up to 7 days ahead and does not overlap Overdue or Stale. | Makes `today` meaningful and the digest deterministic in tests. |
| A31 | Custom headers of `WebhookNotifier` are sent with `Request.add_unredirected_header`, so urllib drops them when a server redirects to another host. Messages from `urlopen` failures that are not HTTP/network errors are replaced by the exception type. | A bearer token must not leak through a redirect or an exception message. |
| A32 | Untrusted text (TODO messages, file names) is escaped per channel: Slack `& < >`, Markdown/Teams backslash escapes, HTML autoescape. Only http(s) links without whitespace or `<>|` are rendered (`digest.safe_url`). | A scanned repository can contain any text, including `<!channel>` or `[x](http://evil)`. |
| A33 | `--format` and `--output` exist on `scan`, `report` and `notify`. `report` is `scan` with the default format `html` (`--out` is an alias of `--output`, the directory for the files, default `.report`); `notify` prints a result only if `--format` is given. `html` is handled by the CLI (it writes files), `formatters.format_result` only does the text formats. | The brief lists the flags as shared; one code path for all three keeps them consistent. |
| A34 | Without PATH arguments, the `paths` of the config file apply (default `.`). PATH arguments override them and are left as given. | `scan` with a config that says `paths = ["src"]` should scan `src`. |
| A35 | `init` without a flag: `.todonotifier.toml` if it exists (message, exit 0), else `pyproject.toml` if it exists (append unless it has `[tool.todonotifier]`, an empty table counts), else create `.todonotifier.toml`. `--pyproject` without a `pyproject.toml` is exit 2 (hint: `--standalone`). It works in the current directory only. | Discovery prefers `.todonotifier.toml`, so a section appended to `pyproject.toml` next to it would be ignored. `settings_file.has_pyproject_table` was added for the check. |
| A36 | `notify` builds the notifiers before scanning (missing env var: exit 2; none configured or all disabled: message pointing to `init` and the README, exit 2). It tries all notifiers, prints one stderr line per failure (`NotificationError` text; any other exception only by type name, traceback with `-v`) and returns 3 if any failed, unless `--fail-on` is met (1). `Notified X` lines go to stderr (hidden by `-q`). | Follows the 0.5 suggestion; secrets cannot leak through an arbitrary exception message. |
| A37 | `--since REF` compares the working tree with `REF` (staged and unstaged edits count) plus untracked files that are not ignored (counted in full). Renames are followed (`-M`), explicit `a/` `b/` prefixes make it independent of `diff.noprefix`/`mnemonicPrefix`, refs starting with `-` are rejected (no option injection, e.g. `--output=`), the ref is checked with `rev-parse --verify REF^{commit}` for a clear message. Unknown ref and "not a repository" are exit 2. `GitError` is the exception of `changed_lines`. | Matches the spec; the extra flags make parsing robust. |
| A38 | `git_meta.filter_git_listed(paths)` replaces the per-file `_is_listed_by_git` of the scanner: one `rev-parse` plus one `ls-files -z --cached --others --exclude-standard -- :(literal)<path>...` from the common directory of the files (split into several calls only above `MAX_PATHSPEC_CHARS`, 24,000). If the common directory is not in a repository, all files count as listed. | 0.4 follow-up (pre-commit speed). |
| A39 | Table, `github` and `sarif` show paths relative to the git root (`git_meta.to_repo_path`) when it is known, else relative to the scan root. Severity: overdue = error, stale or due within 7 days = warning, else notice (SARIF: note). `github` titles are `TODO overdue by 30d`, `TODO stale by 20d`, `TODO due in 3d`. Control characters in untrusted text are replaced in the table, the message of an annotation is one line (max 300 characters). SARIF has no tool version, so snapshots do not change on every release. | GitHub resolves annotation paths against the repository root. Terminal escape sequences in a TODO must not reach the user's terminal. |
| A40 | CLI logging: a handler that writes to the current `sys.stderr` is installed on the `todonotifier` logger (format `LEVEL: message`, with time and logger name for `-v`) and the previous handlers and level are restored when `main` returns. Colors only if stdout is a TTY, `NO_COLOR` is unset or empty, `TERM` is not `dumb` and there is no `--output`. Output that the terminal encoding cannot show is printed with `?` instead of crashing. | `main` must be callable repeatedly (tests, embedding) without leaking logging state. |
| A41 | `jsonschema` is a dev dependency only (`>=4.18,<5`). The JSON Schema is open for additional item properties (new optional fields do not bump `schema_version`) and validates the `date` format in the tests with the format checker. `utils.store_html` now returns the file path and writes UTF-8. | Spec and brief; the encoding fix avoids `UnicodeEncodeError` on non-UTF-8 locales. |
| A42 | CI is one job with a matrix (Python 3.10 to 3.14, `fail-fast: false`), Poetry installed with `pipx install poetry` before `setup-python` (`cache: poetry`), one `poetry install --with dev` per job. Steps: `black --check`, `isort --check-only`, `flake8` (all findings fail), `coverage run -m pytest`, `coverage report -m` (a separate `if: always()` step appends the Markdown table to `$GITHUB_STEP_SUMMARY`), then the self-check `todonotifier scan . --fail-on expired --format github` (`fetch-depth: 0` for blame). `pull_request` has no branch filter, `push` stays on `main` and `development`. | Stacked PRs target `roadmap/*` branches. |
| A43 | `fail_under = 100` in `[tool.coverage.report]` (the package is at 100%, 2478 statements). The repo scans itself with `[tool.todonotifier.exclude_dirs] name = ["tests", "sample_reports"]` (no `fail_on` in the file: CI passes `--fail-on expired`). | Dogfooding shows only real TODOs. |
| A44 | Actions in the workflows touched (`python-app`, `docs`, `release`) are pinned by full SHA with a version comment (checkout v7.0.1, setup-python v6.3.0, upload-artifact v7.0.2, download-artifact v8.0.2, configure-pages v6.0.0, upload-pages-artifact v5.0.0, deploy-pages v5.0.1, `pypa/gh-action-pypi-publish` v1.14.3; annotated tag dereferenced with `^{}`). SHAs were read with `git ls-remote`. | Repo convention (security workflows); Dependabot updates them. |
| A45 | `release.yml` has three jobs: `build` (tag must equal `v` + `poetry version`, `twine check`, upload `dist/`), `publish` (`environment: pypi`, `id-token: write`, no token) and `github-release` (`contents: write`, needs `build` and `publish`, so a GitHub Release only exists for what reached PyPI). Release notes come from `.github/scripts/changelog_section.py` (a file, not inline, so it can be run and linted locally); a tag that is not plain `vX.Y.Z` is created with `--prerelease`. Tag names go through `env:` variables, never inline `${{ }}` in `run:`. | Safer against injection through tag names; testable script. |
| A46 | PyPI has 1.4.0 as the latest release and no 2.0.0, so the README changelog has one `### v2.1.0` section (2.0.0 notes merged, breaking changes first, "2.0.0 was never released"). "Python 3.9 users stay on 1.x" (1.4.0). The heading no longer says "(Unreleased)": the section is final for the tag. `docs.yml` runs on Python 3.12. The CI badge row had a literal `\n` between badges, which was fixed (trivial). | Checked with `curl https://pypi.org/pypi/todonotifier/json` on 2026-10-23. |
| A47 | The legacy HTML reports (`todonotifier report`, the report part of emails) only know explicit dates: `TodoItem.to_legacy()` gives a default due date the no-date sentinel. So "Expired" never lists a stale item, and "Upcoming Week" does not list a default date either. The table, JSON, SARIF, the `github` format and the digests still show default dates (as "stale", and in the digest's "Due this week" when one is about to pass). `driver.run` is not affected. | The legacy structure has one date and cannot say where it came from; presenting a computed date as a deadline someone set, in a report named "Expired" or "Upcoming", is the failure D4 exists to avoid. |
| A48 | `notify --since REF` sends nothing, and logs "No TODOs on the lines changed since REF" at INFO, when no TODO is left on a changed line. `notify` without `--since` always sends, including an "all clear" digest for zero TODOs. The notifiers are still built first, so a config error is reported (exit 2) either way, and `--fail-on` is still judged. | A "nothing new" message on every pull request teaches people to mute the channel; a weekly digest that says "all clear" is information. |
| A49 | A `BrokenPipeError` on stdout (`... \| head -1`) ends the output quietly: the run goes on with stdout pointed at the null device, so the exit code still follows `--fail-on`. A `BrokenPipeError` anywhere else (for example on stderr) exits 0 quietly from `main`. | The Python-documented recipe, without losing the check result. |
| A50 | PATH arguments may be mixed with options through `cli._IntermixedParser` (`parse_known_intermixed_args`) on the subparsers. A command line with `--` is parsed the usual way, because the intermixed mode loses the paths after `--`. Checked on Python 3.10 to 3.14. | `scan a.py --format json b.py` is natural; `-- -odd.py` must keep working. |
| A51 | Teams text is neutralised, not escaped: `*`, `[`, `]`, the backtick and underscores that are not inside a word become look-alike characters (`notifier._teams_text`). The GitHub/Markdown digest keeps backslash escapes (GFM supports them). | A TextBlock supports a small Markdown subset and shows backslashes. Look-alikes cannot form links or emphasis, and `my_file_name.py` stays readable. |
| A52 | `.pre-commit-config.yaml` pins black 26.10.1, flake8 7.4.1 and isort 6.1.0 (the versions of `poetry.lock`/CI) and no `language_version`; `tox.ini` ignores W503; the dead Python <3.10 black constraint and the two GHSA allowances (and the 3.9 comment) of `dependency-review.yml` were removed (the lock holds black 26.10.1 only). | `pre-commit run --all-files` must agree with CI. |
| A53 | `default_due_days` is limited to 0 to 36500 (100 years) in the config file and on the command line. | Larger values overflow `date + timedelta` and crashed with exit 3. |
| A54 | The starter written by `todonotifier init` contains none of the default tags (not even in comments, and not "todo@example.com" for case-insensitive scans). | The first scan after `init` reported the config file's own comments as TODOs. |
| A55 | `Development Status :: 5 - Production/Stable`. | The package has had several 1.x releases on PyPI, has 716 tests at 100% line coverage and a stable CLI/API contract; "Beta" would undersell it. The classifier set also has `Environment :: Console`, `Intended Audience :: Developers`, `Operating System :: OS Independent` (as asked; only Linux was tested here) and the two Topic classifiers of the spec. |
| A56 | The `[tool.poetry]` layout stays; `homepage`, `repository` and `documentation` moved into `[tool.poetry.urls]` (Homepage, Repository, Documentation, plus Changelog and Issue Tracker). `poetry check` passes (exit 0) but still prints deprecation warnings for the whole `[tool.poetry]` table (name, description, license, authors, keywords, urls, scripts, "License classifiers"). | Moving to `[project]` would change how Poetry fills classifiers and also needs the `License ::` classifier, scripts and dependencies moved and re-checked with `poetry build`; it is a release-engineering change, not a quick win. Left for the maintainer (follow-up below). |
| A57 | The PyPI `description` does not mention the GitHub Action or pre-commit hook of the spec's example. | Neither exists yet (1.1, 1.2); metadata must not promise them. Update the description when they ship. |
| A58 | Badges: PyPI version uses shields.io (`pypi/v`) and links to PyPI; Downloads uses `static.pepy.tech/badge/todonotifier` and links to `pepy.tech/projects/todonotifier`. | `pepy.tech/badge/...` answers with a 308 redirect to the static host; using the final URLs avoids a hop that has broken before. All other badge URLs were requested and returned 200 (CI badge reads `passing`, Scorecard badge shows a score). |
| A59 | The comparison table uses `❌` for "not described in the source" and says so under the table; `⚠️ unverified` where a claim could not be confirmed. | A README not mentioning a feature is weaker evidence than a doc saying it is absent. |
| A60 | `--fail-on incomplete` is met by an item with `author_source != "annotation"` or `due_source != "explicit"`: the owner must be written in the comment (`@user` or `TODO(user)`) and the date as `{date}`. A `git blame` author and a default due date do not count. It is a valid `fail_on` in the config file too (`FAIL_ON_CHOICES`). The message counts the items. | The strict hook asks for what the author wrote; blame is off in the hook anyway. |
| A61 | `--blame` was added; `--no-blame` and `--blame` share `dest="blame"` (last one wins, neither is exclusive). | pre-commit appends `args` after `entry`, and a flag in `entry` cannot be removed, so the hook ships `--no-blame` and a consumer undoes it with `args: [--blame]`. A later `--fail-on` wins by argparse's normal rule. |
| A62 | Files named on the command line obey `exclude_dirs` (the directories between the file and the scan root) as well as `exclude_files`, through the same `_is_excluded` as the directory listing. When files are named and every path is inside the current directory, config discovery starts at the current directory instead of the first path. | Before this, `scan tests/x.py` ignored `exclude_dirs = ["tests"]`, and pre-commit would have flagged files a plain `scan .` skips. Passing a file from a nested package could silently use that package's config for all files. Paths outside the current directory keep the old behavior (first path). |
| A63 | A pre-commit run with nothing to scan (all files excluded, binary or of an unknown extension) prints the existing one-line `No files were scanned...` hint and exits 0; it was not made silent. | pre-commit hides the output of a passing hook, and the hint is useful for `scan wrongdir`. |

## Notes per workstream

### 0.1 Foundation

Built: `settings.py` (`ScanSettings`, `from_config`, leading dots stripped from `extensions`), `results.py` (`TodoItem`,
`ScanResult`, `build_web_url`, `compute_status`), `scanner.py` (`scan`, `ScanException`, `_enrich_items` hook),
`ConnectMethod.LOCAL` (+ `Connect.connect_method`, `Connect.source_path`), `BaseSummaryGenerator.reset()`, Python `^3.10`
(`poetry lock` only removed 3.9-only duplicates; no package was upgraded, but the lock header now says Poetry 2.4.3),
`[tool.coverage.run]`. The generator bug was real: two `run()` calls on `default_config` duplicated rows (reproduced before the fix).

Deviations and decisions:
- `driver.run` uses `ScanSettings.from_config` but does **not** call `scan()`. The unmodified tests in `tests/test_driver.py` patch
  `todonotifier.driver.get_files_in_dir` / `parse_files_for_todo_items` and expect the raw parse result to reach `generate_summary`,
  and report paths must keep the `project_dir_name/...` prefix. `scan()` and `driver.run` share `get_files_in_dir` and
  `parse_files_for_todo_items`, so parsing is not duplicated.
- `scan()` root rule: a single directory is its own root; otherwise (files, or several paths) the current working directory if all
  paths are inside it, else the closest common directory. `TodoItem.file` is relative to `ScanResult.root`.
- `TodoItem.author` is `None` when unknown (legacy `JANE_DOE` maps to `None`; `by_author()` groups it under `UNKNOWN_USER_NAME`).
- `generated_at` is timezone-aware local time; when `scan(today=...)` is passed it is that day at midnight, so `due_within()` agrees
  with the stored status fields. `ScanResult.from_dict` rejects a `schema_version` newer than 1.
- `LOCAL` report paths start with the scanned directory's own name (like `DRY_RUN_DIR`, whose paths are `project_dir_name/<dir name>/...`).
- Ran `black` (26.x, the version `pyproject.toml` pins) over `constants.py`, `notifier.py`, `todo_notifier.py` and `utils.py`: one-line
  docstring formatting only, needed for `black --check .` to pass.

Follow-ups:
- 0.3: fill the `_enrich_items` hook in `scanner.py`; call `TodoItem.refresh_status(today)` after setting default due dates. `web_url`
  assumes `ScanResult.root` is the repository root, so 0.3/0.6 should make paths repo-relative (or pass the root) when scanning a subdirectory.
- 0.4: `tags`, `require_comment` and `respect_gitignore` are accepted by `ScanSettings` but not acted on yet; `from_legacy` takes a `tag`
  argument for when the parser reports the matched tag. `.git` is not in `DEFAULT_EXCLUDE_DIRS` (harmless for `.py`, but relevant for other extensions).
- 0.7: CI matrix and docs workflow still on 3.9; README badge row bug is for 1.4.

### 0.2 Config file

Built: `todonotifier/settings_file.py` (`find_config_file`, `load_config`, `resolve_settings`, `resolve_project_config`, `ProjectConfig`,
`ConfigError`, `CLI_DEFAULTS`), `todonotifier/languages.py` (`COMMON_EXTENSIONS`, `expand_extensions`), `ScanSettings.author_aliases`, the
`tomli` conditional dependency, the README "Configuration file" section and changelog bullet. Decisions A7 to A16 above. 100% line coverage
of the new modules; the `tomllib` branch was also run once on Python 3.13 (all new tests pass there).

Follow-ups:
- 0.6: call `resolve_project_config(cli_overrides, config_path, start=<first scan path>)`; map `ConfigError` to exit code 2; pass `fail_on` from
  `ProjectConfig.fail_on` (CLI `--fail-on` goes in the overrides as `fail_on`). Leave relative CLI `paths` as given.
- 0.5: consume `ProjectConfig.notify` (validated dicts with `enabled` always present; read the env vars named by `*_env` yourself, at send time). Extend `_NOTIFIER_SCHEMA` in `settings_file.py` if a notifier needs more keys.
- 0.3: look up `ScanSettings.author_aliases` with the lower-cased git email.
- 0.4: `require_comment`, `ignore_case`, `respect_gitignore` and `tags` are now settable from the file but still ignored by the scanner until 0.4.

### 0.3 Git-aware ownership and TODO age

Built: `todonotifier/git_meta.py` (`find_git_root`, `is_shallow_repository`, `parse_blame_porcelain`, `blame_file`, `blame_files`,
`normalize_remote_url`, `detect_repo_web_url`, `detect_commit_sha`, `enrich_with_git`, `BlameLine`), wired into `scanner._enrich_items`
(only when `use_git_blame`). Library defaults are unchanged (`use_git_blame=False`; `driver.run` and `DefaultConfig` untouched). Decisions A17 to A20.
`tests/test_git_meta.py` (50 tests, real temp repos, two authors, fixed dates, shallow clone via `git clone --depth 1 file://`) plus a hook test in
`test_scanner.py`. 100% line coverage of `git_meta.py` and `scanner.py`; full suite 303 tests; black, isort and flake8 clean.

Performance (synthetic repo, 1,000 `.py` files, 100 TODOs in 100 files, two commits, 4 cores, git 2.43, best of 3, `today` fixed, script not committed):

| Files | `use_git_blame` off | on (`-L` per TODO) | ratio | on, whole-file blame |
|---|---|---|---|---|
| 200 lines each | 0.088 to 0.107 s | 0.283 to 0.305 s | 2.8x to 3.2x | 0.308 s (3.5x) |
| 1,500 lines each | 0.272 s | 0.616 s | 2.3x | 0.810 s (3.0x) |

The 2x target is **missed** on tiny files and nearly met on realistic ones. Cause: cost is dominated by one `git blame` process per TODO file
(about 3.7 ms each, 0.37 s sequential, 0.18 s with 4 workers, i.e. CPU-bound on this 4-core box; 8 to 16 workers are no faster than 4), while the
no-blame scan of tiny files is a very fast ~90 ms. Absolute overhead is ~2 ms per TODO-containing file. `-L` ranges were added (A19) and
re-measured; more workers do not help. The four setup git calls (`rev-parse` root, shallow, `remote`, `HEAD`) add ~20 ms.

Follow-ups:
- Possible speed-up if the ratio matters: run the four setup git calls concurrently with the blame pool (saves ~15 ms), or cache blame across runs keyed by file blob hash (0.6 CLI / SaaS).
- 1.1 (Action): reuse `git_meta.WARNING_SHALLOW_CLONE` text, and set `fetch-depth: 0` in the Action docs. Safe-directory problems in containers ("dubious ownership") make git fail, which currently shows as the "not a git repository" warning; the Action should run `git config --global --add safe.directory`.
- 0.6 CLI: set `ScanSettings.use_git_blame` / `default_due_days` from `CLI_DEFAULTS` (already done by `resolve_settings`); `--fail-on stale` should use `TodoItem.is_stale`.
- Submodules and nested repos are not blamed with their own repository (A19).

### 0.4 Tags, languages and detection accuracy

Built: word-boundary tag matching (one compiled regex per tag set, escaped, longest first, `_` is a word character) in
`todo_notifier.py`; `tags` / `require_comment` / `extended_syntax` arguments on `parse_files_for_todo_items` (old positional signature unchanged);
`models.TODO.tag` and `TodoItem.from_legacy` using it; `languages.COMMENT_SYNTAX`, `get_comment_syntax`, `CommentLexer`, `CommentIndex`;
`git_meta.list_git_files`; scanner wiring for `tags`, `ignore_case`, `require_comment` and `respect_gitignore`; `.git` in `DEFAULT_EXCLUDE_DIRS`; binary
skip and `errors="replace"`; `tests/fixtures/languages/` (10 languages: py, js, ts, go, java, sql, html, md, rs, yaml; 41 expected items). Decisions A21 to A25.

Existing tests touched (not silently):
- `tests/test_scanner.py::test_scan_should_find_the_same_todos_as_parse_files_for_todo_items` compared `scan()` with the legacy parser over
  `tests/sample_test_file.py`. They now differ on exactly one line, `class TODO:` (line 47): legacy message `:`, extended message `""`. The test now calls
  the parser with `extended_syntax=True`, so it still checks that `scan` uses the shared parser.
- `tests/test_settings_file.py` (two tests) asserted the 0.2 `CLI_DEFAULTS`; `require_comment: True` was added to the expected values (decision A22).
- `tests/test_todo_notifier.py::...streaming_parser_should_handle_exception_in_reading_file` still passes, but it now fails earlier (in the binary check)
  instead of in the streaming parser's own `open`; a new test covers that handler by patching `CommentLexer`.
All other existing tests pass unchanged. `DEFAULT_EXCLUDE_DIRS` is not asserted exactly anywhere.

Self-scan (`scan(resolve_settings({}, None, start="."))`, 80 files): 80 items, 79 in `tests/` (35 + 2 from `sample_test_file*.py`, 41 from the language
fixtures, 1 from a comment in `test_scanner.py` that mentions the tag in prose) and 1 in `todonotifier/todo_notifier.py` (also a comment that mentioned the tag
in prose; both comments were reworded). No hits in the README, AGENTS.md or `roadmap/*.md`. A tag in the middle of a comment sentence is reported by design.

Follow-ups:
- 0.6 CLI: `--tags`, `--ignore-case`, `--no-require-comment` and `--no-gitignore` flags map onto the `ScanSettings` fields (`resolve_settings` overrides).
  `scan()` raises `ScanException` for invalid tags.
- A pre-commit run with many staged files runs one `git ls-files` per file (about 4 ms each); batching them by directory is possible if it matters.
- Known heuristic gaps (see the `languages.py` docstring): nested block comments (Rust, Swift, Scala), Ruby `=begin`/`=end`, heredocs, `<script>`/`<style>`
  inside HTML, Python docstrings are not reported with `require_comment` (decision A24; revisit if users write TODOs in docstrings).
- The legacy `driver.run` path still reports `TODO(owner): msg` with the message `(owner): msg`. Switching it to the extended syntax would be a
  behavior change for existing users (and for the `class TODO:` expectation).
- `TODO_REGEX_PATTERN` is kept as an unused constant for import compatibility; remove it in a major version.

### 0.5 Chat and webhook notifiers plus the digest

Built: `todonotifier/digest.py` (`build_digest`, `Digest`, `DigestTotals`, `DigestSection`, `OwnerGroup`, `DigestItem`, `render_text`,
`render_markdown`, `safe_url`, `escape_markdown`, `describe_item`), `BaseNotifier.notify_result`, `DigestNotifier`, `SlackWebhookNotifier`,
`TeamsWebhookNotifier`, `WebhookNotifier`, the private `_post_json` helper, `EmailNotifier` (`starttls`, `username`, `from_env`, digest email via the new
`templates/digest_email.html`), `build_notifiers`, `NotificationError`, `NotifierConfigError`, the README "Notifications" section, changelog and
AGENTS.md. Decisions A26 to A32. `driver.run` and the old `EmailNotifier(...)` behavior are unchanged (old-style subclass and constructor tests).
No schema change was needed in `settings_file.py`: `build_notifiers` consumes the 0.2 tables as they are (tested against `resolve_project_config`).
Tests: `tests/test_digest.py`, extended `tests/test_notifier.py`, fixtures `tests/sample_results.py` and `tests/snapshots/`. 100% line coverage of
`digest.py` and `notifier.py`. A local HTTP server smoke test (503 with `Retry-After`, then 200, custom `Authorization` header) was run once by hand.

Follow-ups:
- 0.6: call `build_notifiers(project_config.notify)` for `todonotifier notify`, set `notifier.new_count` on every `DigestNotifier` for `--since` runs, call
  `notifier.notify_result(result, reports)` (the generated reports may be an empty list), map `NotifierConfigError` to exit code 2 and decide how a
  `NotificationError` of one notifier affects the others and the exit code (suggestion: try all, report each failure, exit non-zero).
- 1.1: `render_markdown(build_digest(...))` is ready for `$GITHUB_STEP_SUMMARY`; Slack/Teams secrets come in as Action inputs/secrets.
- ⚠️ Teams: the Workflows payload (`type: message` with an Adaptive Card attachment, version 1.4) follows the documented format from memory and could not be
  checked against live Microsoft docs in this run. Verify it, and whether the Markdown escapes (`\_`) render correctly in a Teams `TextBlock`, before release.
- Slack mentions from `author_aliases` (`<@U123>`) are not implemented; owners are shown as plain names.
- Teams message size (about 28 KB) is not enforced; only `max_items` limits it.
- Possible: a separate `max_items` for email, `Retry-After` HTTP-date support, discord-native payload.

### 0.6 Command-line interface

Built: `todonotifier/cli.py` (`main`, `build_parser`, `starter_config`, `get_version`, commands `scan`, `report`, `notify`, `init`), `__main__.py`,
`[tool.poetry.scripts]`, `todonotifier/formatters.py` (`format_result` for `table`, `json`, `github`, `markdown`, `sarif`; `build_reports`, `write_reports`,
`describe_due`, `severity`), `todonotifier/schemas/scan_result.schema.json`, `git_meta.changed_lines` / `parse_changed_lines` / `filter_git_listed` /
`to_repo_path` / `GitError`, `settings_file.has_pyproject_table`, README "Command line" section and changelog, AGENTS.md. Decisions A33 to A41.
Tests: `tests/test_cli.py` (pytest style, 100+ cases: every exit code path, flag mapping, fail-on matrix, formats, `--since`, notify with mocked
network, init), `tests/test_formatters.py` (snapshots `table.txt`, `table_color.txt`, `github.txt`, `sarif.json`, schema validation), additions to
`test_git_meta.py` (diff parsing, `changed_lines` in real repos, `filter_git_listed`), `test_scanner.py` (counts subprocess calls: one `ls-files` for 30
files, no blame without `use_git_blame`, one blame per file with it), `test_settings_file.py`, `test_utils.py`. 100% line coverage of the package (670 tests).

Real-world acceptance (venv with Python 3.13, `pip install .`, this repo = shallow clone, ~90 files, 78 TODOs, blame on, no config; venv deleted afterwards):
`todonotifier scan .` 0.33 s, `--format github` 0.40 s, `--format json` 0.38 s (the 30 s limit is met by a wide margin). `poetry run todonotifier scan .` takes about
1.1 s because of Poetry's own startup. `--fail-on expired` exits 1 with `14 overdue TODOs` (the fixtures of the tests have explicit past dates) and `--fail-on stale` exits 1.
The wheel contains `schemas/scan_result.schema.json` and the templates.

Deviations:
- `format_result("html")` raises `ValueError`; HTML goes through `build_reports` / `write_reports` (it produces files, the function is pure).
- `main` has no `today` parameter. Tests fix the day by patching `cli._today` or by using explicit past dates and 2020 commits.
- The SARIF output was not validated against the official schema (no copy offline); it follows the 2.1.0 structure GitHub code scanning documents.

Follow-ups:
- The legacy HTML templates are fragments, not pages, and render an empty file when a report has nothing to show (typically "Upcoming Week"). The "Expired" report cannot tell overdue from stale (legacy structure), and the generators use the real date, not `--since`/`today`. A proper HTML report page is a 1.3/Phase 1 candidate.
- 1.1 (Action): `scan --format github --since origin/$GITHUB_BASE_REF --fail-on expired`, `--format markdown >> $GITHUB_STEP_SUMMARY`, `--format sarif` for `upload-sarif`; shallow clones need `fetch-depth: 0` (blame and `--since`; the shallow warning text is in `git_meta`). GitHub shows at most 10 annotations of each level per step.
- 1.2 (pre-commit): `todonotifier scan <staged files> --fail-on expired --no-blame` is the intended hook; with blame, one `git blame` runs per file.
- `notify` always sends, even when the (filtered) result is empty; an `--only-if-items` flag could be added. With `--since`, `new_count` equals the number of items in the digest.
- argparse needs the PATH arguments to be contiguous (`scan a.py --tags X b.py` is rejected). A `BrokenPipeError` (`... | head`) shows as an unexpected error (exit 3).
- `changed_lines` counts the lines of every untracked, not ignored file (streaming); a huge untracked data file slows `--since` down.
- 0.7: `--version` reads the installed metadata (`unknown` in a bare checkout); `poetry.lock` changed only by `jsonschema` and its four dependencies (`attrs`, `referencing`, `rpds-py`, `jsonschema-specifications`); remember to run the docs build (`pdoc`) once, `__main__.py` is guarded by `if __name__ == "__main__"`.

### 0.7 Release prep v2.1.0 and housekeeping

Built: the CI matrix and self-check (A42), `fail_under = 100` and the repo's own `[tool.todonotifier]` section (A43), SHA-pinned
actions (A44), `.github/workflows/release.yml` and `.github/scripts/changelog_section.py` (A45), `docs.yml` on Python 3.12 (pdoc output
unchanged; `pdoc -o docs --docformat google todonotifier/` was run locally and builds), the README restructure (value proposition, Quick Start with
`pipx install` / `scan` / `init` / CI snippet with plain `pip install`, then Command line, Configuration file, Notifications, TODO Format, Exit codes,
Python API with the old `driver.run` examples, Generated Reports, Customization, Architecture) and the changelog reconciliation (A46),
`.report/` untracked and gitignored, `user_driver.py` moved to `examples/python_api_example.py` (README has no reference to it; AGENTS.md updated),
version `2.1.0` (`todonotifier --version` prints `todonotifier 2.1.0` after `poetry install`), `RELEASING.md`, AGENTS.md (commands, CI, gotchas).

**Not done on purpose (A4): no tag, no PyPI upload, no GitHub Release.** Maintainer steps are in [RELEASING.md](../RELEASING.md).
The acceptance criteria "CI is green on every version", "`pipx install todonotifier==2.1.0` works" and "a GitHub Release exists" can only be
checked after the stack is pushed, merged and tagged.

One-time maintainer setup for `release.yml` (also in RELEASING.md):
1. PyPI > project `todonotifier` > Manage > Publishing > add a GitHub trusted publisher: owner `ashu-tosh-kumar`, repository `todo_notifier`,
   workflow `release.yml`, environment `pypi`.
2. GitHub > Settings > Environments > create `pypi` (optionally with required reviewers).

Verification done locally (Python 3.10): 670 tests pass, coverage 100% (2478 statements), black, isort and flake8 clean;
`todonotifier scan . --fail-on expired --format github` on this repo prints `0 TODOs` (exit 0); `poetry build` gives
`todonotifier-2.1.0` wheel and sdist, `twine check` passes, the wheel holds `templates/*.html` (3 report templates and `digest_email.html`) and
`schemas/scan_result.schema.json`, and has no `tests/`; in a clean Python 3.10 venv the wheel installs and `todonotifier --version`,
`todonotifier scan .` and `python -m todonotifier --help` work. All workflow files parse with PyYAML (`actionlint` is not installed).
The workflows themselves (matrix on 3.11 to 3.14, `cache: poetry`, release) could not be run here.

Follow-ups:
- Check the first CI run on the stack: Python 3.14 resolves all locked dependencies, and `pipx install poetry` + `poetry env use "$(which python)"` picks
  the matrix interpreter. If `cache: poetry` misbehaves, drop it.
- `dependency-review.yml` has a comment saying we "still support 3.9" (stale), and `pyproject.toml` keeps a `black` constraint for Python `<3.10`
  that can no longer apply; both can be cleaned up (the second needs a `poetry lock`).
- 1.4 owns the badge row: the PyPI version badge still uses `badge.fury.io` and the Downloads badge `pepy.tech`; the Python Support badge shows 3.9 until 2.1.0 is on PyPI.
- Other workflows (`bandit`, `codeql`, `dependency-review`, `scorecard`) still only run for PRs against `main` and `development`, and `codeql.yml` uses
  `github/codeql-action@v3` tags rather than SHAs.
- `--fail-on expired` in CI uses `git blame`, hence `fetch-depth: 0`; 1.1 (the Action) should do the same by default or document it.
- `pre-commit run --all-files` disagrees with the CI checks (its own pinned black/isort/flake8 reformat `todonotifier/cli.py`, `tests/test_cli.py`,
  `tests/test_settings_file.py` and report W503 in `cli.py`). The changes were discarded; align the hook versions/args in `.pre-commit-config.yaml`
  with `pyproject.toml` / `tox.ini` (1.2 touches this file anyway).

### Phase 0 review

Reviewer: the P0 review agent, branch `roadmap/p0-review` (on top of 0.1 to 0.7). Method: read the whole Phase 0 diff, built throw-away git repos
(two authors, 2020 and recent commits, explicit and past dates, a subdirectory scan, `--since`, an ignored `node_modules`, a binary file, a Latin-1
file, CRLF line endings, a BOM, a symlink loop, a 1 MB minified bundle, a 20,000 TODO file) and ran `todonotifier` against them, outside a repo and
with broken configs, against a local HTTP server for `notify`, in a clean wheel install, and the test suite on Python 3.10 (Poetry env), 3.11,
3.13 and 3.14. The unmodified tests of `origin/development` (91) pass against this code.

#### Requirements audit

Status: met / partly / not met / maintainer step. "Evidence" is a test (`file::Class::test`) or a command that was run on this branch.

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 0.1 | `scan()` on `sample_test_file*.py` returns the same TODO set (message, user, date, line) as `parse_files_for_todo_items` | met, one documented deviation | `test_scanner.py::TestScanEquivalence::test_scan_should_find_the_same_todos_as_parse_files_for_todo_items`. `scan` uses the extended syntax, so `class TODO:` has the message `""` instead of `:` (A21); the test calls the parser with `extended_syntax=True` |
| 0.1 | Every existing test passes without modification | met | `git archive origin/development tests`, run against this code with `PYTHONPATH`: 91 passed. In this stack the only edits of old test files are two longer import lines and one call in `test_utils.py` that now keeps the return value of `store_html` (`git diff origin/development...HEAD -- tests/<old file>`, removed lines only) |
| 0.1 | `ScanResult` survives `json.dumps(to_dict())` to `from_dict` unchanged | met | `test_results.py::TestScanResult::test_json_round_trip_should_be_unchanged`, `test_scanner.py::TestScanResultFields::test_scan_result_should_survive_a_json_round_trip` |
| 0.1 | `scan()` creates no files and no temp dirs | met | `test_scanner.py::TestScanPurity::test_scan_should_create_no_files_and_no_temp_dirs` |
| 0.1 | `driver.run()` twice does not duplicate rows | met | `test_driver.py::TestRunInPlaceAndRepeatedRuns::test_run_twice_should_not_duplicate_report_rows` |
| 0.1 | Scope: `ScanSettings`, `scanner.scan`, `ScanResult`/`TodoItem` (`to_dict`/`from_dict`/`from_legacy`/`to_legacy`), `ConnectMethod.LOCAL`, `driver.run` on `ScanSettings.from_config`, Python `^3.10` with changelog note, `reset()` | met | `python = "^3.10"` in `pyproject.toml`; README v2.1.0 changelog; `test_settings.py`, `test_results.py`, `test_connect.py::...local...`, `test_driver.py` |
| 0.2 | Precedence matrix: defaults only, file only, CLI only, file plus CLI | met | `test_settings_file.py::TestPrecedence` (four tests) |
| 0.2 | Invalid key or type gives a helpful error, exit 2 in the CLI | met | `TestErrors::test_unknown_key_should_suggest_the_closest_key`, `::test_wrong_types_should_name_the_key_and_the_file`, `test_cli.py::TestScan::test_bad_config_files_are_usage_errors`; run: `tagz = [...]` gives `todonotifier: error: Unknown key 'tagz' in .todonotifier.toml. Did you mean 'tags'?`, exit 2 |
| 0.2 | No config file: defaults, no error | met | `TestDiscovery::test_no_file_should_give_defaults_and_no_error`; run in a bare directory |
| 0.2 | Scope: discovery up to the git root, `--config` override, `tomllib`/`tomli`, notifier tables with env var names, README example | met | `TestDiscovery`, `TestNotify` and the README "Configuration file"; the `tomllib` branch ran on 3.11, 3.13 and 3.14 (711 passed each) |
| 0.3 | Two authors, fixed dates: author and `created_date` correct | met | `test_git_meta.py::TestEnrichWithGit::test_should_fill_author_and_created_date_per_todo`; run: `Alice`/`Bob` and `2020-01-01` in the JSON of the test repo |
| 0.3 | `@user` always wins over blame | met | `TestEnrichWithGit::test_annotation_should_always_win_over_blame_and_aliases` |
| 0.3 | `default_due_days=90`: 100 days old is stale and not overdue, 10 days old is neither | met | `TestEnrichWithGit::test_default_due_days_should_mark_old_items_stale_and_never_overdue` |
| 0.3 | Shallow, non-git and uncommitted cases covered, no crash | met | `::test_shallow_clone_should_warn_once_and_still_run_blame`, `::test_non_git_directory_should_warn_once_and_skip`, `::test_uncommitted_and_untracked_lines`; new: `::test_a_repository_of_another_user_should_say_so...` |
| 0.3 | 1,000 files, 100 TODOs: blame run takes under 2x the run without | partly (a target, not a baseline) | Measured again here: 0.22 s without, 0.47 s with blame, **2.15x** (150 lines per file, 4 cores, best of 3). The 0.3 notes measured 2.3x to 3.2x. One `git blame` process per TODO file is the floor |
| 0.3 | Scope: aliases, `-L` ranges, bounded thread pool, warning once per run | met | `TestEnrichWithGit::test_should_apply_aliases_case_insensitively`, `TestBlame` |
| 0.4 | The three false-positive lines give no TODOs | met for the command line and config file defaults; for library defaults the string-literal line needs `require_comment` | `test_todo_notifier.py::TestDetectionRegressions` (three tests). Run: the three lines of the defects table give "No TODOs found" with the CLI defaults and with `--ignore-case`; with `--no-require-comment` the text `"TODO list"` inside a string is reported (by design: `require_comment` is opt-in for the library) |
| 0.4 | Fixtures in 6 or more languages give the expected items; a TODO in a string is ignored with `require_comment=True` | met | `test_languages.py::TestLanguageFixtures` (10 languages, 41 expected items) |
| 0.4 | `node_modules/` is ignored by default in a git repo that gitignores it | met | `test_scanner.py::TestScanRespectGitignore::test_default_cli_settings_should_not_report_gitignored_files`; run: `node_modules/pkg/index.py` was not reported |
| 0.4 | Existing tests still pass with the library defaults | met | see the 91 unmodified tests above |
| 0.4 | Scope: tags, `common` preset, binary skip, `errors="replace"`, streaming path above 10 MB | met | `TestRobustness`, `TestParseFilesForTodoItems::...streaming...`; run: Latin-1 file gives `caf\ufffd`, a NUL file is skipped, CRLF line numbers are right |
| 0.5 | Payload snapshots for Slack, Teams, generic webhook with the network mocked | met | `test_notifier.py::TestSnapshots` (`tests/snapshots/{slack,teams,webhook}.json`). The Teams snapshot changed in this review (A51). Not checked against live Microsoft documentation or a real Teams tenant (no network access to them) |
| 0.5 | Old-style `EmailNotifier(...)` and custom `BaseNotifier` subclasses work unchanged | met | `TestBackwardsCompatibility::test_old_style_email_notifier_uses_ssl_and_logs_in_as_the_sender`, `::test_notify_result_calls_notify_for_old_style_subclasses` |
| 0.5 | Webhook URLs and passwords never in log output (`assertLogs`) | met | `TestNoSecretsInLogsOrErrors` (3 tests); run: a 500 from a local server gave `Teams webhook POST failed with HTTP 500 ...` with no URL |
| 0.5 | Scope: `notify_result`, `digest.py`, Slack, Teams, webhook, STARTTLS, `from_env`, 10 s timeout, 2 retries, config keys | met | `test_digest.py`, `test_notifier.py`; a local-server run of `todonotifier notify` delivered the Slack JSON and exited 3 for the failing Teams endpoint |
| 0.6 | `pipx install .` then `todonotifier scan .` on this repo prints a table in under 30 s with no config | met | wheel built with `poetry build`, installed in a clean Python 3.10 venv (`pipx` itself is not installed here): `todonotifier scan <repo>` 0.4 s, `--version` prints `todonotifier 2.1.0`, `python -m todonotifier` works; the wheel holds `templates/*.html` and `schemas/scan_result.schema.json` |
| 0.6 | `--fail-on expired` is 1 for a passed explicit date, 0 for a repo with only stale TODOs; `--fail-on stale` is 1 there | met | `test_cli.py::TestFailOn::test_overdue_explicit_date`, `::test_only_stale_todos_do_not_fail_expired`; run: stale-only repo `expired` 0, `stale` 1; repo with an overdue explicit date `expired` 1 |
| 0.6 | `--format json` validates against the schema; `--format github` matches the workflow-command syntax | met | `TestFormats::test_json_validates_against_the_schema`, `::test_github_annotations_match_the_workflow_command_syntax`, `test_formatters.py` snapshots. SARIF (stretch) was not validated against the official schema (no copy offline) |
| 0.6 | `scan file1.py file2.py` scans only those | met | `TestScan::test_only_the_named_files_are_scanned`, new `TestParsing::test_mixed_paths_scan_only_those_files`; run: `scanned_files` was exactly the two files |
| 0.6 | `--since HEAD~1` reports only TODOs on changed lines | met | `TestSince::test_only_todos_on_changed_lines_are_reported`; run: one item (`src/app.py:10`) in the test repo |
| 0.6 | Scope: four commands and `--version`, shared flags, formats table/json/github/markdown/sarif/html, exit codes 0 to 3, `main(argv)` testable | met | `test_cli.py` (about 125 tests), `--help` shows the exit codes. Exit 3 for `... \| head -1` was a bug, fixed here |
| 0.7 | CI is green on every version of the matrix | maintainer step (cannot run Actions here) | `python-app.yml` parses, matrix 3.10 to 3.14, `fail-fast: false`. Locally: 716 tests passed on 3.10 (Poetry env) and, in throw-away venvs, on 3.11, 3.13 and 3.14 (black, isort, flake8 and coverage ran on 3.10 only) |
| 0.7 | `pipx install todonotifier==2.1.0 && todonotifier --version` works from PyPI | maintainer step | Nothing is tagged or published (A4, `RELEASING.md`). The equivalent local check is the wheel install above |
| 0.7 | A GitHub Release exists with notes | maintainer step | `release.yml` parses; `python .github/scripts/changelog_section.py v2.1.0` prints the notes |
| 0.7 | Scope: CI cleanup, `release.yml`, README quick start, hygiene, version bump | met | one job with a matrix and `black`/`isort`/`flake8`/coverage steps; `git ls-files .report` is empty and `.report/` is in `.gitignore`; `user_driver.py` is `examples/python_api_example.py`; `poetry version -s` is `2.1.0`; `docs.yml` on 3.12; `pdoc` builds |
| Exit | `todonotifier scan .` works on any git repo with zero config | met | run on five throw-away repos and this repo (see the review above). Outside a git repo it works too, with one warning and no authors |
| Exit | `todonotifier scan --fail-on expired` can gate CI | met | the exit code table above; this repository's own CI step exits 0 here (`0 TODOs: 0 overdue ...`) |
| Exit | Settings can live in `[tool.todonotifier]` in `pyproject.toml` | met | this repo does (`exclude_dirs`), `test_settings_file.py`; run in a throw-away repo with `tags = ["FIXME"]` |
| Exit | TODOs without `@user` get an owner from `git blame` | met | run: `old undated thing` got `Alice` (`author_source: git_blame`) |
| Exit | The known false-positive defects are fixed | met | see 0.4 |
| Exit | `v2.1.0` is published on PyPI | maintainer step | tag and publish are A4; checklist in `RELEASING.md` |

#### Issues found and fixed

The first seven are the known issues of the workstream notes. Every fix has a regression test; each was checked to fail without the fix.

1. **Broken pipe**: `todonotifier scan . | head -1` printed `unexpected BrokenPipeError` and exited 3 (A49). Now quiet, and the exit code follows `--fail-on`.
2. **Legacy "Expired" report counted stale items** (A47). `TodoItem.to_legacy()` gives default due dates the sentinel; "Upcoming Week" no longer lists default dates either.
3. **Interleaved arguments**: `scan a.py --format json b.py` was rejected with the top-level usage (A50).
4. **`notify` with nothing to report** (A48).
5. **pre-commit drift** (A52): black 24.3.0 / flake8 7.0.0 / isort 5.13.2 reformatted `cli.py`, `test_cli.py`, `test_settings_file.py` and reported W503. `pre-commit run --all-files` now passes and changes nothing (run with the network: the hook environments were installed).
6. **Stale constraints**: the 3.9 comment and GHSA allowances of `dependency-review.yml`, the black constraint for Python <3.10. `poetry lock` changed only the content hash.
7. **Teams cards** showed backslashes (A51); snapshot updated.

New findings:

8. **`todonotifier init` made the first scan report junk**: the starter's own comments contained the tags (`# TODO Notifier configuration`, ``# tags = ["TODO", ...]``, and `todo@example.com` with `--ignore-case`), so `scan` after `init` reported three TODOs in the config file, in `pyproject.toml` too (A54).
9. **Quadratic comment lexer**: a 1.2 MB minified JS file with one tag took 2 min 31 s (tokens were searched again after every string literal). Now 0.6 s; the output is identical on 5,400 random lines (compared with the old lexer).
10. **Quadratic line lookup**: 20,000 TODOs in one file took 25 s (every lookup added up all lines). Running totals and `bisect` are used; plain dict maps still work.
11. **`generated_at` was midnight** in every CLI JSON/webhook result (the CLI always passes today's date to `scan`). The real time is kept when the reference day is today.
12. **Unparsable-date warning**: printed the raw date and file path (terminal escape sequences from a scanned file) and the internal sentinel; a date such as `{99999999999999999999}` raised `OverflowError` and dropped the TODO with a traceback.
13. **Windows paths in `filter_git_listed`**: `git ls-files` prints `/`, the caller's paths have `\`, so `todonotifier scan file.py` (pre-commit) found no file on Windows. Paths are normalised (checked by simulating `ntpath`; not run on Windows).
14. **"Dubious ownership"** (Docker bind mounts, container jobs) was reported as "not inside a git repository". The warning now says why and gives the `safe.directory` command.
15. **Unreadable file**: a full traceback per file at ERROR level. One line now.
16. **`--default-due-days 99999999999`** crashed with `OverflowError` (exit 3); it is a config error (exit 2) now (A53).
17. **`digest.safe_url` raised `ValueError`** for a mistyped repository URL such as `http://[::1`, which broke the notification.
18. **`Connect.__str__` showed clone-URL credentials**, and `driver.run` logs it at INFO (a token in `https://user:token@host/...` reached the log).
19. **Symlink cycles** (`up -> ..`) in a directory walk (no git, or `--no-gitignore`) listed each file up to 41 times.
20. **A BOM** at the start of a YAML or shell file hid a comment on the first line.

#### Left unfixed on purpose

- **A lone `\r` is a line break for the parser** (Python universal newlines) but not for `git blame`/`git diff`: in a file with stray CRs (`\r\r\n`), line numbers after them are off by one for blame and `--since`. CRLF files are right. Fixing it means reading with `newline="\n"` in the parser and in the public `utils.compute_file_line_no_to_chars_map`; rare enough to wait.
- **dateutil is lenient**: `{1}`, `{may}` or `{10:30}` after a tag parse as dates in the current month or day (legacy `models.TODO` behaviour; the documented format is `YYYY-MM-DD`). A strict parser would break `{Dec 31 2024}`-style dates that work today.
- **`DEFAULT_EXCLUDE_DIRS` skips tracked directories named `build`, `dist`, `site`, `target`, `var`, `migrations`, `instance`, ...** even in a git repo (the legacy list for the Python library). A first-time user with TODOs in a `migrations/` folder sees none and no hint. Worth a decision for the CLI defaults (a Phase 1 docs point at least).
- **Owner spelling**: `@alice` (annotation) and `Alice` (blame) are two owners in the digest and the reports; only blame results go through `[authors]`. Aliases for annotations would be a feature.
- **Raw URLs in a TODO message** are auto-linked by Slack and Teams (the text cannot form a hidden link, but a phishing URL can be visible).
- **Table `DUE` column** does not say that a not-yet-due date is a default one (`2027-01-21 due in 90d` for an undated TODO); the `github`/JSON outputs do. **Wide (CJK) characters** misalign the table.
- **Created dates are UTC dates** of the commit's author time (decision in 0.3), which can differ by a day from `git log` in the author's time zone.
- **`git ls-files` failures or timeouts** (60 s) silently fall back to walking the tree, which includes `node_modules` when `--no-blame` hides the only warning.
- **`KeyboardInterrupt`** prints Python's traceback (exit 130). **`report`** writes `.report/` into the project, which is not git-ignored in other people's repositories (a hint would help).
- **Not verifiable here**: the Teams payload against live Microsoft documentation or a tenant; SARIF against the official schema; Windows and macOS (separators, console encodings); Python 3.12; the GitHub workflows themselves (parsed, not run).

#### Numbers

716 tests pass (670 before the review); `coverage report` is 100% (2541 statements, `fail_under = 100` holds); `black --check .`, `isort --check-only .`,
`flake8 . --config ./tox.ini` and `pre-commit run --all-files` are clean; `todonotifier scan . --fail-on expired --format github` on this repo exits 0.

### 1.2 pre-commit hook

Built: `.pre-commit-hooks.yaml` (hooks `todonotifier`: `scan --fail-on expired --no-blame`, and `todonotifier-strict`: `scan --fail-on incomplete --no-blame`; both
`language: python`, `types: [text]`, `pass_filenames`, `require_serial`), `--fail-on incomplete`, `--blame`, `exclude_dirs` for named files and
config discovery from the current directory for named files (A60 to A63), README "pre-commit" section (copy-paste config with `rev: v2.1.0`,
`args` customisation, Ruff TD note) and changelog, AGENTS.md. Tests: `tests/test_pre_commit_hooks.py` (loads the YAML with PyYAML, which comes with
`pre-commit` in the dev environment, so no new dependency; asserts ids, entries, settings and runs each entry through `main`), and in
`tests/test_cli.py` the classes `TestFailOnIncomplete`, `TestBlameFlag`, `TestExplicitFiles` (subprocess call count for 10 files: one `ls-files`, no
blame; config from the root; exclusions; unknown extensions and binary files; zero files). 758 tests, 100% line coverage, black, isort, flake8 and
`pre-commit run --all-files` clean; `todonotifier scan . --fail-on expired` exits 0.

Acceptance (pre-commit 4.3.0, network available, 2026-10-23):
- `pre-commit try-repo . todonotifier --files tests/sample_test_file.py` in this repo (committed HEAD): `todonotifier (overdue TODOs)....Passed`, exit 0, because
  this repo's config excludes `tests`.
- The same from a throw-away git repo that holds only `tests/sample_test_file.py` and no config (`pre-commit try-repo <this repo> todonotifier --files ...`):
  `Failed`, exit 1, with a table of 35 TODOs of which 14 are overdue (the sample has explicit dates in 2022 and 2026). `todonotifier-strict` fails too (exit 1).
  The failure output is the full table of the staged files plus the `--fail-on` line, and two warnings for the sample's unparseable dates.
- Timing, 10 files (6 modules of the package, `README.md`, `pyproject.toml`, `AGENTS.md`, `CONTRIBUTING.md`; 4,689 lines), best of 5:
  `todonotifier scan --fail-on expired --no-blame <10 files>` **0.19 s** (0.19 to 0.29); with `--blame` 0.22 s (fresh one-commit repo, so blame is cheap here);
  `pre-commit run todonotifier --files <10 files>` with the hook environment already installed **0.39 s** (0.39 to 0.45; 0.39 s with `args: [--blame, --fail-on, stale]`).
  `pre-commit try-repo` takes about 5 s because it clones and installs the environment on every call; the first normal run installs the environment once (a few seconds).
  The target of 2 s is met by a wide margin.

Deviations and notes:
- The brief names `Claude Opus 5.5` in the commit trailer; the session's own attribution reminder says `Claude Sonnet 5.5`, which is used.
- `todonotifier-strict` fails on items it does not need to show: the table lists every TODO in the staged files, not only the incomplete ones. Fine for a hook (the exit line says how many), but a `--only-failing` output option could be a follow-up.
- Ruff `TD002`/`TD003` overlap is explained in the README; no code depends on Ruff.
- `pyyaml` is not a declared dev dependency (it arrives with `pre-commit`, already a dev dependency); declare it if `pre-commit` is ever dropped.

Follow-ups:
- 1.3 (docs): the quickstart step "add the pre-commit hook" can link the README section (`#pre-commit`). The PyPI `description` (A57) can now mention the hook; the GitHub Action (1.1) is still to come.
- The maintainer must tag `v2.1.0` before `rev: v2.1.0` in the README resolves (RELEASING.md); until then use the commit SHA.
- This repository does not use its own hook in `.pre-commit-config.yaml` (it would need `repo: local` or a published tag); consider it after the release.
- The hook scans whole files, not only the staged lines (`--since` needs a ref; `HEAD` would also count unstaged edits). Staged-lines-only would be a separate feature.

### 1.4 Discoverability quick wins

**Built:**
- `pyproject.toml`: new `description` (116 characters), 12 `keywords`, 14 `classifiers`, and `[tool.poetry.urls]` (Homepage, Repository, Documentation, Changelog = `README#changelog`, Issue Tracker). `poetry check` exits 0; `poetry build` works and `unzip -p dist/*.whl '*/METADATA'` shows `Summary`, `Keywords`, every `Classifier` and the five `Project-URL` lines. `dist/` was deleted afterwards (decisions A55 to A57).
- README: SEO paragraph under the title, a "How it compares" section (decision A59), fixed badges (A58), a short Contributing section that links to `CONTRIBUTING.md`, and a changelog bullet. The README badge row had no literal `\n` left (0.7); every badge and badge link was requested and returned 200 (or the one redirect described in A58).
- `CONTRIBUTING.md` (setup, checks, hooks, tests and 100% coverage, commit style, adding a language, adding a notifier), `.github/ISSUE_TEMPLATE/{bug_report,feature_request,config}.yml`, `.github/pull_request_template.md`. `AGENTS.md` links to CONTRIBUTING.md and notes why the `[tool.poetry]` layout stays.
- `roadmap/good-first-issues.md`: 9 issues ready to paste (title, labels, body, acceptance criteria), taken from the "left unfixed" list and the workstream follow-ups.

**Competitor claims, checked 2026-10-23 with four fetches** (todo-to-issue-action README, Todo Tree README, Ruff rules page, Ruff docs home). What was verified: todo-to-issue-action creates, updates and closes issues from TODOs in a push diff, assigns them from `TODO(@user)` or `assignees:`, lists 62 languages, and its README describes no deadlines, overdue alerts, digests or PR checks. Todo Tree is a ripgrep based tree view with highlighting, status bar counts, JSON export and a configurable regex; its README describes no deadlines, owners, notifications, CI or issue creation. Ruff TD001 to TD007 are format and presence rules (tag, author, issue link, colon, description, capitalization, space after colon), none about dates; Ruff describes itself as a Python linter with VS Code integration. **Unverified:** whether Ruff's own docs describe CI/PR use (the pages read do not), and Todo Tree's exact language coverage (README gives no list). Both are marked in the table. Absence in a README is shown as `❌ not described`, with a note that it is not proof.

**Deviation:** the spec's example description names the GitHub Action and pre-commit hook; they do not exist yet, so the description does not (A57). `Typing :: Typed` was not added: the package ships no `py.typed`.

**Manual GitHub settings for the maintainer** (repository Settings, none of this can be done from code):
- [ ] **About box, Website:** `https://ashu-tosh-kumar.github.io/todo_notifier/` (or the PyPI page until the docs site is the landing page).
- [ ] **About box, Description:** `Track TODO and FIXME comments with deadlines and owners. Overdue TODO reminders via CLI, CI, Slack, Teams and email.`
- [ ] **Topics:** `todo`, `fixme`, `technical-debt`, `code-quality`, `developer-tools`, `github-actions`, `pre-commit`, `python`, `cli`, `todo-comments`, `reminder`, `slack` (GitHub allows up to 20; drop `github-actions` and `pre-commit` until 1.1 and 1.2 ship if you want the topics to be strictly true).
- [ ] **Social preview image:** Settings, General, "Social preview", upload a 1280 x 640 px PNG or JPG (under 1 MB) with the name, the one-line value proposition and a table screenshot (a safe margin of 40 px).
- [ ] **Discussions:** Settings, General, Features, tick "Discussions", then create the categories "Q&A", "Ideas" and "Show and tell". The issue form contact links and the README point to `/discussions`; they 404 until this is on.
- [ ] **Labels:** create `good first issue` (and `enhancement`, `bug`, `documentation`, `detection`, `cli`, `notifications`, `owners` if missing), then create the issues from `roadmap/good-first-issues.md`.
- [ ] **Security policy:** check that Settings, Code security, "Private vulnerability reporting" is on, because the issue chooser links to the security policy.
- [ ] **PyPI:** after `v2.1.0` is published, the README renders on the project page with the new keywords, classifiers and links; check "Project links" shows Changelog, Documentation, Issue Tracker. The Python-versions badge shows 3.10+ only after that release.
- [ ] **OpenSSF Best Practices badge** (commented out in the README): register at bestpractices.dev, then enable the line.
- [ ] Optional: re-check the comparison table's sources before each launch post (1.5), because the tools change.

**Follow-ups:**
- Move `pyproject.toml` to `[project]` metadata (Poetry 2 deprecation warnings), as its own change, and re-check the `poetry build` METADATA diff (A56).
- Docs site (1.3): move the comparison table there; the README keeps a short version. Ship `py.typed` if the project wants `Typing :: Typed`.
- Update the PyPI description when the GitHub Action (1.1) and the pre-commit hook (1.2) are released, and replace "coming soon" in the README intro.
