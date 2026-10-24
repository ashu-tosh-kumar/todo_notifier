# How it compares

Several good tools deal with TODO comments, and they solve different problems. This table shows what each one documents, so you can pick the
right tool or combine them.

| | **TODO Notifier** | [todo-to-issue-action](https://github.com/alstr/todo-to-issue-action) | [Todo Tree](https://github.com/Gruntfuggly/todo-tree) (VS Code) | [Ruff `TD` rules](https://docs.astral.sh/ruff/rules/#flake8-todos-td) |
|---|---|---|---|---|
| **Main job** | Track deadlines and owners, remind and gate CI | Turn committed TODOs into GitHub issues | Show TODOs in the editor | Lint the format of TODO comments |
| **Deadlines** | ✅ `{2026-12-31}` dates, plus a default due date for undated TODOs | ❌ not described | ❌ not described | ❌ no `TD` rule checks dates |
| **Owners** | ✅ `@user`, `TAG(user)` or `git blame` | ✅ `TODO(@user)` or an `assignees:` option assigns the new issue | ❌ not described | ◐ `TD002` requires an author to be present; it does not resolve or assign one |
| **Overdue alerts** | ✅ `--fail-on expired`, annotations, digests | ❌ not described | ❌ not described | ❌ |
| **Digests** | ✅ Slack, Teams, webhook, email | ❌ not described | ❌ not described (status bar and badge counts only) | ❌ |
| **PR checks** | ✅ `scan --since BASE --format github` annotations plus an exit code | ◐ runs on push and creates issues; not described as a check | ❌ editor only | ⚠️ unverified (the pages checked do not describe CI use) |
| **Issue creation** | ❌ (use todo-to-issue for this) | ✅ creates, updates and closes issues | ❌ not described | ❌ (`TD003` requires an issue link, it does not create one) |
| **IDE view** | ❌ terminal table, HTML reports | ❌ | ✅ tree view, highlighting, status bar | ◐ diagnostics through Ruff's editor integrations, no TODO list |
| **Language support** | Comment-aware detection for 37 file extensions (27 scanned by default) | 62 languages listed | Regex based: default regex matches tags after common comment markers; ⚠️ no language list stated | Python only (Ruff is a Python linter) |

✅ supported · ◐ partly · ❌ not supported, or not described in the source linked below (absence in a README is not proof that a feature does not
exist) · ⚠️ could not be verified from the sources.

## Which one should I use?

 Use Ruff `TD` for TODO *format* linting, todo-to-issue for turning TODOs into issues, and TODO Notifier for
deadlines, owners and reminders. They work well together.

Sources, all checked on 2026-10-23 (these tools change, so check their current docs before relying on a row):
[todo-to-issue-action README](https://github.com/alstr/todo-to-issue-action),
[Todo Tree README](https://github.com/Gruntfuggly/todo-tree),
[Ruff rules: flake8-todos (TD)](https://docs.astral.sh/ruff/rules/#flake8-todos-td) and the
[Ruff documentation home](https://docs.astral.sh/ruff/). Spot a mistake? Please [open an issue](https://github.com/ashu-tosh-kumar/todo_notifier/issues/new/choose).
