# pre-commit

TODO Notifier ships two hooks for [pre-commit](https://pre-commit.com). Add this to your `.pre-commit-config.yaml`, then run `pre-commit install`
(and `pre-commit autoupdate` to move `rev` to a newer release):

```yaml
repos:
  - repo: https://github.com/ashu-tosh-kumar/todo_notifier
    rev: v2.1.0
    hooks:
      - id: todonotifier           # fails if a staged file has a TODO whose {date} has passed
      # - id: todonotifier-strict  # fails if a staged file has a TODO without an owner or an explicit {date}
```

<!-- release-note: delete this line once v2.1.0 is tagged (RELEASING.md) -->
`rev: v2.1.0` exists once the release is tagged; until then use a commit SHA of this repository.

| Hook | Runs | Fails the commit when |
|---|---|---|
| `todonotifier` | `todonotifier scan --fail-on expired --no-blame <staged files>` | a staged file has a TODO whose explicit `{date}` has passed |
| `todonotifier-strict` | `todonotifier scan --fail-on incomplete --no-blame <staged files>` | a staged file has a TODO without an owner (`@user` or `TODO(user)`) or without an explicit `{date}` |

Both hooks scan only the files pre-commit passes (one process, one `git ls-files` call, no walk of the repository). Binary files and files with an
unknown extension are skipped, and so is anything your config excludes (`exclude_dirs`, `exclude_files`, `.gitignore`). The config file of the repository
root (`[tool.todonotifier]` in `pyproject.toml`, or `.todonotifier.toml`) applies as usual, so `tags`, `extensions` and `require_comment` work in the hooks
too. The first run installs the tool in a pre-commit environment; after that the hook takes about 0.4 s for a commit of 10 files (measured with
`pre-commit run`, blame off). Only the TODOs in the staged files are looked at, but the whole file counts, not only the lines you changed.

The hook environment needs Python 3.10 or newer. If the `python3` that pre-commit finds is older, name a newer one at the top of your
`.pre-commit-config.yaml`: `default_language_version: {python: python3.12}`.

## What a stopped commit looks like

```text
todonotifier (overdue TODOs).............................................Failed
- hook id: todonotifier
- exit code: 1

LOCATION      TAG   OWNER  DUE                      MESSAGE
src/app.py:2  TODO  alice  2026-04-01 overdue 206d  Remove the legacy path

1 TODO · 1 overdue · 0 stale · 0 unowned
todonotifier: --fail-on expired: 1 overdue TODO (an explicit date has passed)
```

Fix the TODO (or move its `{date}`) and commit again.

## Blame is off by default

The hooks run with `--no-blame` so they stay fast: `git blame` runs once per file. The expired check only uses dates written in the comment, so it does
not need blame. Turn blame on when you want authors, ages and default due dates, for example to also fail on stale TODOs. pre-commit appends `args` to
the `entry`, before the file names. A later `--fail-on` replaces the earlier one, and a later `--blame` replaces the `--no-blame` of the entry:

```yaml
    hooks:
      - id: todonotifier
        args: [--blame, --fail-on, stale]   # runs: todonotifier scan --fail-on expired --no-blame --blame --fail-on stale <files>
```

Other flags work the same way, for example `args: [--tags, "TODO,FIXME"]` or `args: [--config, ci/todonotifier.toml]`. To change the scan for the hook
only, use `args`; to change it for every run, put it in the [config file](reference/configuration.md).

## Ruff's TD rules or TODO Notifier?

They do different jobs. Use [Ruff's TD rules](https://docs.astral.sh/ruff/rules/#flake8-todos-td) (flake8-todos) to lint the *format* of TODO comments,
and TODO Notifier for *deadlines*: `todonotifier` finds the overdue ones. `todonotifier-strict` overlaps with Ruff's `TD002` (author) and `TD003`
(issue link) in spirit but checks for an owner and a date; use it if you want every TODO dated, and skip it if Ruff already covers what you need. See
also [How it compares](comparison.md).

## Try it without installing anything

```bash
pre-commit try-repo https://github.com/ashu-tosh-kumar/todo_notifier todonotifier --files path/to/file.py
```
