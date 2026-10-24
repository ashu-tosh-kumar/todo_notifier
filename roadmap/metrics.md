# Launch metrics

Baseline recorded **2026-10-24**, before any launch post. Track the same numbers every week for 6 weeks after the launch (see the table at the end) so
that the 2.3 GO / NO-GO decision rests on a trend, not on one good day.

> Every number below was fetched on 2026-10-24 with `curl -s` from the source in the "Source" column. Nothing is estimated. Anything marked
> "manual" needs the maintainer's login and could not be read from here.

## Baseline (2026-10-24)

| Metric | Value | Source | How it was read |
|---|---|---|---|
| PyPI downloads, last day | 2 | <https://pypistats.org/api/packages/todonotifier/recent> | `data.last_day` |
| PyPI downloads, last week | 1 | <https://pypistats.org/api/packages/todonotifier/recent> | `data.last_week` |
| PyPI downloads, last month | 21 | <https://pypistats.org/api/packages/todonotifier/recent> | `data.last_month` |
| PyPI downloads, 7 days to 2026-10-22, without mirrors | 7 | <https://pypistats.org/api/packages/todonotifier/overall> | sum of the `without_mirrors` rows from 2026-10-16 to 2026-10-22 (rows exist only for days with downloads: 10-20: 3, 10-21: 2, 10-22: 2) |
| PyPI downloads, 30 days to 2026-10-22, without mirrors | 42 | <https://pypistats.org/api/packages/todonotifier/overall> | sum of the `without_mirrors` rows from 2026-09-23 to 2026-10-22 |
| PyPI downloads, since 2026-04-08, without mirrors | 284 | <https://pypistats.org/api/packages/todonotifier/overall> | sum of the 73 rows with `category = without_mirrors` (2026-04-08 to 2026-10-22) |
| PyPI downloads, since 2026-04-08, with mirrors | 1,455 | <https://pypistats.org/api/packages/todonotifier/overall> | sum of the 144 rows with `category = with_mirrors` (same range) |
| GitHub stars | 6 | <https://api.github.com/repos/ashu-tosh-kumar/todo_notifier> | `stargazers_count` |
| GitHub forks | 1 | <https://api.github.com/repos/ashu-tosh-kumar/todo_notifier> | `forks_count` |
| GitHub watchers (subscribers) | 1 | <https://api.github.com/repos/ashu-tosh-kumar/todo_notifier> | `subscribers_count`. The API field `watchers_count` is 6, but it is a legacy alias of the star count, so it is not recorded as watchers. |
| GitHub open issues and pull requests | 13 | <https://api.github.com/repos/ashu-tosh-kumar/todo_notifier> | `open_issues_count` (GitHub counts issues and PRs together) |
| "Used by" dependents | ⚠️ manual check | <https://github.com/ashu-tosh-kumar/todo_notifier/network/dependents> | Not available from the API. The maintainer opens the page and writes the count here. |
| Insights traffic: unique visitors and views (14 days) | ⚠️ manual check | <https://github.com/ashu-tosh-kumar/todo_notifier/graphs/traffic> | Needs push access to the repository (the REST traffic endpoints reject anonymous requests). GitHub keeps only 14 days of history, so **record it before the launch and then every week**. |
| Insights traffic: referrers and popular content | ⚠️ manual check | <https://github.com/ashu-tosh-kumar/todo_notifier/graphs/traffic> | Same page. Useful to see which channel worked. |
| GitHub Action Marketplace usage | 0 / n.a. | not published yet | The Action is not on the Marketplace (it lives in `integrations/github-action/`, decision A3). Nothing to count until it is published. |
| Waitlist signups | 0 | not live | The landing page and waitlist (2.1) are not live. |

### Notes on reading these numbers

- **The baseline is small, and that is fine.** Between 21 and 42 downloads in 30 days (depending on the endpoint, see below), some of which may be bots, tell us there is no existing
  audience. The launch is a cold start. Do not read the first weekly numbers as a verdict on the idea: they are a verdict on one week of posting.
- **Use the "without mirrors" series for decisions.** The "with mirrors" total is about five times larger (1,455 against 284) because mirrors and
  caches download every release. pypistats documents the difference at <https://pypistats.org/about>. ⚠️ I did not verify how pypistats classifies mirrors beyond that page's
  description.
- **The two pypistats endpoints do not agree.** `/recent` says 1 download last week and 21 last month; summing `/overall` (without mirrors) gives 7 and
  42 for the 7 and 30 days to 2026-10-22. ⚠️ I do not know why (different cut-off days or a different bot filter are possible). The weekly table uses
  the `/overall` sums, so the series is consistent from week to week. Data also lags by about a day: the last `/overall` row is 2026-10-22.
- **The release is not on PyPI yet.** `v2.1.0` is not published, so these downloads are of `2.0.x` and earlier (the baseline is for the old
  version). The "pepy.tech" total on the README badge counts differently (<https://pepy.tech/project/todonotifier>); it was not fetched here, so use one
  source and keep using it. ⚠️ not fetched (pepy.tech is a dynamic page and was left out to stay within the call budget).
- **Stars are a vanity metric.** They are recorded because people compare them. The numbers that matter more for the GO / NO-GO decision are: unique
  visitors to the docs, installs without mirrors, repositories using the Action or the hook (the dependents page, and a code search for
  `ashu-tosh-kumar/todo_notifier` in `.github/workflows` and `.pre-commit-config.yaml`), and issues and replies from real users.

## Weekly tracking (6 weeks after the launch)

Fill one row every Monday for the previous 7 days, always from the same sources as above. "Launch day" is the day the first post goes out; week 1 is the
seven days starting then. Put what you did that week (posts, releases, fixes) in the last column, because a number without its cause is hard to read
later.

| Week | Week starting | PyPI last week (without mirrors) | PyPI total (without mirrors) | Stars | Forks | Dependents | Unique visitors (14 d) | Docs visitors | Action users | Waitlist signups | What happened |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 (baseline) | 2026-10-24 | 7 (2026-10-16 to 10-22) | 284 | 6 | 1 | ⚠️ manual | ⚠️ manual | n.a. | 0 | 0 | Before the launch |
| 1 | | | | | | | | | | | |
| 2 | | | | | | | | | | | |
| 3 | | | | | | | | | | | |
| 4 | | | | | | | | | | | |
| 5 | | | | | | | | | | | |
| 6 | | | | | | | | | | | |

How to fill the columns:

- **PyPI last week and total:** `https://pypistats.org/api/packages/todonotifier/overall`. For the weekly figure, add up the `without_mirrors` rows
  of the last 7 days; for the total, add up all of them (or the rows since the last total, and add that to the previous total).
- **Stars, forks:** `https://api.github.com/repos/ashu-tosh-kumar/todo_notifier` (`stargazers_count`, `forks_count`).
- **Dependents:** the dependents page above.
- **Unique visitors (14 d):** Insights -> Traffic. Take the number on the day you record it; the 14-day windows overlap, so do not add them up.
- **Docs visitors:** ⚠️ the docs site has no analytics (privacy by default), so leave it as n.a. unless the maintainer decides to add some. Referrers in
  Insights -> Traffic show how many came from the docs and from each post.
- **Action users:** the Marketplace page once published, plus a GitHub code search for the `uses:` line. ⚠️ code search needs a login.
- **Waitlist signups:** the form provider's dashboard, once 2.1 is live.
