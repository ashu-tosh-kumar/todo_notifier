# TODO Notifier

**Find every TODO in your code, see who owns it and how old it is, and fail CI when one expires.**

TODO Notifier is a **TODO deadline reminder**, **FIXME tracker** and lightweight **technical debt tracker**. It finds `TODO`, `FIXME`, `HACK` and `XXX`
comments, gives each one an owner (from `@user`, `TODO(user)` or `git blame`) and a due date, flags every **overdue TODO**, and tells your team in the
terminal, in CI, and by Slack, Teams, webhook or email. It needs no config to start.

## Three commands

```bash
pipx install todonotifier                     # install the command line tool in its own environment
todonotifier scan .                           # list every TODO with its owner and due date
todonotifier scan . --fail-on expired         # exit with 1 if a TODO's {date} has passed (for CI)
```

```text
LOCATION      TAG    OWNER  DUE                      MESSAGE
src/api.py:2  TODO   carol  2030-01-15 due in 1179d  Cache the lookup
src/api.py:5  HACK   bob    2027-01-22 due in 90d    Think about naming
src/app.py:2  TODO   alice  2026-04-01 overdue 206d  Remove the legacy path
src/old.py:1  FIXME  alice  2026-04-10 stale 197d    Rewrite this module

4 TODOs · 1 overdue · 1 stale · 0 unowned
```

New here? The [Quickstart](quickstart.md) takes 5 minutes and ends with the check running in CI and in your commits.

## What you get

- **A command line tool** that works with zero config: table, JSON, GitHub annotations, SARIF and Markdown output, `--fail-on` for CI and `--since`
  for pull requests. [Command line](cli.md)
- **Owners and ages from `git blame`**, so old undated TODOs are noticed. An undated TODO turns *stale* after 90 days; one whose `{date}` has passed is
  *overdue*. [TODO syntax](syntax.md)
- **A GitHub Action** with annotations, a job summary, an optional sticky pull request comment, `fail-on`, and a weekly digest. [CI integrations](ci.md)
- **A pre-commit hook** that stops a commit that touches an overdue TODO. [pre-commit](pre-commit.md)
- **Slack, Microsoft Teams, webhook and email digests.** [Notifications](notifications.md)
- **A config file** (`.todonotifier.toml` or `[tool.todonotifier]` in `pyproject.toml`) for tags, languages, exclusions and notifiers.
  [Configuration](reference/configuration.md)
- **A Python API** for embedding a scan (`scan()` returns a structured, JSON-serializable result), custom report generators and custom notifiers.
  [Python API](python-api.md)
- **Privacy by default.** Nothing leaves your machine unless you configure a notifier. [FAQ](faq.md#privacy)

## Where to go next

| I want to... | Read |
|---|---|
| try it now | [Quickstart](quickstart.md) |
| write TODOs it understands | [TODO syntax](syntax.md) |
| fail pull requests on expired TODOs | [CI integrations](ci.md) |
| get a weekly digest in Slack or Teams | [Notifications](notifications.md) |
| look up a flag or a config key | [CLI flags](reference/cli.md), [Configuration](reference/configuration.md) |
| compare it with other TODO tools | [How it compares](comparison.md) |
| call it from Python | [Python API](python-api.md), [API reference](api/index.html) |
