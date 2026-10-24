# Interview synthesis (template)

Copy this file to `roadmap/interviews/synthesis.md` when you have at least 10 interviews, fill it in and link it from `roadmap/decision-saas.md`
(workstream 2.3). Anonymise everything: aliases (`INT-NNN`) only, no names, employers or repository names.

The `product-management:synthesize-research` skill can help to group the notes into themes. Review its output by hand, and check every quote
against the notes.

⚠️ Rules of thumb (not sourced benchmarks): with 10 to 15 interviews, a theme heard from 3 or more people is worth noting and one heard once is an
anecdote. Counts show direction only; they are not statistics. Report the interviews that go against your hopes first.

## 1. Programme summary

| | |
|---|---|
| Period | YYYY-MM-DD to YYYY-MM-DD |
| Interviews completed | N (target 10 to 15) |
| Roles | N EMs, N tech leads, N staff engineers, N other |
| Regions | N India, N other (see the tally) |
| Company sizes | N with 10-49 developers, N with 50-200, N outside the profile |
| Sources | N waitlist, N launch commenters, N LinkedIn, N communities, N referrals |
| Outreach | N contacted, N replied, N interviewed (reply rate N%) |
| Bias to watch | Who was easy to reach (friends, people who already like the open-source tool) and who is missing |

## 2. Tally output

Paste the output of `python roadmap/interviews/scripts/tally_interviews.py` here (run without `--include-examples`):

```text
(paste here)
```

## 3. Themes

One row per theme. "Count" is the number of interviews where it came up (use the aliases), not the number of mentions.

| Theme | Count | Interviews | Representative quote (anonymised) |
|---|---|---|---|
| e.g. TODOs are written and never read again | N / N | INT-001, INT-004 | "…" |
| | | | |
| | | | |

Notes on each theme (what exactly was said, exceptions, and what people already do about it):

## 4. Pains ranked by frequency × intensity

Frequency is the number of interviews that described the pain. Intensity is the mean pain score (1 to 5, from the notes) of the people who described
it. Score = frequency × intensity. Rank by score and show your working.

| Rank | Pain | Frequency (N) | Mean intensity | Score | Is it about TODOs, or something adjacent? |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

What do people do today for the top pains (current process, tools tried, why they did or did not stick)?

## 5. Ownership and budget

| Question | What we heard (counts) |
|---|---|
| Who owns the problem? | N tech leads, N EMs, N nobody |
| Who approves spend, and up to what amount without approval? | |
| Typical purchase process (card, procurement, security review)? | |
| What do they pay for today in this area? | |

## 6. Willingness to pay

| | Count |
|---|---|
| Yes | N |
| Maybe | N |
| No | N |

Amounts named (INR per month, before seeing the prices): …

Reaction to the ₹1,499 (Team) and ₹4,999 (Business) anchors: too cheap N, about right N, too expensive N, not for us N.

Commitments (concrete next step agreed):

| Pilot | Pre-order | Letter of intent | None |
|---|---|---|---|
| N | N | N | N |

⚠️ "It sounds good" and "send me the link" are not commitments. Count a commitment only if a person agreed to a specific step.

## 7. Mapping to the 2.3 GO criteria

Only the first and third rows come from the interviews. The others are filled in at the GO / NO-GO step from `roadmap/metrics.md` and the waitlist
sheet.

| Signal | GO threshold | Result | Met? |
|---|---|---|---|
| Teams that say they would pay (or commit to a paid pilot, pre-order or LOI) | 5 or more | N / 5 needed | yes / no |
| Waitlist signups | 100 or more, with 20% or more answering "yes" to paying | (from the sheet) | |
| Interviewees who rate the pain 4/5 or higher and describe a recurring problem | 3 or more | N / 3 needed | yes / no |
| Repos using the GitHub Action | 20 or more | (from metrics) | |

How reliable is the evidence? (one team per interview? friendly sources? any commitment that actually has a date?)

## 8. PIVOT signals

Tick what you saw, with counts and aliases. Several ticks mean the pain may be real but about something other than the planned product.

- [ ] The pain is strong (4 or 5) but it is **not about TODOs**: it is about general tech debt visibility, stale code, ownership of code, lint suppressions, skipped tests, outdated dependencies or something else (name it):
- [ ] People want the thing **inside a tool they already use** (Jira, Slack, GitHub Issues, an IDE) rather than a new dashboard.
- [ ] The **buyer is different** from the people interviewed (a CTO, platform team or security team) and nobody interviewed can approve spend.
- [ ] People already have a **good-enough workaround** (a lint rule, a ticket label, a weekly meeting) and would not pay to replace it.
- [ ] The pain is real but **a free or open-source tool is enough** (the existing CLI, Action or pre-commit hook), so there is no paid need.
- [ ] Interest is strong in **a smaller or larger customer** than the 10 to 200 developer profile.
- [ ] Willingness to pay is "yes" only for a **different feature set** than the pricing sketch shows.

## 9. NO-GO signals

- [ ] Fewer than 3 people rate the pain 4 or more with a recurring problem.
- [ ] Most "yes" answers have no concrete next step.
- [ ] Nobody can say who would pay.
- [ ] Interviews were mostly with people who already like the open-source tool (selection bias).

## 10. Recommendation for 2.3

GO / PIVOT / NO-GO on the interview evidence alone, with the three strongest reasons and the evidence for each. The maintainer decides in
`roadmap/decision-saas.md`.

## 11. What to change in the product, the pricing and the script

- Phase 3 scope changes suggested by the interviews:
- Pricing observations (anchors, tiers, metric):
- Changes to the landing page (what was unclear or missing):
- Questions to ask in the next round:
