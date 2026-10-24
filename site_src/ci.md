# CI integrations

TODO Notifier runs in any CI system: install it, run `todonotifier scan` and let the exit code decide. The only thing it needs from the checkout is the
**full git history** (`fetch-depth: 0` on GitHub, `GIT_DEPTH: 0` on GitLab), because `git blame` and `--since` read it. In a shallow clone the scan still
works, but it warns, and the owners and ages are missing or wrong. See the [FAQ](faq.md#shallow-clones).

## GitHub Action

The action in [`integrations/github-action`](https://github.com/ashu-tosh-kumar/todo_notifier/tree/main/integrations/github-action) is for **deadlines,
owners and digests**, not for turning TODOs into issues. It is a thin wrapper around the command line tool, so the config file, tags, owners and default
due dates all work the same. Pin it to a release tag or, better, a full commit SHA.

It has two modes. (`@v2.1.0` and the PyPI release it installs exist once 2.1.0 is published; see the release status note in the
[Quickstart](quickstart.md).)

### Pull requests (`mode: pr`)

Copy this to `.github/workflows/todos.yml`:

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
          fetch-depth: 0          # git blame (owners, ages) and --since (changed lines) need the full history
          persist-credentials: false
      - uses: ashu-tosh-kumar/todo_notifier/integrations/github-action@v2.1.0
        with:
          mode: pr
          fail-on: expired        # fail the check when the pull request adds a TODO whose {date} has passed
```

You get:

- **Annotations** on the lines the pull request adds or changes. Overdue TODOs are errors, stale ones and those due within 7 days are warnings, the
  rest are notices. GitHub shows at most 10 of each level per step; the job summary has the full table.
- **A table in the job summary**: open, overdue, stale, due this week, unowned and new, with the TODOs grouped by owner.
- **`fail-on`**: the check fails if such a TODO is on a changed line, so old TODOs never block an unrelated change. Without it the action only reports.
- **Outputs** `total`, `overdue`, `stale` and `new` for later steps.

Set `comment: true` (and `pull-requests: write`) to keep one comment on the pull request, updated on every push. Pull requests from forks get a read-only
token: the action then prints a warning and carries on.

### Weekly digest (`mode: digest`)

Scan the whole repository on a schedule and send the digest to Slack, Teams or a webhook. Add the webhook URL as a repository secret first
([how to create one](notifications.md)).

```yaml
name: TODO digest
on:
  schedule:
    - cron: "0 8 * * 1"      # Mondays at 08:00 UTC
  workflow_dispatch:          # lets you run it by hand to try it
permissions:
  contents: read
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
          # teams-webhook: ${{ secrets.TEAMS_WEBHOOK_URL }}
          # webhook-url: ${{ secrets.TODO_WEBHOOK_URL }}
```

It also writes the job summary and uploads the three HTML reports as the artifact `todonotifier-report`. Without a webhook input nothing is sent. Scheduled
workflows run on the default branch only, and GitHub pauses them in a public repository after 60 days without activity.

### Permissions

| Use | `permissions:` |
|---|---|
| `pr` mode, `digest` mode, annotations, summary, `fail-on` | `contents: read` |
| `pr` mode with `comment: true` | `contents: read` and `pull-requests: write` |

The action is tested on `ubuntu-latest` only. Use `pull_request`, not `pull_request_target`, unless you know why: the latter runs with a write token. The action never writes to the repository, so use
`persist-credentials: false` on checkout. All inputs, outputs and troubleshooting tips are in the
[action README](https://github.com/ashu-tosh-kumar/todo_notifier/blob/main/integrations/github-action/README.md).

### Without the action

The command line does the same on any runner. This fails the job when a pull request adds an expired TODO and writes annotations:

```yaml
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - run: pipx install todonotifier
      - run: todonotifier scan . --format github --since "origin/$BASE_REF" --fail-on expired
        env:
          BASE_REF: ${{ github.base_ref }}   # through env, never ${{ }} inside the script: a branch name is not trusted text
```

## GitLab CI

GitLab has no annotations for these results, so print the table in the job log and keep the JSON as an artifact. On merge requests, look only at the
lines the merge request changed with `--since`:

```yaml
todos:
  stage: test
  image: python:3.12
  variables:
    GIT_DEPTH: "0"                 # full history for git blame and --since
  before_script:
    - git config --global --add safe.directory "$CI_PROJECT_DIR"
    - pip install todonotifier
  script:
    - todonotifier scan . --format json --output todos.json     # the artifact is written first, so it exists even if the check fails
    - |
      if [ -n "$CI_MERGE_REQUEST_DIFF_BASE_SHA" ]; then
        todonotifier scan . --since "$CI_MERGE_REQUEST_DIFF_BASE_SHA" --fail-on expired
      else
        todonotifier scan . --fail-on expired
      fi
  artifacts:
    when: always
    paths:
      - todos.json
```

Choose the `--format` for the job log: `table` (the default) reads best in a log. `json` is for artifacts and other tools, `markdown` for a comment or
a wiki, and `sarif` and `github` are for GitHub code scanning and annotations, so they do nothing special on GitLab.

## Any other CI

1. Check out the **full history** (not a shallow clone).
2. Install Python 3.10 or newer and `pipx install todonotifier` (or `pip install todonotifier`).
3. Run the check. Its exit code decides the job:

   ```bash
   todonotifier scan . --fail-on expired
   ```

For a pull request or merge request, add `--since <base commit or branch>` so that only the TODOs on changed lines count. To post a weekly digest from a
scheduled job, run `todonotifier notify . --slack-webhook-env NAME` with the webhook URL in a secret variable (see [Notifications](notifications.md)).

The exit codes are `0` OK, `1` the `--fail-on` condition was met, `2` usage or config error, `3` unexpected error. Treat anything but `0` as a failure,
or let `1` fail the build and alert on `2` and `3`. See [CLI flags and exit codes](reference/cli.md).
