# Brief for implementation agents

Shared rules for every agent implementing a roadmap workstream in this run. The orchestrator
passes the workstream ID and any extra context; everything else is here.

## Before you start
1. You are already on the workstream branch (`roadmap/<id>-<slug>`). Do **not** switch,
   create, push or rebase branches, and do **not** open PRs. The orchestrator does that.
2. Read, in order: `AGENTS.md`, `roadmap/README.md`, the phase file section for your
   workstream, `roadmap/PROGRESS.md` (decisions A1+ and notes left by earlier workstreams),
   then the code you will change.
3. The roadmap's maintainer decisions (D1 to D6) and the orchestrator's decisions (A1+) are
   fixed. If you must make a new product or engineering call, make the best one you can, and
   record it in the "Decisions" table of `roadmap/PROGRESS.md` (next free `A<n>` id).

## While working
- Use the Poetry env (Python 3.10, the minimum version): `poetry run <cmd>`.
- Library rules from `roadmap/README.md` apply: Python 3.10 syntax is allowed, minimal runtime
  dependencies (standard library first), backwards compatibility of the public API, type hints
  on all arguments, return values **and variables**, Google-style docstrings, match the
  existing module docstring and comment style.
- Tests: `unittest.TestCase` classes in `tests/`, run with pytest. Every new module gets
  `tests/test_<module>.py`. Mock network and SMTP. Build temporary git repos inside tests with
  fixed `GIT_AUTHOR_*` / `GIT_COMMITTER_*` env vars. Never write outside temp dirs.
- **Coverage:** 100% line coverage for every module you create or change
  (`poetry run coverage run -m pytest && poetry run coverage report -m`). Use
  `# pragma: no cover` only for code that genuinely cannot run in tests, and say why in a
  comment.
- Security: no secrets in config files, logs or exception messages. `subprocess` with list
  arguments only, never `shell=True`. Timeouts on all network and subprocess calls.
- Stay inside the workstream's scope. Write out-of-scope findings as "Follow-ups" in the
  `roadmap/PROGRESS.md` notes for your row.

## Before you finish
1. Run all of these and make them pass:
   `poetry run pytest -q`, `poetry run black --check .`, `poetry run isort --check-only .`,
   `poetry run flake8 . --config ./tox.ini`, and the coverage command above.
2. Update docs:
   - `README.md` changelog: add bullets under `### v2.1.0 (Unreleased)` (create it above
     `v2.0.0` if missing). Keep entries from other workstreams.
   - `AGENTS.md` if you changed commands, architecture, gotchas or compatibility rules.
   - `roadmap/PROGRESS.md`: set your row to ✅ and write short notes (what was built, any
     deviation, follow-ups).
3. Commit everything with a Conventional Commit message (`feat(scope): ...`) ending with:

   ```text
   Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
   Claude-Session: https://claude.ai/code/session_01VcRbvQzqiB2UtnSLYc8Hbd
   ```

   You may make several commits. Leave the working tree clean.
4. Reply with a short report (at most about 400 words): what changed, how each acceptance
   criterion is met, decisions you made, follow-ups, and the test and coverage numbers.
