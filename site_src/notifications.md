# Notifications

The result of a scan can be turned into a **digest** and sent to Slack, Microsoft Teams, any webhook or email, from the config file with
`todonotifier notify`, from the [GitHub Action](ci.md) (`mode: digest`), or from Python.

The digest has these totals: open, overdue, stale, due this week, unowned and, when known, new TODOs. Below them come three sections, **Overdue**,
**Stale** and **Due this week**, each grouped by owner (most items first, unowned last) with the most overdue item first and a deep link to the line when
the repository URL and commit are known. "Overdue" means an explicit `{date}` has passed, "Stale" means a default due date has passed (see
[TODO syntax](syntax.md#overdue-versus-stale)). Each section shows at most `max_items` TODOs (default 10) and ends with "...and N more".

## Secrets stay out of files

A webhook URL is a secret. A config file never holds one: every `*_env` key names an **environment variable**, and a key like `webhook`, `url`,
`password` or `token` is rejected with a hint. `todonotifier notify` reads the variable when it sends. A variable that is missing or empty is a usage
error (exit code 2) that names the variable and never shows a value. Webhook URLs, request headers and response bodies never appear in logs or error
messages.

The HTTP notifiers use the standard library only, a 10 s timeout, and 2 retries with backoff (1 s, 2 s) on HTTP 5xx, 429 (a numeric `Retry-After` is
honoured, up to 30 s) and network errors. They do not retry other 4xx errors. Only `https://` URLs are accepted (`http://` only for `localhost` and
`127.0.0.1`, for tests). `notify` tries every notifier and prints one line per failure; it exits with 3 if any failed, unless `--fail-on` is met (1).

## Slack

1. Create an [incoming webhook](https://api.slack.com/messaging/webhooks) for the channel and copy its URL into a secret, for example
   `TODO_SLACK_WEBHOOK` (a repository secret in CI, an environment variable locally).
2. Add the table to your [config file](reference/configuration.md):

   ```toml
   [tool.todonotifier.notify.slack]
   webhook_env = "TODO_SLACK_WEBHOOK"
   max_items = 10
   ```

3. Send it:

   ```bash
   export TODO_SLACK_WEBHOOK="https://hooks.slack.com/services/..."
   todonotifier notify .
   ```

Or without a config file: `todonotifier notify . --slack-webhook-env TODO_SLACK_WEBHOOK`.

The message is a Block Kit message: a header, a section with the totals, and one section per digest group, with links to the code and a plain text
fallback for notifications. It respects Slack's limits (3000 characters per section, 50 blocks) and says how many TODOs did not fit.

!!! info "Screenshot placeholder"
    A screenshot of the Slack digest belongs here. The maintainer adds it as `site_src/assets/slack-digest.png` and replaces this box with
    `![The Slack digest](assets/slack-digest.png)`.

## Microsoft Teams

!!! warning "Check the current Microsoft documentation"
    Microsoft is retiring the Office 365 connectors in favour of Power Automate Workflows, and the format may change. The payload below follows the
    documented Workflows format and has not been verified against a live Teams tenant.

1. In the channel, create a workflow from the template "Post to a channel when a webhook request is received" (trigger "When a Teams webhook request is
   received") and copy its URL into a secret, for example `TODO_TEAMS_WEBHOOK`.
2. Add the table:

   ```toml
   [tool.todonotifier.notify.teams]
   webhook_env = "TODO_TEAMS_WEBHOOK"
   max_items = 10
   ```

It posts `{"type": "message", "attachments": [{"contentType": "application/vnd.microsoft.card.adaptive", ...}]}` with an Adaptive Card (version 1.4) made
of `TextBlock`s and a `FactSet`. Teams limits a message to about 28 KB, so keep `max_items` modest. A `TextBlock` understands only a small Markdown subset
and shows backslash escapes as they are, so text from the scanned files (messages, file names, authors) is neutralised, not escaped: `*`, `[`, `]`, the
backtick and underscores that are not inside a word are replaced by look-alike characters, which keeps a message from forming links or emphasis
(`my_file_name.py` is left alone). The links to the code lines still work.

!!! info "Screenshot placeholder"
    A screenshot of the Teams card belongs here (`site_src/assets/teams-digest.png`).

## Generic webhook

POSTs this JSON, for Discord bridges, Zapier, n8n or internal tools:

```json
{"event": "todonotifier.scan", "result": {"...": "ScanResult.to_dict()"}, "digest": {"open": 4, "overdue": 1, "stale": 1, "due_soon": 0, "unowned": 0}}
```

`result` is the [JSON output](python-api.md#the-json-output). `headers_env` names a variable that holds a JSON object of extra headers, for example
`{"Authorization": "Bearer ..."}`; the headers are not forwarded if the server redirects.

```toml
[tool.todonotifier.notify.webhook]
url_env = "TODO_WEBHOOK_URL"
headers_env = "TODO_WEBHOOK_HEADERS"   # optional
```

## Email

```toml
[tool.todonotifier.notify.email]
smtp_host = "smtp.example.com"
smtp_port = 587
starttls = true
sender = "todo@example.com"
recipients = ["team@example.com"]
username_env = "TODO_SMTP_USER"        # optional, if the login is not the sender
password_env = "TODO_SMTP_PASSWORD"
```

`smtp_port` defaults to 587 with `starttls = true`, else 465 (SSL). The email has the digest (a plain text part and an HTML part, escaped) and the
generated HTML reports below it.

From Python, `EmailNotifier.from_env()` reads the settings from these variables:

| Variable (prefix `TODO_SMTP_`) | Meaning |
|---|---|
| `HOST`, `SENDER`, `RECIPIENTS` (comma separated), `PASSWORD` | required |
| `PORT` | optional, default 587 with `STARTTLS`, else 465 |
| `USERNAME` | optional, default: the sender |
| `STARTTLS` | optional, `1`/`true`/`yes`/`on`, default off |

## Several notifiers

Add as many tables as you like; `enabled = false` keeps a table without using it. The keys of each table are in the
[configuration reference](reference/configuration.md#notifyname). To write your own notifier, see [Python API](python-api.md#custom-notifiers).
