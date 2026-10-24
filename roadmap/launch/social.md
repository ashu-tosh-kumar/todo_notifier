# Social drafts

Status: draft, maintainer to post. Post only after `v2.1.0` is on PyPI and the docs are live. Order and timing are in `launch-week-checklist.md`.

The GIF is `assets/demo.gif` in the repository. It shows `scan`, `scan --fail-on expired` with its exit code 1, and `scan --format github`. Attach the file
to the first post (X and Bluesky both accept GIFs; ⚠️ check the current size limit, because the file is about 250 KB, which should be fine). On LinkedIn, upload it as an image/GIF
to the post. If a platform rejects it, link to the README instead.

## LinkedIn post

1500 characters (⚠️ LinkedIn's limit is about 3,000 characters for a post; check in the editor). Attach the GIF. LinkedIn does not render the code lines, so they are plain text.

```text
Every codebase I have worked on has TODO comments that nobody owns and nobody dates.

# TODO: handle the empty cart
# HACK skip validation for the Diwali sale

Who wrote them? When? Is the sale over? A TODO is a promise to your future self, with no deadline and no reminder.

So I built TODO Notifier, a small open source Python command line tool (MIT):

- It finds TODO, FIXME, HACK and XXX comments.
- It works out the owner from @user, TODO(user) or git blame, and gives undated TODOs a default due date (90 days after the line was added).
- It separates "overdue" (someone wrote a {date} and it passed) from "stale" (only the default date passed), so adopting it does not turn your CI red because of comments from 2021.
- `todonotifier scan . --fail-on expired` exits with 1 when an overdue TODO exists. A GitHub Action checks only the lines a pull request adds, and a weekly digest can go to Slack or Teams.

Try it: pipx install todonotifier, then todonotifier scan .

It is a one-person side project and young. It does not create issues, it has no editor integration, and its comment detection is a heuristic. The docs have an honest comparison with the other tools in this space.

What I would like to know: how does your team keep TODOs from rotting? And which TODO styles in your codebase would it miss?

Docs and a 5-minute quickstart: https://ashu-tosh-kumar.github.io/todo_notifier/
Code: https://github.com/ashu-tosh-kumar/todo_notifier

#Python #DevOps #OpenSource #SoftwareEngineering
```

Notes:

- The first two lines show before "see more", so the hook is in them.
- LinkedIn lowers the reach of posts with links in the body (⚠️ commonly reported, not verified). If you want to test it, delete the two link lines and put them in the first comment instead.
- Reply to every comment within 24 hours. Tag nobody you do not know.

## X / Bluesky thread

Six posts. Each is at most 280 characters including the full URL text, so the same text fits X (280; X counts every link as 23 characters, so there is room) and Bluesky (300).
The count after each post is its length in characters, as counted by Python `len`, which can differ for emoji, and there are none. Attach `assets/demo.gif` to post 1 and delete the
bracketed `[GIF ...]` marker from the text first (the counts include it, so the real post is shorter).

**1/6** (259 characters)

```text
Your TODO comments have no owner and no deadline, so they rot.

I built TODO Notifier: a Python CLI that finds them, works out who owns each one and how old it is, and fails CI when a deadline has passed.

Open source, no config needed. [GIF: assets/demo.gif]
```

**2/6** (204 characters)

```text
Write TODOs the way you already do. Add a date or an owner when you want a deadline:

# TODO(priya) {2026-08-31}: remove the old tax table

Owner and date are optional. Missing owners come from git blame.
```

**3/6** (253 characters)

```text
Undated TODOs get a default due date: the day git blame says the line was added, plus 90 days. They show as "stale".

A TODO with a written {date} that has passed is "overdue". Only overdue ones fail `--fail-on expired`, so day one does not turn CI red.
```

**4/6** (239 characters)

```text
In pull requests it checks only the lines the PR adds, so old TODOs never block unrelated changes.

The GitHub Action adds annotations on the changed lines and a job summary. There is also a pre-commit hook and a weekly Slack/Teams digest.
```

**5/6** (265 characters)

```text
Honest limits: it does not create issues (todo-to-issue-action does) and has no editor view (Todo Tree does). Comment detection is a heuristic, not a parser. Only tested on Linux.

Comparison with sources: https://ashu-tosh-kumar.github.io/todo_notifier/comparison/
```

**6/6** (255 characters)

```text
Try it in 5 minutes:

pipx install todonotifier
todonotifier scan .

Docs: https://ashu-tosh-kumar.github.io/todo_notifier/
Code (MIT): https://github.com/ashu-tosh-kumar/todo_notifier

Which TODO style does it miss in your codebase? I would like to know.
```

Notes:

- No hashtags are used, on purpose. Add `#Python` to post 1 if you like; check the count after.
- Bluesky: ⚠️ the 300 limit is counted in graphemes, and links in the text count in full unless the client turns them into a link card. These posts are under 280 either way.
- Do not tag people or the tools in the comparison (todo-to-issue-action, Todo Tree, Ruff) to ask for a share. If one of them replies, answer politely.
- A one-line post for later days (no thread): "Week 1 of TODO Notifier: <what you shipped from the feedback>. Thanks to everyone who tried it and told me what broke."
