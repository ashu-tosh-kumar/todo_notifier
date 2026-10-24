# Show HN draft

Status: draft, maintainer to post. Post it only after `v2.1.0` is on PyPI, the docs are deployed and the demo works from a clean install.

⚠️ Unverified: I did not read the current [Show HN guidelines](https://news.ycombinator.com/showhn.html) or the HN rules from here. Read them before posting.
As I remember them: the project must be something people can run or try, no sign-up wall, do not ask for upvotes, and the first comment is where the
author explains. Check that this is still true.

## Title (77 characters)

```text
Show HN: TODO Notifier, a CLI that fails CI when a TODO's deadline has passed
```

The limit is 80 characters. Alternatives:

- `Show HN: TODO Notifier, deadlines and owners for TODO comments` (62)
- `Show HN: A CLI that fails CI when a TODO comment passes its deadline` (68)

URL to submit: `https://github.com/ashu-tosh-kumar/todo_notifier` (the repository, so that the README with the GIF is the first thing people see). The docs site
is `https://ashu-tosh-kumar.github.io/todo_notifier/`.

## First comment

Paste this as the first comment right after submitting. Edit freely: it should sound like you.

---

Hi HN, I'm the author. TODO Notifier is a Python command line tool (MIT) that finds `TODO`, `FIXME`, `HACK` and `XXX` comments, works out who owns each
one and how old it is, and can exit non-zero when one has expired.

**Why.** Every codebase I have worked on has TODO comments that nobody owns and nobody dates, so they never get done and nobody can tell which ones still
matter. I wanted something small that I could add to CI without a service or an account.

**How it works.**

- Syntax you already use, with optional extras: `# TODO {2026-12-31} @priya Remove the old tax table` or `# TODO(priya) {2026-12-31}: ...`. Both the owner and the date
  are optional.
- Missing owners come from `git blame` (one `git blame` call per file that contains a TODO). A missing date becomes a default due date: the day the line was
  added plus 90 days. 90 is a judgment call; it is configurable and 0 turns it off.
- Two words on purpose. *Overdue* means somebody wrote a `{date}` and it passed. *Stale* means only the default date passed. `--fail-on expired` fails on
  overdue only, so adopting the tool does not turn CI red because of comments from 2021. `--fail-on stale` and `--fail-on incomplete` are opt-in.
- Only comments count, not strings or docstrings, for 37 file extensions. It is a heuristic, not a parser.
- `scan --since BASE --format github` judges only the lines a pull request adds. A GitHub Action wraps that (annotations, a job summary, an optional
  sticky comment) and has a weekly digest mode for Slack, Teams or a webhook. There is also a pre-commit hook.
- Nothing leaves your machine unless you configure a notifier. Webhook URLs are read from environment variables, never from the config file.

`pipx install todonotifier && todonotifier scan .` is all it takes to try it. The docs have a 5-minute quickstart with real output.

**Limitations, so you do not have to find them.**

- It does not create issues. If you want that, [todo-to-issue-action](https://github.com/alstr/todo-to-issue-action) does it, and the two work together. There is
  no editor integration either ([Todo Tree](https://github.com/Gruntfuggly/todo-tree) does that). I wrote a comparison page and I tried to be fair; tell me if a row is wrong.
- Comment detection can miss or invent a TODO in unusual code (nested block comments, heredocs, a `<script>` block in HTML).
- Owners come from plain `git blame`, so a reformatting commit can make the person who ran the formatter the owner. In a shallow CI clone the owners are
  wrong; it warns, and the docs say to use `fetch-depth: 0`.
- The table output does not yet mark which due dates are defaults.
- I tested it on Linux only. The Microsoft Teams message follows the documented Workflows format but I have not verified it against a real tenant.
- It is a one-person side project, and the project is young: do not expect polish.

**Feedback I would like.**

1. Is the overdue/stale split the right default, or would you have chosen otherwise?
2. TODO syntaxes in your codebase that it misses (please paste the line).
3. Whether you would use the PR check, the weekly digest, or neither, and why.
4. Anything that made the first five minutes confusing.

Repo: https://github.com/ashu-tosh-kumar/todo_notifier. Docs: https://ashu-tosh-kumar.github.io/todo_notifier/. I'll be around to answer questions.

---

## Notes for the maintainer

- Best time: HN's front-page traffic is highest on weekday mornings US Eastern time (late afternoon in India). ⚠️ This is common advice, not something I measured. See
  `launch-week-checklist.md` for the suggested slot.
- Do not ask friends to upvote; HN detects voting rings and penalizes them. Share the link only as a normal link, if at all.
- Answer every comment, include the critical ones, calmly and in the thread. If someone points at a real bug, say so and open an issue; link it in the reply.
- If the post does not get traction, do not repost it the same week. HN allows a second attempt later, ⚠️ check the current rule on reposts.
