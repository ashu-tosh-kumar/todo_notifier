# Reddit drafts

Status: draft, maintainer to post. Post only after `v2.1.0` is on PyPI and the docs are live.

**I did not fetch Reddit or read any subreddit's rules.** Everything under "Rules to check before posting" is from general knowledge and is ⚠️ unverified. Rules
change often and differ by subreddit. Read the sidebar, the wiki and the pinned posts of each subreddit the day you post, and follow them over anything written here.

General advice for all three:

- Each post is written for its audience. Do not paste the same text into all of them, and do not post all three on the same day.
- Reddit is hostile to promotion from accounts that only post their own project. ⚠️ Many subreddits expect a ratio such as "mostly contribute, rarely promote" (the old
  "9:1" guideline is often quoted). Check your own history, and comment helpfully in the subreddit for a few weeks before you post, if you have not already.
- Do not ask for upvotes, do not use multiple accounts, do not link-spam.
- Reply to every comment, including the critical ones. The `launch-week-checklist.md` has the routine.
- Attach the GIF (`assets/demo.gif`) as an image or link to the repo, depending on what the subreddit allows.

---

## 1. r/Python

Target: <https://www.reddit.com/r/Python/>

### Rules to check before posting

- ⚠️ Is there a designated place for project showcases? r/Python has historically used a weekly or periodic showcase/"what are you working on" thread, and/or a
  "Showcase" post flair. Find out which applies today, and use it. Do not post as a normal discussion post if that is not allowed.
- ⚠️ Is a "Showcase" flair required, and does it need a particular structure? I recall that showcase posts are asked to say **what the project does**, **its target
  audience** and **how it compares to alternatives**. The draft below has those three headings so you can adapt it. Verify.
- ⚠️ Self-promotion limits: is there a rule on how often you may post your own project, on the share of your activity that may be self-promotion, or on posting the same
  project twice?
- ⚠️ Does the subreddit require the project to be open source, on PyPI, or to have a minimum of documentation? (This project is MIT licensed, is on PyPI once `v2.1.0` is published, and has a docs site.)
- ⚠️ Are AI-generated posts or code restricted or must they be disclosed? This tool's code and docs were written with an AI assistant's help, under the maintainer's review. If a rule
  asks for disclosure, disclose it. Do not hide it.
- ⚠️ Are links to a blog allowed in the body, or must it be a text post only?
- ⚠️ Is there a rule about titles (no clickbait, no all caps)?

### Draft (Showcase)

**Flair:** Showcase (⚠️ confirm the name)

**Title:** `TODO Notifier: a CLI that gives TODO comments owners and deadlines, and fails CI on expired ones`

**Body:**

**What My Project Does**

`todonotifier` finds `TODO`, `FIXME`, `HACK` and `XXX` comments in your repository, works out the owner (from `@user`, `TODO(user)` or `git blame`) and a due date, and
reports them in the terminal, as GitHub annotations, JSON or SARIF, or as a Slack, Teams, webhook or email digest. `todonotifier scan . --fail-on expired` exits with 1 when a
TODO's `{date}` has passed, so you can put it in CI. There is a GitHub Action and a pre-commit hook.

```text
$ todonotifier scan .
LOCATION            TAG    OWNER  DUE                     MESSAGE
shop/billing.py:2   TODO   priya  2026-08-31 overdue 54d  Remove the old tax table after the GST migration
shop/payments.py:1  FIXME  priya  2026-05-11 stale 166d   this retry loop hammers the gateway
shop/search.py:2    TODO   rahul  2027-03-31 due in 158d  Cache the lookup
shop/search.py:5    HACK   rahul  2026-12-19 due in 56d   skip validation for the Diwali sale

4 TODOs · 1 overdue · 1 stale · 0 unowned
```

An undated TODO gets a default due date 90 days after `git blame` says it was added, and is then called *stale*. A TODO with a written `{date}` that has passed is *overdue*.
Only overdue ones fail `--fail-on expired`, so adopting it does not break CI on old comments.

**Target Audience**

Teams (or solo maintainers) with a codebase of any size who want TODOs to have a deadline, and are happy with a CLI plus CI. Early stage: it works, it has 100% line coverage and
CI on Python 3.10 to 3.14, but it is young and has few users.

**Comparison**

