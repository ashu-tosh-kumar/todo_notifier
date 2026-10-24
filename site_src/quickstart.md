# Quickstart (5 minutes)

By the end of this page TODO Notifier will list the TODOs of your project, fail a pull request that adds an expired one, and stop a commit that touches
one. You need Python 3.10 or newer and git.

Every output below was captured by running the command on the small sample project shown next. Your project will print different TODOs, and the
numbers of days depend on the day you run the commands.

??? note "No project at hand? Create the sample project"

    ```bash
    mkdir demo && cd demo && git init -q -b main
    mkdir src
    printf 'def main():\n    # TODO {2026-04-01} @alice Remove the legacy path\n    return 0\n' > src/app.py
    printf '# FIXME Rewrite this module\ndef parse(text):\n    return text.split()\n' > src/old.py
    printf 'def lookup(key):\n    # TODO(carol) {2030-01-15}: Cache the lookup\n    return key\n' > src/api.py
    git add . && GIT_AUTHOR_DATE="2026-01-10T10:00:00" GIT_COMMITTER_DATE="2026-01-10T10:00:00" \
      git -c user.name=alice -c user.email=alice@example.com commit -qm "Add the app"
    printf '\n# HACK Think about naming\n' >> src/api.py
    git add . && git -c user.name=bob -c user.email=bob@example.com commit -qm "Tweak the API"
    ```

    The commits matter: the owners and ages come from `git blame`.

## 1. Install

[pipx](https://pipx.pypa.io/) installs the tool in its own environment, so it never clashes with your project's dependencies.

```bash
pipx install todonotifier
```

```text
  installed package todonotifier 2.1.0, installed using Python 3.13.17
  These apps are now available
    - todonotifier
done! ✨ 🌟 ✨
```

`pip install todonotifier` works too, and also gives you the [Python API](python-api.md). Check it with `todonotifier --version`, which prints
`todonotifier 2.1.0`.

## 2. Scan

Run it in the root of your project. It needs no config: it reads the comments of the [common languages](syntax.md#supported-languages), skips what
`.gitignore` excludes, and asks `git blame` who wrote each line and when.

```bash
todonotifier scan .
```

```text
LOCATION      TAG    OWNER  DUE                      MESSAGE
src/api.py:2  TODO   carol  2030-01-15 due in 1179d  Cache the lookup
src/api.py:5  HACK   bob    2027-01-22 due in 90d    Think about naming
src/app.py:2  TODO   alice  2026-04-01 overdue 206d  Remove the legacy path
src/old.py:1  FIXME  alice  2026-04-10 stale 197d    Rewrite this module

4 TODOs · 1 overdue · 1 stale · 0 unowned
```

Read the DUE column like this:

- **overdue**: the TODO has an explicit `{date}` and it has passed (`src/app.py`).
- **stale**: the TODO has no date, so it was given a default one, 90 days after `git blame` says it was added, and that has passed (`src/old.py`).
- **due in ...**: a date that has not passed. `src/api.py:5` has no date either; it is owned by `bob` and has the default due date.

To fail on the overdue ones, which is what CI will do, add `--fail-on expired`. The command prints the table, a reason on stderr, and exits with 1:

```bash
todonotifier scan . --fail-on expired; echo "exit code: $?"
```

```text
LOCATION      TAG    OWNER  DUE                      MESSAGE
src/api.py:2  TODO   carol  2030-01-15 due in 1179d  Cache the lookup
src/api.py:5  HACK   bob    2027-01-22 due in 90d    Think about naming
src/app.py:2  TODO   alice  2026-04-01 overdue 206d  Remove the legacy path
src/old.py:1  FIXME  alice  2026-04-10 stale 197d    Rewrite this module

4 TODOs · 1 overdue · 1 stale · 0 unowned
todonotifier: --fail-on expired: 1 overdue TODO (an explicit date has passed)
exit code: 1
```

## 3. Write a config file (optional)

Everything works without one. `init` writes a starter file in which every option is commented out, so you can see what can be changed:

```bash
todonotifier init
```

```text
Created .todonotifier.toml. Every option in it is commented out: edit it to change the defaults.
Next: run 'todonotifier scan .' to see your TODOs, and see the docs to set up notifications: https://ashu-tosh-kumar.github.io/todo_notifier/notifications/
```

If your project has a `pyproject.toml`, `init` appends a commented `[tool.todonotifier]` section to it instead. Commit the file. All options are in
the [configuration reference](reference/configuration.md).

## 4. Check pull requests with the GitHub Action

Create `.github/workflows/todos.yml`. In `pr` mode the action looks only at the lines the pull request adds or changes, so old TODOs never block an
unrelated change:

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
          fetch-depth: 0          # git blame and the changed lines need the full history
          persist-credentials: false
      - uses: ashu-tosh-kumar/todo_notifier/integrations/github-action@v2.1.0
        with:
          mode: pr
          fail-on: expired        # fail the check when the pull request adds an expired TODO
```

The action runs on GitHub, so there is nothing to print locally. It runs the same scan you ran above, limited to the lines of the pull request, and
turns the result into annotations. This is that scan for a pull request that adds an expired TODO to `src/app.py` (a branch off `main`, scanned with
`--since main`):

```bash
todonotifier scan . --since main --format github --fail-on expired
```

```text
::error file=src/app.py,line=5,title=TODO overdue by 53d::Delete this shim (@bob, due 2026-09-01)
1 TODO: 1 overdue, 0 stale, 0 unowned
todonotifier: --fail-on expired: 1 overdue TODO (an explicit date has passed)
```

On the pull request that line shows as a red annotation on the "Files changed" tab, the job summary has a table, and the check fails. More in
[CI integrations](ci.md).

## 5. Check commits with pre-commit

Add this to `.pre-commit-config.yaml` (install [pre-commit](https://pre-commit.com) first, for example with `pipx install pre-commit`):

```yaml
repos:
  - repo: https://github.com/ashu-tosh-kumar/todo_notifier
    rev: v2.1.0
    hooks:
      - id: todonotifier
```

```bash
pre-commit install
pre-commit run --all-files
```

```text
pre-commit installed at .git/hooks/pre-commit
[INFO] Initializing environment for https://github.com/ashu-tosh-kumar/todo_notifier.
[INFO] Installing environment for https://github.com/ashu-tosh-kumar/todo_notifier.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
todonotifier (overdue TODOs).............................................Failed
- hook id: todonotifier
- exit code: 1

LOCATION      TAG    OWNER  DUE                      MESSAGE
src/api.py:2  TODO   carol  2030-01-15 due in 1179d  Cache the lookup
src/api.py:5  HACK   -      -                        Think about naming
src/app.py:2  TODO   alice  2026-04-01 overdue 206d  Remove the legacy path
src/old.py:1  FIXME  -      -                        Rewrite this module

4 TODOs · 1 overdue · 0 stale · 2 unowned
todonotifier: --fail-on expired: 1 overdue TODO (an explicit date has passed)
```

The hook runs without `git blame` to stay fast, so it only judges explicit `{date}`s, and the HACK and FIXME have no owner here. From now on, a commit
that touches a file with an expired TODO is stopped until you fix the TODO or its date. See [pre-commit](pre-commit.md) for the strict hook and for
turning blame on.

## Where next

- Send a weekly digest to Slack or Teams: [Notifications](notifications.md).
- Learn the full [TODO syntax](syntax.md): `TODO(owner)`, dates, other tags.
- Tune the scan: [Configuration](reference/configuration.md) and [Command line](cli.md).
