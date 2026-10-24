# Launch week checklist

Status: draft, maintainer to follow. Nothing here has been done: no post was made, no label was created, nothing was published.

Day 1 is the first day you post. The suggested weekdays assume Day 1 is a Tuesday; shift them as needed, but keep the order. All times are suggestions; the HN and Reddit
"best time" advice is common advice and ⚠️ not something I measured. Times are given in UTC with the IST equivalent (IST = UTC + 5:30).

## Before Day 1: pre-launch checks

Do not post until every box that is marked "must" is checked. Posting a link to something that does not install is worse than waiting a week.

### Must

- [ ] **`v2.1.0` is on PyPI.** Follow [RELEASING.md](../../RELEASING.md). Then, on a clean machine or a fresh virtualenv: `pipx install todonotifier`, `todonotifier --version` prints
  `todonotifier 2.1.0`, and `todonotifier scan .` works on a real repository.
- [ ] **The tag `v2.1.0` exists on GitHub**, so `rev: v2.1.0` (pre-commit) and `@v2.1.0` (the Action) in the docs and posts resolve. Test both in a scratch repository: a workflow
  with `mode: pr` and a `.pre-commit-config.yaml` with the hook.
- [ ] **The GitHub Action is usable.** Today it lives in `integrations/github-action/` of this repository (decision A3), and the posts use that path. If you have moved it to its own
  repository (decision D2: `todonotifier-action`) and published it on the Marketplace, update the `uses:` line in the posts, the docs (`site_src/ci.md`, `site_src/quickstart.md`) and
  `curated-lists.md` first, and set the "Action Marketplace usage" row of `roadmap/metrics.md`.
- [ ] **The docs are deployed.** <https://ashu-tosh-kumar.github.io/todo_notifier/> loads, the Quickstart and the comparison page open, and no page still says "coming soon". Check
  the GitHub Pages setting (Settings -> Pages -> Source: GitHub Actions) and the latest `docs` workflow run on the default branch.
- [ ] **The README renders on GitHub and on PyPI**, including the GIF. On PyPI a relative image path does not render: see the comment next to the GIF in `README.md` and point it at the
  raw GitHub URL once the files are on the default branch.
- [ ] **Metrics are recorded.** The baseline in [`roadmap/metrics.md`](../metrics.md) is from 2026-10-24. If more than a week has passed, redo it, and fill in the two manual rows:
  Used-by dependents, and Insights -> Traffic (GitHub keeps only 14 days, so a late reading loses data).
- [ ] **The posts are proof-read** and every command in them still works. The terminal outputs in the drafts were made on 2026-10-24 from a sample project; the days in the DUE column
  differ when you run it. Re-run the sample commands if you want the post to match the current date.
- [ ] **GitHub issue labels exist** (see "Labels" below) and Discussions is enabled (the issue templates link to it).
- [ ] **You have a free 2 hours after each post** to answer comments, and the following day too.

### Soft dependency (2.1, the landing page and waitlist)

- [ ] ⚠️ If the landing page and waitlist (2.1) are live, you may link them from the profile or the end of the anchor post. They are not live as of 2026-10-24, so **the drafts do not
  mention a waitlist or a hosted version**. Do not add one to the posts unless it exists and works, and keep it a single line at the end, so the posts stay about the open source tool.
  Record the signups in `roadmap/metrics.md` once there is a form.

### Nice to have

- [ ] Replace the Slack and Teams screenshot placeholders in `site_src/notifications.md` (the maintainer step from 1.3).
- [ ] Create the `good first issue` issues from [`roadmap/good-first-issues.md`](../good-first-issues.md) so visitors who want to contribute find something. Do this **before** the r/developersIndia post, which mentions them.
- [ ] Turn on GitHub Discussions and pin one welcome thread. ⚠️ Optional.
- [ ] Set the repository's About text, topics and social preview (1.4 listed these as maintainer settings).

## Posting plan

One channel per day, not all at once: each one needs your attention for the replies. The anchor post comes first, because every other post can link to it.

| Day | Weekday | What | File | When (UTC / IST) | Notes |
|---|---|---|---|---|---|
| 1 | Tue | Anchor post on dev.to or Hashnode (canonical link to the docs), then the LinkedIn post and the X/Bluesky thread | [anchor-post.md](anchor-post.md), [social.md](social.md) | 04:00 to 06:00 / 09:30 to 11:30 (morning in India) | Publish the post first, then the social posts that link to it. Read the post once in the platform's preview. |
| 2 | Wed | Show HN | [show-hn.md](show-hn.md) | about 13:00 to 15:00 / 18:30 to 20:30 ⚠️ | HN is read mostly by a US audience, so the US morning is the usual slot. Stay online for at least 3 hours. |
| 3 | Thu | r/Python (showcase) | [reddit.md](reddit.md) | about 13:00 to 15:00 / 18:30 to 20:30 ⚠️ | Use the showcase thread or flair that the rules require. |
| 4 | Fri | r/developersIndia | [reddit.md](reddit.md) | about 05:00 to 07:00 / 10:30 to 12:30 ⚠️ | The audience is in India: a morning in IST. |
| 5 | Sat | Quiet day: reply to everything, triage the issues, start the visible fix | | | Weekends are quiet on r/devops and in newsletters; use them to work. |
| 8 | Tue (week 2) | r/devops, if the first posts brought useful feedback to quote | [reddit.md](reddit.md) | about 13:00 to 15:00 / 18:30 to 20:30 ⚠️ | Optional: skip it if r/devops rules forbid it. |
| 8 to 9 | week 2 | Newsletter submissions | [newsletters.md](newsletters.md) | any time | Confirm the process first. |
| 28+ | week 4 or later | Curated lists, only if the traction bar in the file is met | [curated-lists.md](curated-lists.md) | any time | Decide from the week 4 numbers. |

