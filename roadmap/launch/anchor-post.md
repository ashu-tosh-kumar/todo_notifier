<!--
Maintainer notes (delete this comment before posting):
- Status: draft, maintainer to post. Post it only after v2.1.0 is on PyPI, the docs are deployed and the GitHub Action ref in the snippets exists.
- The terminal outputs were produced with todonotifier 2.1.0 (this branch) on a throwaway sample repo on 2026-10-24. The "days" in the DUE column depend on
  the day the command runs, so a reader will see different numbers. The post says so.
- dev.to: paste everything below the second "---" line of the front matter. dev.to allows at most 4 tags. Keep `published: false` until you have read it once in the preview.
- Hashnode: set the canonical URL in the post settings ("Are you republishing?"), and use the same body. Hashnode ignores the front matter.
- Upload assets/demo.gif to the post and replace the GIF placeholder below. In the dev.to editor, drag the file into the text.
- Length: about 1,360 words of prose, about 1,750 with the code blocks.
-->
---
title: "Your TODOs have no deadlines: here's how to fix that"
published: false
description: "TODO comments rot because they have no owner and no date. A small open source CLI that fills in both from git blame, flags the overdue ones, and fails CI when one expires."
tags: python, devops, opensource, productivity
canonical_url: https://ashu-tosh-kumar.github.io/todo_notifier/
cover_image:
---

Open any codebase that is a few years old and search for `TODO`. You will find a list that nobody owns.

```python
# TODO: handle the case where the cart is empty
# FIXME this retry loop hammers the gateway
# HACK skip validation for the Diwali sale
```

Who wrote each of those? When? Is the sale over? Is the retry loop still hammering the gateway? A `TODO` comment is a promise to your future self, and
it has no due date, no owner and no reminder. So it is quietly broken the day you write it.

