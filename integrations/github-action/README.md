# TODO Notifier GitHub Action

Deadlines, owners and digests for the TODO comments in your code. This action is **not** a "TODO to issue" action (for that, see
[todo-to-issue-action](https://github.com/alstr/todo-to-issue-action)). It answers two other questions:

- **In a pull request:** does this change add a TODO that is already overdue, or one nobody owns? The action puts an annotation on each such line,
  writes a table to the job summary, can keep one comment up to date on the pull request, and can fail the check.
- **Every week:** which TODOs are overdue, stale or due soon, and who owns them? The action scans the repository, sends the digest to Slack, Microsoft
  Teams or a webhook, and uploads the HTML reports as an artifact.

It is a thin wrapper around the [`todonotifier`](https://pypi.org/project/todonotifier/) command line tool, so everything the tool does (the config file,
tags, `git blame` owners, default due dates) works here too. See the [documentation](https://ashu-tosh-kumar.github.io/todo_notifier/) for the TODO format and the config file.

> **Where it lives.** Until the action has its own repository (`todonotifier-action`), use it from this repository:
> `uses: ashu-tosh-kumar/todo_notifier/integrations/github-action@<ref>`, where `<ref>` is a release tag or, better, a full commit SHA.
> The folder is self-contained, see [Moving to the todonotifier-action repo](#moving-to-the-todonotifier-action-repo).

<!-- release-note: delete this block once todonotifier 2.1.0 is on PyPI and v2.1.0 is tagged (RELEASING.md) -->
> **Release status.** The examples use `@v2.1.0` and install `todonotifier` 2.1.0 from PyPI, which work once that release is published and tagged. Before
> that, use a commit SHA as `<ref>` and add `package: git+https://github.com/ashu-tosh-kumar/todo_notifier@<the same SHA>`.

> **Runners.** Only `ubuntu-latest` is tested. The scripts need `bash`, `python`, `git`, and (for the comment) `gh` and `jq`, which the Windows and macOS
> hosted runners also have, so they should work, but nobody has run them there. Please report a problem.

## Pull requests

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
          fetch-depth: 0 # git blame (owners, ages) and --since (changed lines) need the full history
          persist-credentials: false
      - uses: ashu-tosh-kumar/todo_notifier/integrations/github-action@v2.1.0
        with:
          mode: pr
          fail-on: expired # fail the check when the pull request adds a TODO whose {date} has passed
```

What you get:

- **Annotations** on the lines the pull request adds or changes: overdue TODOs are errors, stale ones and those due within 7 days are warnings, the
  rest are notices. GitHub shows at most 10 annotations of each level per step; the job summary has the full table.
- **A table in the job summary** (open, overdue, stale, due this week, unowned, new) with the TODOs grouped by owner.
- **`fail-on`:** the check fails if such a TODO is on a changed line. In `pr` mode only the lines the pull request adds or changes count, so old
  TODOs never block an unrelated change. Without `fail-on` the action only reports.
- **Outputs** (`total`, `overdue`, `stale`, `new`) for later steps.

### Sticky pull request comment

Set `comment: true` to keep one comment on the pull request, updated on every push (the action finds its own comment by a hidden marker,
`<!-- todonotifier-action -->`, so there is never more than one). It starts with a line such as
"This PR adds 3 TODOs: 1 without an owner, 1 overdue, 0 stale." followed by the same table as the job summary.

```yaml
permissions:
  contents: read
  pull-requests: write # only needed for comment: true

# ...
      - uses: ashu-tosh-kumar/todo_notifier/integrations/github-action@v2.1.0
        with:
          mode: pr
          comment: true
```

Pull requests from forks get a read-only token even with `pull-requests: write`; the action then prints a warning and carries on (the annotations,
the summary and `fail-on` still work). The comment is skipped with a notice on events other than `pull_request` and `pull_request_target`. It uses the
`gh` command line tool, which every GitHub-hosted runner has.

## Weekly digest

Copy this to `.github/workflows/todo-digest.yml`, and add the Slack incoming webhook URL as the repository secret `SLACK_WEBHOOK_URL`
(see [Slack](https://ashu-tosh-kumar.github.io/todo_notifier/notifications/#slack) for how to create one):

```yaml
name: TODO digest

on:
  schedule:
    - cron: "0 8 * * 1" # Mondays at 08:00 UTC
  workflow_dispatch: # lets you run it by hand to try it

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

The `digest` mode scans the whole repository, writes the job summary, sends the digest to every webhook you give, and uploads the three HTML reports
(module-wise, expired by user, upcoming week) as the artifact `todonotifier-report` (its folder is the output `report-path`). Without a webhook input
nothing is sent and a notice says so (an empty or misspelled secret counts as not set); you still get the summary and the artifact. If a message cannot be delivered the job fails, after the summary and the artifact are
done. Scheduled workflows run on the default branch only, and GitHub pauses them in a public repository after 60 days without activity.

Use `fail-on` together with `digest` if you want the scheduled run to go red when something is overdue.

## Inputs

| Input | Default | Meaning |
|---|---|---|
| `mode` | `pr` | `pr`: only the lines the pull request adds or changes (`--since` the base commit). `digest`: the whole repository, then notify and upload the reports. |
| `version` | `2.1.0` | Version of the `todonotifier` package to install from PyPI. Pin it; the action never installs "latest". |
| `package` | | Advanced. A pip requirement that replaces `todonotifier==<version>`, e.g. a path to a checkout or a git URL. The self-test of this repository uses it to install the code under test. |
| `config` | | Config file (`.todonotifier.toml`, or a `pyproject.toml` with `[tool.todonotifier]`), relative to `working-directory`. Default: the file the tool finds in the repository. |
| `working-directory` | `.` | Directory to scan, relative to the repository root. |
| `fail-on` | `none` | Fail the action if such a TODO exists: `none`, `expired` (an explicit `{date}` has passed), `stale` (also default due dates), `any`, `incomplete` (no owner or no explicit date written in the comment). In `pr` mode: on changed lines. This input decides; a `fail_on` in the config file is not used by the action. |
| `default-due-days` | | A TODO without a date turns **stale** this many days after `git blame` says it was added. `0` turns this off. Default: the config file, else `90`. |
| `tags` | | Comma separated tags, e.g. `TODO,FIXME`. Default: the config file, else `TODO,FIXME,HACK,XXX`. |
| `extensions` | | Comma separated extensions without the dot, e.g. `py,js`, or `common`. Default: the config file, else `common`. |
| `slack-webhook` | | Slack incoming webhook URL (`digest` mode). Pass a secret. |
| `teams-webhook` | | Microsoft Teams webhook URL (`digest` mode). Pass a secret. |
| `webhook-url` | | URL that receives the digest as JSON (`digest` mode). Pass a secret. |
| `comment` | `false` | `true`: post and update one comment on the pull request (`pr` mode). Needs `pull-requests: write`. |
| `github-token` | `${{ github.token }}` | Token for the comment. Nothing else uses it. |
| `python-version` | `3.12` | Python used to run the tool (3.10 or newer). |
| `artifact-name` | `todonotifier-report` | Name of the artifact with the HTML reports (`digest` mode). Artifact names must be unique within a workflow run, so set it if you use the action twice in one run. |

A webhook that is not a secret is still masked in the log (`::add-mask::`). The notifiers that the config file defines in `[tool.todonotifier.notify.*]`
(for example email) are used too, but only when at least one webhook input is given; the Slack, Teams and webhook inputs are added on top of them. The
tool reads each webhook from an environment variable that the action sets from the input (`todonotifier notify --slack-webhook-env NAME`), so the URL
is never on a command line.

## Outputs

| Output | Meaning |
|---|---|
| `total` | Number of TODOs found. In `pr` mode: on the lines the pull request adds or changes. |
| `overdue` | Number of TODOs whose explicit `{date}` has passed. |
| `stale` | Number of TODOs whose default due date has passed. |
| `new` | Number of TODOs on the changed lines (`pr` mode). Empty in `digest` mode. |
| `report-path` | Folder with the HTML reports (`digest` mode). Empty in `pr` mode. |

```yaml
      - uses: ashu-tosh-kumar/todo_notifier/integrations/github-action@v2.1.0
        id: todos
      - run: echo "$OVERDUE overdue TODOs"
        env:
          OVERDUE: ${{ steps.todos.outputs.overdue }}
```

The outputs and the job summary are written before the action fails because of `fail-on`, so a later step with `if: always()` (or
`continue-on-error: true` on the action step) can still read them.

## Least privilege

| Use | `permissions:` |
|---|---|
| `pr` mode, `digest` mode, annotations, summary, `fail-on` | `contents: read` |
| `pr` mode with `comment: true` | `contents: read` and `pull-requests: write` |

The action needs no other permission and no secret except the webhooks. It never writes to the repository. Use `persist-credentials: false` on
`actions/checkout`, since nothing after it needs to push.

Good to know:

- **Injection safety.** The action passes every input and event field to its scripts through environment variables and quotes them; nothing from
  `inputs.*` or `github.event.*` is pasted into a shell script. TODO text from the scanned files is untrusted too: annotations escape it, and the
  Markdown in the summary and the comment is escaped (an `@user` or `@org/team` in a TODO message is defused, so the comment notifies nobody).
- **Use `pull_request`, not `pull_request_target`,** unless you know why. With `pull_request_target` the workflow runs with a write token, and its default
  checkout is the base branch, not the pull request. The action only reads files and never runs code from the repository, but that is no reason to give
  untrusted pull requests a write token.
- **Pin the action** to a release tag or a full commit SHA, and pin `version`.
- **`safe.directory`.** The action runs `git config --global --add safe.directory "$GITHUB_WORKSPACE"` once, because git refuses repositories that
  belong to another user ("dubious ownership"), which happens in containers. On a GitHub-hosted runner the setting disappears with the runner. On a
  self-hosted runner it stays in the global git config of the runner user.

## Troubleshooting

- **"The repository is a shallow clone" warning, or all owners are the same person.** Use `fetch-depth: 0` on `actions/checkout` (every example above
  does). Without full history `git blame` cannot tell who wrote a line or when. In `pr` mode the action fetches the base commit of a shallow checkout
  by itself (just that commit, so `--since` works), but if that fails (a private repository checked out with `persist-credentials: false`) the scan
  fails with exit code 2 and a warning "Base commit missing".
- **`pr` mode scans the whole repository.** The event is not a pull request (there is no base commit), so `since` cannot be used; a notice says so.
- **Exit code 2 or 3 of the scan.** The action fails with an `::error` that says which, and the message of the tool is in the log of the "Scan" step.
  Typical causes: a `config` path that does not exist, a webhook variable that is empty, or a base commit that is not in the clone.
- **No annotations on the "Files changed" tab.** GitHub shows them only on lines that are part of the diff, and only 10 per level per step.
  The job summary and the comment have the full list.
- **The comment is missing.** Check `permissions: pull-requests: write`, that the pull request is not from a fork, and the "Post or update the pull request
  comment" step of the log for a warning.

## How it works

One scan, many renderings. The action installs `todonotifier`, runs `todonotifier scan --format json` **once**
(`--since <base sha>` in `pr` mode) and keeps its exit code. [`scripts/render.py`](scripts/render.py) then reads that JSON and uses the library to
print the annotations, write the job summary and the outputs, write the comment body and the HTML reports. In `digest` mode `todonotifier notify`
scans again to send the digest. The last step applies `fail-on` with the same rule as `todonotifier scan --fail-on` and also fails if the scan or a
notification failed, so a failure never hides the summary.

## Moving to the todonotifier-action repo

This folder is the whole action: `action.yml` at its root, the `scripts/` folder, and this README. The maintainer can move it to its own repository,
which GitHub Marketplace requires (a public repository with a single `action.yml` at its root):

1. Create the public repository `todonotifier-action` and copy this folder's **contents** to its root
   (`cp -R integrations/github-action/. ../todonotifier-action/`). Leave `selftest.toml` behind, or keep it for the self-test in step 4.
2. Check the `name` in `action.yml`. A Marketplace name must be unique: it cannot match an existing action, a Marketplace category, or a user or
   organization (other than your own). If "TODO Notifier" is taken, change `name:`.
3. In the copied `README.md`, replace every `ashu-tosh-kumar/todo_notifier/integrations/github-action@...` with `ashu-tosh-kumar/todonotifier-action@v1`
   (the links to the documentation site are absolute, so they keep working). Enable Dependabot for the `github-actions` ecosystem in the new repository, because the action pins its own actions by commit SHA.
4. Move the self-test: copy `.github/workflows/action-selftest.yml` and the fixtures `tests/fixtures/languages` and `tests/fixtures/action`, use
   `uses: ./`, replace `package: ${{ github.workspace }}` by `version: <the version on PyPI>` and fix the `working-directory` paths.
   (`tests/test_action_render.py` in the main repository tests `scripts/render.py` and stays there while the action is also used from there.)
5. Tag the release: `git tag -a v1.0.0 -m "v1.0.0" && git tag -f -a v1 -m "v1" && git push origin v1.0.0 && git push -f origin v1`. The moving
   `v1` tag is the one users put in `uses:`; move it with every compatible release.
6. Publish to the Marketplace: on the repository page, open `action.yml` (a banner offers it) or draft a release for `v1.0.0`, tick
   **Publish this Action to the GitHub Marketplace** (the account must have accepted the Marketplace Developer Agreement, and 2FA is required), and choose
   the categories **Code quality** (primary) and **Utilities**.
7. Keep `version` in `action.yml` equal to a version that is on PyPI.