todo-to-issue-action turns TODOs into issues, Todo Tree shows them in VS Code, and Ruff's `TD` rules lint their format. This one tracks deadlines and owners and gates CI. It does not
create issues and has no editor integration. There is a [comparison page](https://ashu-tosh-kumar.github.io/todo_notifier/comparison/) with sources.

`pipx install todonotifier`. Repo: https://github.com/ashu-tosh-kumar/todo_notifier. Docs: https://ashu-tosh-kumar.github.io/todo_notifier/.

Limitations: comment detection is a heuristic (not a parser), only Linux was tested, and owners come from plain `git blame`. I would like to hear which TODO syntaxes it misses.

---

## 2. r/devops

Target: <https://www.reddit.com/r/devops/>

### Rules to check before posting

- ⚠️ r/devops has historically been strict about self-promotion and low-effort tool links. Check whether promotion is allowed at all, allowed only in a weekly thread (for
  example a recurring "tools" or "self-promotion" thread), or only with a flair.
- ⚠️ Does it require a certain amount of text with the link, or ban posts whose main purpose is to link to your own blog or repo?
- ⚠️ Is there a minimum account age or karma?
- ⚠️ Is there a rule against posts about your own product that is a "service" (this one is a free CLI, and the SaaS is not built, so there is nothing to disclose; but do not mention the
  roadmap or any waitlist in this post unless the landing page is live and the rules allow it)?
- ⚠️ Are AI-assisted posts or projects restricted or must they be disclosed? Disclose if asked.
- ⚠️ What flair fits (for example "Tools", "Discussion")?

### Draft

**Title:** `How do you stop TODO comments from rotting? I made CI fail on expired ones (open source)`

**Body:**

Question first: how do your teams deal with `TODO`/`FIXME` comments in a codebase? In ours they pile up with no owner and no date, and a review comment saying "please
remove this TODO" is not a process.

What I ended up with, in case it helps, and I would like to hear what you do instead:

1. Give each TODO an optional deadline and owner in the comment: `# TODO(priya) {2026-08-31}: remove the old tax table`.
2. A CI step that looks only at the lines a PR adds and fails when one has an expired date:

   ```yaml
   - uses: actions/checkout@v4
     with:
       fetch-depth: 0
       persist-credentials: false
   - uses: ashu-tosh-kumar/todo_notifier/integrations/github-action@v2.1.0
     with:
       mode: pr
       fail-on: expired
   ```

3. A weekly job that posts the overdue and stale TODOs, grouped by owner, to Slack or Teams.

Undated TODOs are given a default due date (added per `git blame` plus 90 days) and are shown as "stale". They do not fail the build unless you opt in, because failing on
years-old comments the day you adopt the tool is a good way to get it removed.

The tool is `todonotifier`, a Python CLI (MIT). It works in any CI that can run Python and git: the exit code is the gate (`--fail-on expired` exits with 1), and there is a JSON and a
SARIF output. The GitHub Action is the only CI integration that is packaged. For GitLab the docs show a plain `script:` step. The one trap is shallow clones: `git blame` needs the
full history, and the tool warns when it does not have it.

Repo: https://github.com/ashu-tosh-kumar/todo_notifier (docs: https://ashu-tosh-kumar.github.io/todo_notifier/). What I do not know: whether a TODO deadline is the right thing to
gate on at all, or whether you would rather create tickets (there are tools for that too, and I link them in the comparison page). Tell me what you do.

---

## 3. r/developersIndia

Target: <https://www.reddit.com/r/developersIndia/>

### Rules to check before posting

- ⚠️ r/developersIndia has historically had a flair system and rules about "Showcase" or "Resource" type posts. Check which flair is meant for sharing your own open source project, and
  whether one is required.
- ⚠️ Is there a weekly or monthly thread for self-promotion or projects, and is promotion outside it removed?
- ⚠️ Does it ban posts that only link to a repo, or need a text explanation (the draft has one)?
- ⚠️ Is there a minimum account age or karma, or a ban on new accounts posting links?
- ⚠️ Does it restrict referral links, hiring or "please star my repo" posts? The draft does not ask for stars. Keep it that way.
- ⚠️ AI-assisted work disclosure rules.
- The audience is mostly Indian developers, many at services companies, product companies and startups, and students. The tone that works is usually direct, specific and
  modest. The draft uses an e-commerce example with GST and a festive-sale hack (invented for the sample project, not from a real codebase). Keep or drop it as you like.

### Draft

**Title:** `I built an open source CLI that gives TODO comments owners and deadlines, and fails CI on expired ones`

**Body:**

I am a developer from India, and I kept running into the same thing at work and in my side projects: `TODO` comments with no owner and no date, still there years later.
The classic is `# TODO remove after GST migration`, and nobody remembers if the migration is done. Or `# HACK skip validation for the Diwali sale` that is still in production in March.

So I built `todonotifier`, a free, open source (MIT) Python command line tool:

- It finds `TODO`, `FIXME`, `HACK` and `XXX` comments.
- It finds the owner from `@priya`, `TODO(priya)` or `git blame`, and gives undated TODOs a default due date (90 days after the line was added).
- `todonotifier scan . --fail-on expired` exits with 1 when a TODO with a written `{date}` has passed, so you can fail a pull request. There is a GitHub Action (PR annotations, weekly
  Slack/Teams digest) and a pre-commit hook.

```text
LOCATION            TAG    OWNER  DUE                     MESSAGE
shop/billing.py:2   TODO   priya  2026-08-31 overdue 54d  Remove the old tax table after the GST migration
shop/payments.py:1  FIXME  priya  2026-05-11 stale 166d   this retry loop hammers the gateway
```

Install: `pipx install todonotifier`. Everything runs locally; nothing is sent anywhere unless you set up a Slack/Teams/email notifier.

It is a side project by one person, so it is early and rough in places (comment detection is a heuristic, only tested on Linux). I am looking for honest feedback, mainly:
which TODO styles in your codebase it misses, and whether a deadline on a TODO is something your team would actually use. Also happy to take small contributions: there are
labelled `good first issue`s for people who want a first open source PR. (Only keep this sentence once the maintainer has created those issues from
`roadmap/good-first-issues.md`.)

Repo: https://github.com/ashu-tosh-kumar/todo_notifier. Docs and a 5-minute quickstart: https://ashu-tosh-kumar.github.io/todo_notifier/.

Skipped on purpose: r/MachineLearning and r/learnpython (off-topic for this tool, per the roadmap).
