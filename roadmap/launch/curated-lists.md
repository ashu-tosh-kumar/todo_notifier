# Curated lists

Status: draft, maintainer to submit. **Wait for traction before submitting.** Many lists expect some adoption before they accept a project, ⚠️ often stated as a minimum
number of stars, a minimum age, or evidence of real use. I did not check the current rules of any of these lists. Read each list's contributing guide first and follow it over this file.

Suggested bar before submitting (a judgment call, not a rule): `v2.1.0` published for at least a few weeks, the docs live, a handful of stars or users who are not you, and no
open bug that breaks the quickstart. Look at the metrics (`roadmap/metrics.md`) at week 4 and decide then. A rejected pull request is not harmful, but a list maintainer's
first impression of the project is worth protecting.

One pull request per list, one line per pull request, no promotional wording. Read the last 10 merged pull requests of the list to see what a good one looks like.

## 1. awesome-python

- Repository: <https://github.com/vinta/awesome-python> (⚠️ confirm the current repository and that it is still maintained)
- Section: **Code Analysis** (⚠️ confirm the section still exists under that name; the list has been reorganized before)
- Why it fits: a static analysis tool for Python projects. The tool also scans other languages' comments, but the CLI is a Python package.
- ⚠️ The contributing guide historically asks for: one pull request per project, the entry in alphabetical order, a short description ending in a period (or not; check the format of
  the neighbours), and a project that is established. Verify.

Exact line to submit (adjust to the list's format after reading its neighbours):

```markdown
* [todonotifier](https://github.com/ashu-tosh-kumar/todo_notifier) - Find TODO comments, resolve owners and ages from git blame, and fail CI on expired deadlines.
```

Suggested pull request title: `Add todonotifier to Code Analysis`

Suggested pull request description (short; copy what the guide asks for):

> Adds todonotifier: a CLI that finds TODO/FIXME comments, takes owners and ages from git blame and fails CI when a written deadline has passed. MIT, on PyPI, docs at https://ashu-tosh-kumar.github.io/todo_notifier/.

## 2. awesome-actions

- Repository: <https://github.com/sdras/awesome-actions> (⚠️ confirm the current repository)
- Section: ⚠️ pick the closest of its categories after reading the list (likely a "Utility", "Code quality" or "Pull request / issue management"-type section). Do not guess: read it.
- ⚠️ **Prerequisite:** the list is about GitHub Actions, so submit only when the Action is usable by others, ideally published on the Marketplace in its own repository
  (`todonotifier-action`, decision D2; currently it lives in `integrations/github-action/` of this repo, decision A3, and works as
  `uses: ashu-tosh-kumar/todo_notifier/integrations/github-action@v2.1.0`). If the list only accepts Marketplace actions or actions in a root `action.yml`, wait for the move.

Exact line to submit (adjust the link to the action's final repository if it moves):

```markdown
- [TODO Notifier](https://github.com/ashu-tosh-kumar/todo_notifier/tree/main/integrations/github-action) - Annotate pull requests with overdue TODOs, fail the check when a deadline has passed, and send a weekly digest to Slack or Teams.
```

Suggested pull request title: `Add TODO Notifier`

## 3. awesome-pre-commit

- ⚠️ **I am not sure that this list exists.** There are lists of pre-commit hooks (for example, pre-commit.com has a page of supported hooks and a list of "pre-commit hooks" repositories),
  but I cannot say there is an actively maintained "awesome-pre-commit" repository. Search GitHub for `awesome-pre-commit` and for "pre-commit hooks list" first. If none is
  maintained, skip this step.
- If a maintained list exists, the entry is a hook repository with the hook id:

```markdown
- [todonotifier](https://github.com/ashu-tosh-kumar/todo_notifier) - Stops a commit that touches an overdue TODO (hook id `todonotifier`; `todonotifier-strict` also wants an owner and a date on every TODO).
```

The hook ids (`todonotifier`, `todonotifier-strict`) were checked against `.pre-commit-hooks.yaml` on 2026-10-24. The hook ref `rev: v2.1.0` must exist as a tag before anyone can use it.

## Other places to consider later (not drafted)

- The "Supported hooks" page of pre-commit.com, if it accepts third-party additions. ⚠️ unverified.
- Hacktoberfest-style or "good first issue" aggregators, once the `good first issue` issues exist (`roadmap/good-first-issues.md`). ⚠️ check each one's rules.
- Python Package Index classifiers and keywords are already done in 1.4; nothing to submit.
