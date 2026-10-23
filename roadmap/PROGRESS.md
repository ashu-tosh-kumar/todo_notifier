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
| 0.2 | Config file | `roadmap/0.2-config-file` | | 🟡 in progress | |
| 0.3 | Git blame ownership and age | `roadmap/0.3-git-blame` | | ⬜ todo | |
| 0.4 | Tags, languages, detection accuracy | `roadmap/0.4-detection` | | ⬜ todo | |
| 0.5 | Chat and webhook notifiers + digest | `roadmap/0.5-notifiers` | | ⬜ todo | |
| 0.6 | CLI | `roadmap/0.6-cli` | | ⬜ todo | |
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
