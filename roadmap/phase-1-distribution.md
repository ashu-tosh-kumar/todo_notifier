# Phase 1: Distribution

**Goal:** put TODO Notifier where developers already work (GitHub Actions, pre-commit, PyPI
search, Python communities), with documentation that delivers the "5-minute setup" promise.

⚠️ Estimated effort: 2 to 3 weeks, of which 1.4 and the 1.3 drafting can start immediately.

**Exit criteria**
- The GitHub Action is listed on the Marketplace.
- The pre-commit hook is usable from this repo.
- The docs site has a 5-minute quickstart.
- PyPI metadata and the README are optimized.
- The launch posts are out, and baseline metrics were recorded before launch.

Read [README.md](README.md) first for the dependency graph, shared agent rules and open
decisions.

---

## 1.1 GitHub Action

**Size:** M · **Hard dependencies:** 0.6, 0.7 (published `v2.1.0`) · **Soft dependencies:** 0.3, 0.5 · **Blocks:** 1.5

**Positioning:** this is not another "TODO to issue" action (alstr/todo-to-issue-action
already covers that). It focuses on **deadlines, owners and digests**: "fail or warn on
overdue TODOs in PRs" and "weekly overdue-TODO digest to Slack".

### Scope
1. **Repository:** per D2 (decided), a new public repo `todonotifier-action` with `action.yml`
   at its root. ⚠️ GitHub Marketplace requires the action metadata file at the root of a public
   repository. Check GitHub's current publishing docs before starting.
2. **Composite action:** `actions/setup-python` → `pip install todonotifier==<version input>` →
   `todonotifier ...`. Cache pip.
3. **Inputs:** `mode` (`pr` or `digest`), `version`, `config` (path), `fail-on`
   (`none`, `expired`, `stale`, `any`; default `none`, see D4 design), `default-due-days`
   (default `90`), `tags`, `extensions`, `slack-webhook`, `teams-webhook`,
   `comment` (true/false), `working-directory`.