Order rules:

- If a major bug shows up on Day 1 or 2, **pause the next post**, fix it, release, and tell the people who reported it. A day's delay costs nothing.
- Do not post the same text twice. Do not cross-link a post to "my other post on r/..." in a way that looks like asking for votes.
- Do not post to a subreddit whose rules you have not read today (see the ⚠️ checklists in [reddit.md](reddit.md)).

## Reply routine: every comment within 24 hours

For the whole of launch week (and the week after):

1. **Twice a day** (for example after breakfast and before dinner IST), open: GitHub notifications, the issues list, Discussions, dev.to / Hashnode comments, the HN thread, the Reddit
   inboxes and threads, LinkedIn and X/Bluesky mentions. Keep a list of the links in a scratch note so you do not forget one.
2. **Reply to everything within 24 hours**, including "nice" and negative comments. Say thank you once, and answer the question. If it is a bug: say "thanks, that is a bug, I opened
   #123", and link the issue. If it is a feature idea: say so and ask a question about their use case. If it is a mistake in the comparison page: fix it the same day and say so.
3. **Never argue.** If a criticism is fair, agree and say what you will change. If it is not, give one short factual answer, once.
4. **Turn feedback into issues.** For each distinct piece of feedback, create (or add a comment to) a GitHub issue, apply the labels below, and link the source (post or comment).
   Do it the same day, while you remember the context. One issue per problem, with a reproduction when it is a bug.
5. **Record the numbers** every Monday in [`roadmap/metrics.md`](../metrics.md).
6. At the end of the week, write 5 lines in `roadmap/PROGRESS.md` or an issue: what worked (the channel that brought installs and issues), what did not, the top three requests.

### Labels to create

Create these in Issues -> Labels (the maintainer does this; labels were not created from here):

| Label | Colour (suggestion) | Meaning |
|---|---|---|
| `feedback` | `#0e8a16` | Anything that came from a user reacting to the launch: ideas, confusion, a missing syntax. Apply to every issue that came from a comment, in addition to `bug` or `enhancement`. |
| `launch` | `#1d76db` | The work and tracking of the launch itself (the visible fix, the posts, the listings). Also use it on bugs found in the first two weeks, so you can count them. |

Existing labels used with them: `bug`, `enhancement`, `documentation`, `good first issue` (see CONTRIBUTING.md). ⚠️ I did not list the repository's current labels (no authenticated
access from here); check which already exist.

## Ship one visible fix during launch week

The point: show that a report gets a response. Pick a fix that is **small, visible to a user and finished in a day**, release it as `v2.1.1`, and mention it in the thread where the
feedback came from.

**Recommended candidate: good first issue 3, "Mark default due dates in the `DUE` column of the table output"**
([`roadmap/good-first-issues.md`](../good-first-issues.md), section 3).

Why this one:

- It is a limitation the posts already admit ("the table does not yet mark which due dates are defaults"), so somebody is likely to mention it, and fixing it is a visible answer.
- It changes the thing users see first (the table), and has clear acceptance criteria and a small diff (`describe_due` in `todonotifier/formatters.py`, snapshots, README example).
- It does not change the other formats, the exit codes or the public Python API.

Caveats: the quickstart, README and docs show the table output, and the snapshots and the README example must be updated in the same change. The numbers in the posts will then
differ from the new output; the posts are already published by then, so that is fine, but update the docs.

**Fallbacks**, if real feedback points elsewhere (always prefer the problem a real user reported over this list):

- Issue 4, "Handle Ctrl-C without a Python traceback" (a bug, easy to explain in a reply).
- Issue 8, "Document the directories that are skipped by default" (a documentation fix, extra small, good if the first-run confusion was about what gets scanned).
- A syntax a commenter says it misses: add the language or the comment syntax with a fixture (see issues 1 and 2 for the pattern).

**Plan:**

1. Day 1 to 3: collect feedback; decide by the end of Day 4 which fix to ship (the one most people mention, otherwise the candidate above).
2. Day 5 to 6: implement it on a branch with tests and 100% coverage, update the README changelog under `### v2.1.1`, and run the pre-push checks (`pytest`, `black --check`, `isort --check-only`, `flake8`, coverage).
3. Day 6 to 7: release `v2.1.1` following [RELEASING.md](../../RELEASING.md) (⚠️ a patch release changes the version, the tag, and the `@v2.1.0` refs in the docs; decide whether to
   bump them or keep the minor tag).
4. Reply in each thread where the problem was raised: "Fixed in 2.1.1: <link to the changelog or commit>. Thanks for reporting it."
5. If a contributor volunteers for a good first issue, let them have it and ship a different fix yourself. A first external pull request is worth more than the speed.