I have a few of these in my own projects, and I got tired of grepping for them. So I built a small tool, [TODO Notifier](https://ashu-tosh-kumar.github.io/todo_notifier/),
that does three things: it finds the TODOs, it works out who owns each one and how old it is, and it can fail your CI when one has expired. It is
open source (MIT), it is a Python command line tool, and it needs no configuration to start. This post shows how it works, what it does not do, and how
to try it in five minutes.

## Give a TODO a deadline and an owner

The syntax is the one you already use, with two optional extras:

```python
# TODO {2026-08-31} @priya Remove the old tax table after the GST migration
# TODO(rahul) {2027-03-31}: Cache the lookup
# FIXME this retry loop hammers the gateway
```

- `{YYYY-MM-DD}` is the due date.
- `@priya` or `TODO(priya):` (the Google style) is the owner.
- The tags are `TODO`, `FIXME`, `HACK` and `XXX` by default, and you can change that.
- Everything is optional. A bare `# FIXME this retry loop hammers the gateway` is still found.

Nobody is going to annotate hundreds of old comments by hand, so the tool fills the gaps. That is the part that made it useful for me.

## Git blame fills in the rest

If a TODO has no `@owner`, the tool asks `git blame` who wrote that line, and when. If it has no `{date}`, it gives the TODO a **default due date**:
the day the line was added plus 90 days. (90 is a judgment call, not a benchmark. You can change it, or set it to 0 to turn default dates off.)

Here is a tiny sample project, a shop with four TODOs, scanned the day I wrote this (24 October 2026):

```bash
pipx install todonotifier
todonotifier scan .
```

```text
LOCATION            TAG    OWNER  DUE                     MESSAGE
shop/billing.py:2   TODO   priya  2026-08-31 overdue 54d  Remove the old tax table after the GST migration
shop/payments.py:1  FIXME  priya  2026-05-11 stale 166d   this retry loop hammers the gateway
shop/search.py:2    TODO   rahul  2027-03-31 due in 158d  Cache the lookup
shop/search.py:5    HACK   rahul  2026-12-19 due in 56d   skip validation for the Diwali sale

4 TODOs · 1 overdue · 1 stale · 0 unowned
```

Nobody wrote `@priya` on the FIXME; it comes from `git blame`. Nobody wrote a date on it either; the 2026-05-11 is the day the line was added (10 February,
plus 90 days). Your numbers will differ from mine, because the days are counted from the day you run it.

The scan only reads comments, not strings. `print("TODO list")` is not a TODO, and neither is a tag inside a docstring. That detection works for 37 file
extensions (the command line scans a preset of the common ones by default). It is a heuristic, not a parser, and the docs list where it can be wrong.

## Stale is not the same as overdue

This is the design decision I thought hardest about, so I will explain it.

If every undated TODO got a default due date, and every expired date failed the build, then the day a team adopted the tool, CI would go red because of
comments written in 2021. That is the worst first impression a tool can make, and people would remove it that afternoon.

So the tool uses two words:

- **overdue**: somebody wrote a `{date}` and it has passed. That is a promise that was broken.
- **stale**: nobody wrote a date, and the default one (added + 90 days) has passed. That is a nudge, not a promise.

`--fail-on expired` fails only on **overdue** TODOs. Stale ones are shown but never fail anything, unless you opt in with `--fail-on stale`. (Without
`--fail-on` the command only reports and exits 0.)

```bash
todonotifier scan . --fail-on expired; echo "exit code: $?"
```

```text
LOCATION            TAG    OWNER  DUE                     MESSAGE
shop/billing.py:2   TODO   priya  2026-08-31 overdue 54d  Remove the old tax table after the GST migration
shop/payments.py:1  FIXME  priya  2026-05-11 stale 166d   this retry loop hammers the gateway
shop/search.py:2    TODO   rahul  2027-03-31 due in 158d  Cache the lookup
shop/search.py:5    HACK   rahul  2026-12-19 due in 56d   skip validation for the Diwali sale

4 TODOs · 1 overdue · 1 stale · 0 unowned
todonotifier: --fail-on expired: 1 overdue TODO (an explicit date has passed)
exit code: 1
```

The exit code is 1, so any CI system can stop on it. There is also `--fail-on stale` (explicit or default dates) and `--fail-on incomplete` (every TODO
must have an owner and a date written in the comment). Pick the strictness your team can live with.

## In pull requests: only the lines you changed

Failing on every old TODO in the repository would block unrelated pull requests. So in pull requests you want to judge only the TODOs a change *adds*.
That is what `--since` does: it keeps the TODOs on lines added or changed since a ref. This is what a pull request that adds an expired TODO produces on
my sample project:

```bash
todonotifier scan . --since main --format github --fail-on expired
```

```text
::error file=shop/payments.py,line=6,title=TODO overdue by 53d::Delete this shim (@asha, due 2026-09-01)
1 TODO: 1 overdue, 0 stale, 0 unowned
todonotifier: --fail-on expired: 1 overdue TODO (an explicit date has passed)
```

The `::error file=...` line is GitHub's annotation format, so on GitHub the TODO shows as a red mark on the "Files changed" tab. You do not need to run
that by hand. The GitHub Action does it:

```yaml
name: TODOs
on:
  pull_request:
permissions:
  contents: read
jobs:
  todos:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0          # git blame and the changed lines need the full history
          persist-credentials: false
      - uses: ashu-tosh-kumar/todo_notifier/integrations/github-action@v2.1.0
        with:
          mode: pr
          fail-on: expired
```

The action adds annotations on the changed lines, a table in the job summary, and, if you turn it on, one comment on the pull request that is updated
on every push. The `fetch-depth: 0` line matters: in a shallow clone, `git blame` attributes everything to the latest commit and the owners are wrong.
The tool warns when it sees one.

## A weekly digest, so someone sees the list

Failing a build helps with new TODOs. The old ones need a reminder. The same action has a `digest` mode that scans the whole repository on a schedule
and posts the result to Slack, Microsoft Teams or a webhook (the command line can also send it by email):

```yaml
on:
  schedule:
    - cron: "0 8 * * 1"      # Mondays at 08:00 UTC
jobs:
  digest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: ashu-tosh-kumar/todo_notifier/integrations/github-action@v2.1.0
        with:
          mode: digest
          slack-webhook: ${{ secrets.SLACK_WEBHOOK_URL }}
```

The digest lists the overdue, stale and due-this-week TODOs, grouped by owner, with links to the lines when it knows the repository URL. A webhook URL is a secret: it goes in a
repository secret, never in the config file. (I have not been able to verify the Microsoft Teams message against a live tenant, so treat that one as
experimental.)

You can also stop a commit on a developer's machine with the [pre-commit](https://pre-commit.com) hook, which scans only the staged files and judges
only explicit dates.

## How it compares

It is not the only tool that touches TODO comments, and it does not replace the others:

- [todo-to-issue-action](https://github.com/alstr/todo-to-issue-action) turns TODOs into GitHub issues. If you want your TODOs in an issue tracker, use
  that. TODO Notifier does not create issues.
- [Todo Tree](https://github.com/Gruntfuggly/todo-tree) shows TODOs in the VS Code sidebar. TODO Notifier has no editor integration.
- Ruff's `TD` rules lint the *format* of TODO comments (author, issue link) in Python. They do not track dates.

TODO Notifier's job is narrower: deadlines, owners, reminders and a CI gate. The [comparison page](https://ashu-tosh-kumar.github.io/todo_notifier/comparison/)
has a table with the sources I checked. If I got a row wrong, please [open an issue](https://github.com/ashu-tosh-kumar/todo_notifier/issues/new/choose)
and I will fix it.

## Honest limitations

- Comment detection is a heuristic. Nested block comments, heredocs and a `<script>` block in HTML can cause a missed or a spurious TODO.
- The table output does not yet mark which due dates are defaults: a not-yet-due default date looks like a written one. (The `json` and `github`
  formats say which is which.)
- Owners come from `git blame`, so a reformatting commit can make the person who ran the formatter the "owner" (it runs plain `git blame`, with no ignore-revisions
  support). An `[authors]` table maps git emails to the names you want to see, but it does not fix this.
- I only tested it on Linux. It is plain Python and git, so macOS should work; Windows I do not know. ⚠️
- It is a one-person project. Expect it to be useful and not polished.

## Try it in five minutes

```bash
pipx install todonotifier        # or: pip install todonotifier
cd your-project
todonotifier scan .              # see every TODO with its owner and due date
todonotifier init                # optional: writes a starter config, every option commented out
```

Then:

1. Add the workflow above to `.github/workflows/todos.yml` to check pull requests.
2. Or add the pre-commit hook (`repo: https://github.com/ashu-tosh-kumar/todo_notifier`, `id: todonotifier`).
3. Start with `fail-on: expired` (the action's default is `none`, which only reports). Move to `stale` only when your team is ready.

The [Quickstart](https://ashu-tosh-kumar.github.io/todo_notifier/quickstart/) walks through all of it with real output. Nothing leaves your machine
unless you configure a notifier.

## What I would like to hear

Is the stale/overdue split the right call, or would you want something else as the default? Which TODO syntax in your codebase does it miss? Would you use
the digest, or is the PR check enough? Comments here or [issues on GitHub](https://github.com/ashu-tosh-kumar/todo_notifier/issues) are both welcome.

The repository is at [github.com/ashu-tosh-kumar/todo_notifier](https://github.com/ashu-tosh-kumar/todo_notifier). If it saves you a forgotten FIXME, a star
helps others find it.

---

## Medium cross-post note (not part of the post)

- Publish on Medium only after the dev.to or Hashnode post is live. Use Medium's **Import a story** (Medium profile menu -> Stories -> Import a story) with the
  dev.to URL: it copies the text and sets the canonical link to the original automatically. ⚠️ I did not verify that Medium's importer is still available
  in your account; if it is not, paste the post and, in the story's **Advanced settings**, set the **canonical link** by hand.
- The canonical link should point at the page the maintainer wants to rank. The brief says the docs site: `https://ashu-tosh-kumar.github.io/todo_notifier/`.
  A docs home page is not a copy of the article, so search engines may ignore a canonical link that points at a different page. If that matters to you,
  add the post to the docs site as a page (for example `site_src/blog/todos-have-no-deadlines.md`) and point `canonical_url` at it. That is optional and was
  left out to keep things simple.
- Medium does not render code blocks with a language or tables well. Paste the terminal outputs as code blocks (the ``` button) or as GitHub Gists, and
  replace any table with a list.
- Medium has no tags beyond 5. Suggested: Python, DevOps, Open Source, Software Development, Git.
- Add the line "Originally published at <canonical URL>" at the top.
- Do not post to Medium publications that require an exclusive story unless you want to lose the canonical link. ⚠️ unverified.
