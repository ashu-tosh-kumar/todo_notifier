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

| # | Workstream | Branch | PR | Status | Notes |
|---|---|---|---|---|---|
| - | Roadmap docs + progress file | `claude/serene-hopper-qkult2` | | 🟡 in progress | Merged latest `development` |
| 0.1 | Foundation | `roadmap/0.1-foundation` | | ⬜ todo | |
| 0.2 | Config file | `roadmap/0.2-config-file` | | ⬜ todo | |
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
