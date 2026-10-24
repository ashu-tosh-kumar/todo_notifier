# Newsletter submissions

Status: draft, maintainer to submit.

⚠️ **Confirm the current submission process before you send anything.** I did not fetch either site. As far as I remember: PyCoder's Weekly takes link suggestions through a form on
its website (⚠️ something like `https://pycoders.com/submissions`; find the current link in the footer of the newsletter or on pycoders.com), and Python Weekly takes submissions
by a form or an email (⚠️ find the current one on pythonweekly.com). Both are curated by editors, may not publish a submission, and may prefer an article or a notable release
over a new project. Do not follow up more than once. Do not submit before the project is on PyPI and the docs are live. A blog post (the anchor post) is usually an easier submission
than a repository link, so submit the anchor post URL first, and the repository only if the form invites projects. ⚠️ unverified.

Submit one item per newsletter and one at a time, after the Show HN and Reddit posts, when there is some traction and a few replies you can quote (see the checklist). Newsletters
are issued weekly, so a Monday to Wednesday submission is the usual way to catch the next issue. ⚠️ unverified.

## PyCoder's Weekly

Target: PyCoder's Weekly, <https://pycoders.com/> (⚠️ confirm the submission link).

**Item type:** article (the anchor post) or project (the repository), whichever the form offers.

**Title:** `TODO Notifier: give TODO comments owners and deadlines, and fail CI on expired ones`

**Link:** the anchor post URL (dev.to or Hashnode, once posted). For a project submission: https://github.com/ashu-tosh-kumar/todo_notifier

**Blurb (about 50 words):**

> TODO Notifier is an MIT-licensed Python CLI that finds TODO, FIXME, HACK and XXX comments, fills in the owner and age from git blame, and gives each one a due date. `scan . --fail-on expired` exits with 1 when a written deadline has passed. It comes with a GitHub Action, a pre-commit hook and Slack or Teams digests.

**One-line version (if the form has a short field):**

> A CLI that gives TODO comments owners and deadlines, and fails CI on overdue ones.

**Note to the editor (optional field):**

> I'm the author. The post explains the design choice I'm least sure about: undated TODOs get a default due date and are shown as "stale", but only TODOs with a written date can fail a build. I'm looking for feedback on that. The docs include a comparison with todo-to-issue-action, Todo Tree and Ruff's TD rules.

## Python Weekly

Target: Python Weekly, <https://www.pythonweekly.com/> (⚠️ confirm the submission link or email).

**Item type:** project / article.

**Title:** `TODO Notifier: a CLI for TODO deadlines, owners and CI checks`

**Link:** https://github.com/ashu-tosh-kumar/todo_notifier (or the anchor post, if the form wants articles).

**Blurb (about 40 words):**

> TODO Notifier finds TODO and FIXME comments, takes the owner and age from git blame, flags overdue ones, and can fail CI when a deadline has passed. Includes a GitHub Action, a pre-commit hook and weekly Slack or Teams digests. Open source (MIT), Python 3.10+, no config needed.

**Note to the editor (optional):**

> I'm the author. It is a new release (v2.1.0) of a small project. Feedback is welcome.

## Facts to double check against the release before sending

- The version is published on PyPI as `2.1.0` and `pipx install todonotifier` works from a clean machine.
- The minimum Python version is 3.10 (decision D1).
- The Action ref in the docs (`@v2.1.0`) exists as a tag. If the Action moved to its own repo, update the link in the post first.
- The links work: repository, docs home, `comparison/`, `quickstart/`.