4. **Outputs:** `total`, `overdue`, `stale`, `new`, `report-path`.
5. **`pr` mode** (on `pull_request`):
   - `todonotifier scan --since ${{ github.event.pull_request.base.sha }} --format github`, so
     new TODOs show up as inline annotations;
   - write a summary table to `$GITHUB_STEP_SUMMARY`;
   - optionally post or update a single sticky PR comment ("This PR adds 3 TODOs, 1 has no
     owner, 0 overdue"). This needs `pull-requests: write`. Keep it opt-in;
   - exit non-zero according to `fail-on`.
6. **`digest` mode** (on `schedule`, e.g. weekly):
   - full scan, then send to the Slack, Teams or email notifiers configured from inputs or
     secrets;
   - upload the HTML reports as a workflow artifact;
   - write the job summary.
7. **Git history:** blame needs full history. Document `actions/checkout` with
   `fetch-depth: 0` in every example, and surface the shallow-clone warning from 0.3 as an
   `::warning`.
8. **Least privilege:** document the minimal `permissions:` block for each mode
   (`contents: read`, plus `pull-requests: write` only when `comment: true`).
9. **Examples and tests:** copy-paste workflow files in the action README for both modes. Add
   a self-test workflow in the action repo that runs against fixture files and checks the
   outputs.
10. **Release:** tag `v1.0.0` plus a moving `v1` tag, then publish to the Marketplace with the
    categories "Code quality" and "Utilities".

### Acceptance criteria
- A sample repo using `uses: <owner>/todonotifier-action@v1` in `pr` mode shows annotations on
  a PR that adds an overdue TODO, and fails when `fail-on: expired`.
- `digest` mode on `workflow_dispatch` posts to a test Slack webhook and uploads the artifact.
- The Marketplace listing is live.

---

## 1.2 pre-commit hook

**Size:** S · **Hard dependencies:** 0.6, 0.7 · **Blocks:** 1.5

### Scope
1. Add `.pre-commit-hooks.yaml` at the root of this repo with:
   - `todonotifier`: `entry: todonotifier scan --fail-on expired`, `language: python`,
     `pass_filenames: true`, `types: [text]`. It fails a commit that touches files with
     overdue TODOs;
   - `todonotifier-strict` (optional hook): fails on any TODO without an owner or date. It
     overlaps with Ruff's TD rules, so the docs should say: use Ruff TD for format linting and
     TODO Notifier for deadlines.
2. Make sure the CLI handles a list of filenames efficiently (no full-repo walk). Skip blame
   by default in this hook for speed and document how to turn it on.
3. Document usage with `rev: v2.1.0`.

### Acceptance criteria
- `pre-commit try-repo . todonotifier --files tests/sample_test_file.py` runs and gives the
  expected result.
- The hook runs in under 2 s on a typical commit of about 10 files (measured, not assumed;
  record the number in the PR).

---

## 1.3 Documentation and the 5-minute guide

**Size:** M · **Soft dependency:** 0.6 (drafting can start in Wave 2) · **Hard dependency:** 0.7 (final content) · **Blocks:** 1.5

### Why
The current docs site is only a pdoc API reference (`.github/workflows/docs.yml`), and the
main setup guide lives on Medium. New users need task-oriented docs.

### Scope
1. **Site:** add a user guide built with MkDocs Material, keep the pdoc API reference under
   `/api/`, and deploy both from the existing Pages workflow. Note: `docs/` is gitignored and
   used as the pdoc output folder. Put MkDocs sources in a new folder (e.g. `site_src/`) or
   change the pdoc output path, and update `.gitignore` and the workflow together.
2. **Pages:**
   - **Quickstart (5 minutes):** `pipx install` → `todonotifier scan` → `todonotifier init` →
     add the GitHub Action → add the pre-commit hook. Each step has one copy-paste block and
     the expected output;
   - **TODO syntax:** tags, `{date}`, `@owner`, and how blame fills the gaps;
   - **Configuration reference:** every `ScanSettings` key with its type, default and
     example. Generate it from the dataclass so it stays in sync;
   - **CLI reference:** commands, flags and exit codes;
   - **CI integrations:** GitHub Action (both modes), GitLab CI snippet, generic CI;
   - **pre-commit**;
   - **Notifications:** Slack, Teams, email and generic webhook setup, with screenshots;
   - **Python API:** the existing `driver.run` usage and custom generators and notifiers;
   - **Comparison** (see 1.4) and **FAQ**.
3. **README:** rewrite as a landing page: one-line value proposition, a demo GIF, three
   commands, a feature list, links to the docs. Move the long content into the docs.
4. **Demo GIF:** a terminal recording of `scan`, `--fail-on` and a Slack digest screenshot.
   ⚠️ Charm's VHS is one scriptable recorder. Commit the tape file so the GIF can be
   regenerated.
5. Port the Medium guide content into the docs and link Medium → docs, not the other way
   round.

### Acceptance criteria
- A new user can follow the Quickstart end to end in a clean environment in 5 minutes or less.
  Test it yourself and time it.
- The configuration reference is generated from code, and CI fails if it is stale.
- The docs site deploys from `main`.

---

## 1.4 Discoverability quick wins

**Size:** S · **Hard dependencies:** none, **start now** · **Blocks:** 1.5

### Scope
1. **Fix the broken README badge row** (literal `\n` at `README.md:9`).
2. **PyPI metadata** in `pyproject.toml` (a new release is needed before PyPI shows it; it
   ships with 0.7):
   - `description`: e.g. "Find, assign and get reminded about overdue TODO/FIXME comments.
     CLI, GitHub Action and pre-commit hook.";
   - `keywords`: todo, fixme, technical-debt, code-quality, developer-tools, cli,
     github-actions, pre-commit, linter, productivity;
   - `classifiers`: Development Status, Environment :: Console, Intended Audience ::
     Developers, Topic :: Software Development :: Quality Assurance, Topic :: Software
     Development :: Bug Tracking, License :: OSI Approved :: MIT License, and Programming
     Language :: Python :: 3.10 to 3.14 (D1);
   - `[tool.poetry.urls]`: Changelog, Issue Tracker, Documentation.
3. **GitHub repo settings** (the maintainer does these manually; the agent lists them in the
   PR): topics (`todo`, `fixme`, `technical-debt`, `code-quality`, `developer-tools`,
   `github-actions`, `pre-commit`, `python`, `cli`), a social preview image, the website link,
   and GitHub Discussions turned on.
4. **Contributor on-ramp:** `CONTRIBUTING.md` (the setup section moves there from the README),
   issue templates (bug, feature), a PR template, and 5 or more issues labelled
   `good first issue` taken from the roadmap follow-ups.
5. **Comparison table** (README section, moved to the docs in 1.3). Be honest. It compares
   TODO Notifier with alstr/todo-to-issue-action, Todo Tree (VS Code) and Ruff's `TD` rules on:
   deadlines, owners, overdue alerts, digests, PR checks, issue creation, IDE view and
   language support. ⚠️ Verify each competitor's features from their current docs before
   publishing, and link the sources.
6. **SEO wording** for the README, docs titles and the PyPI description: "track TODO comments",
   "TODO deadline reminder", "overdue TODO", "FIXME tracker", "technical debt tracker",
   "TODO GitHub Action". Avoid broad terms like "automated code review tools".

### Acceptance criteria
- The badges render correctly on GitHub.
- `poetry check` passes, and `python -m build` (or `poetry build`) metadata shows the new
  keywords and classifiers.
- The PR lists the manual GitHub settings for the maintainer.

---

## 1.5 Launch and community

**Size:** M (mostly done by the maintainer; an agent drafts content) · **Hard dependencies:** 1.1, 1.2, 1.3, 1.4 · **Soft dependency:** 2.1 (waitlist live) · **Blocks:** 2.3

### Scope
1. **Baseline metrics** (record before launch; track weekly in `roadmap/metrics.md`):
   - PyPI downloads ([pepy.tech](https://pepy.tech/project/todonotifier),
     [pypistats.org](https://pypistats.org/packages/todonotifier));
   - GitHub stars, forks, unique visitors (Insights → Traffic) and "Used by" dependents;
   - Action Marketplace usage and waitlist signups.
2. **Content the agent drafts and the maintainer reviews and posts:**
   - an anchor blog post, "Your TODOs have no deadlines: here's how to fix that", on dev.to
     or Hashnode, cross-posted to Medium with a canonical link to the docs;
   - a Show HN post (title plus a first comment explaining why and how);
   - Reddit posts. ⚠️ Read each subreddit's self-promotion rules first:
     r/Python (use the designated showcase thread or flair), r/devops, r/developersIndia.
     Skip r/MachineLearning and r/learnpython (off-topic for this tool);
   - a LinkedIn post, plus an X/Bluesky thread with the GIF;
   - newsletter submissions: PyCoder's Weekly and Python Weekly (both accept link
     submissions ⚠️; confirm the current submission process).
3. **Curated lists** (submit after launch traction, because many lists expect some adoption ⚠️):
   awesome-python (Code Analysis section), awesome-actions, awesome-pre-commit (if it exists ⚠️).
4. **Launch-week routine:** reply to every comment within 24 h, turn feedback into GitHub
   issues, and ship one visible fix during launch week.

### Acceptance criteria
- The baseline metrics are recorded with the date.
- The blog post, Show HN post and at least 2 Reddit posts are published (by the maintainer).
- Feedback is captured as labelled GitHub issues.
