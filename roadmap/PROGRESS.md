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
| 0.6 | CLI | `roadmap/0.6-cli` | | ✅ done | See "Notes per workstream" below |
| 0.7 | Release prep v2.1.0 + CI housekeeping | `roadmap/0.7-release` | | ⬜ todo | Tag/publish is a maintainer step |
| P0 | Phase 0 review | (fixes on the tip branch) | | ⬜ todo | |
| 1.4 | Discoverability quick wins | `roadmap/1.4-discoverability` | | ⬜ todo | |
| 1.2 | pre-commit hook | `roadmap/1.2-pre-commit` | | ⬜ todo | |
| 1.1 | GitHub Action (seed in this repo) | `roadmap/1.1-github-action` | | ⬜ todo | See decision A3 |
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
