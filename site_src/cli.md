# Command line

`todonotifier scan .` needs no config (see the [Quickstart](quickstart.md)). It scans the [common languages](syntax.md#supported-languages), skips what
`.gitignore` excludes, counts tags only inside comments, and asks `git blame` who wrote each line and when. An undated TODO becomes **stale** 90 days
after it was added; a TODO whose `{date}` has passed is **overdue**.

Every flag, with its default, is in the [CLI flags and exit codes](reference/cli.md) reference, which is generated from the program. This page is the
guide.

## Commands

| Command | What it does |
|---|---|
| `todonotifier scan [PATH ...]` | Scan and print the TODOs (default path `.`, or the `paths` of the config file). Paths may be files, for example the staged files from pre-commit. |
| `todonotifier report [PATH ...] [--out DIR]` | Write the HTML reports (module-wise, expired by user, upcoming week) to `DIR` (default `.report`) and print their paths. Same as `scan --format html`. |
| `todonotifier notify [PATH ...]` | Scan, then send the digest to every notifier of the config file and to those added with `--slack-webhook-env`, `--teams-webhook-env` and `--webhook-url-env`. See [Notifications](notifications.md). |
| `todonotifier init` | Append a commented `[tool.todonotifier]` section to `pyproject.toml` (if it exists and has none), else create `.todonotifier.toml`. `--pyproject` or `--standalone` force one of them. Never overwrites anything. |
| `todonotifier --version` | Print the version. |

`python -m todonotifier ...` does the same as the `todonotifier` command. PATH arguments may be mixed with options
(`todonotifier scan a.py --format json b.py`); after a `--` everything is a path. A flag beats the config file, which beats the built-in defaults.

Colors are used only when stdout is a terminal, `NO_COLOR` is unset and there is no `--output`. Results go to stdout (or `--output`); logs and errors
go to stderr. If the reader of the output goes away (`todonotifier scan . | head -1`), the output ends quietly and the exit code is the one the run
would have had.

## Examples

```bash
todonotifier scan src/ tests/                      # only these directories
todonotifier scan . --tags TODO,FIXME              # fewer tags
todonotifier scan . --ext py,sql                   # only these file types ("common" is the preset)
todonotifier scan . --no-blame                     # no git blame: faster, but no authors, ages or default dates
todonotifier scan . --fail-on expired              # exit 1 if an explicit {date} has passed
todonotifier scan . --fail-on stale                # also fail on default due dates that have passed
todonotifier scan . --fail-on incomplete           # every TODO needs an owner and a {date} written in the comment
todonotifier scan . --since origin/main            # only TODOs on lines added or changed since origin/main
todonotifier scan . --format json --output todos.json
todonotifier report . --out reports                # HTML reports in ./reports
```

`--since GIT_REF` compares the working tree with the ref (staged and unstaged edits count, and new files count in full) and keeps only the TODOs on the
changed lines. `--fail-on` is judged after `--since`, so a pull request fails only for the TODOs it adds.

## Output formats

`--format` takes one of these (the default is `table`):

- `table`: aligned columns and a summary line.
- `json`: the whole result, documented by a [JSON Schema](python-api.md#the-json-output). Dates are ISO strings, "no due date" is `null`. New optional
  properties can appear without a version change; incompatible changes bump `schema_version`.
- `github`: [workflow commands](https://docs.github.com/actions/reference/workflow-commands-for-github-actions) that GitHub shows as annotations on the
  pull request. Overdue TODOs are errors, stale ones and those due within 7 days are warnings, the rest are notices. Paths are relative to the
  repository root, even if you scan a subdirectory.
- `markdown`: the digest that the notifiers send, for example for `$GITHUB_STEP_SUMMARY`.
- `sarif`: SARIF 2.1.0 for GitHub code scanning (one rule per tag, the same levels as `github`).
- `html`: the three built-in reports as files (use `report`).

```text
$ todonotifier scan . --format github --since origin/main
::error file=src/app.py,line=5,title=TODO overdue by 53d::Delete this shim (@bob, due 2026-09-01)
1 TODO: 1 overdue, 0 stale, 0 unowned
```

GitHub shows at most 10 error, 10 warning and 10 notice annotations per step, so `--since` keeps pull requests readable.

## Sending a digest

`notify` scans and then sends the digest to the notifiers of your config file. Three flags add a notifier without a config file, for CI jobs where the
webhook is a secret. Each takes the **name** of an environment variable that holds the URL, never the URL itself, so it cannot end up in a process list
or a shell history:

```bash
TODO_SLACK_WEBHOOK=https://hooks.slack.com/services/... todonotifier notify . --slack-webhook-env TODO_SLACK_WEBHOOK
```

A variable that is not set or is empty is a usage error (exit code 2) that names the variable and never shows a value. With `--since`, nothing is
sent (the reason is logged at INFO level, see `-v`) if no TODO is on a changed line; without `--since` an empty result is still sent, as an "all clear".

## Exit codes

The same list is in the generated [reference](reference/cli.md#exit-codes).

| Code | Meaning |
|---|---|
| `0` | OK |
| `1` | The `--fail-on` condition was met (for `notify`, this wins over a failed notification) |
| `2` | Usage or config error: a bad flag or config file, a path that does not exist, an unknown `--since` ref or no git repository for it, no notifier configured |
| `3` | Unexpected runtime error (the traceback is shown with `-v`), or a notification could not be delivered |

Errors are one line on stderr, for example `todonotifier: error: Unknown key 'tagz' in pyproject.toml [tool.todonotifier]. Did you mean 'tags'?`.
