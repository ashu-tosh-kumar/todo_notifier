# TODO syntax

A TODO is a tag in a comment, optionally followed by an owner, a date and a message. Everything but the tag is optional:

```python
# TODO {2026-12-31} @john_doe Implement user authentication     (date and owner)
# TODO {2026-12-31} Add error handling                          (date only)
# TODO @jane_smith Review this logic                            (owner only)
# TODO(jane_smith): Review this logic                           (owner in parentheses, Google style)
# FIXME(jane_smith) {2026-12-31} Handle the empty case
# FIXME: Crashes on empty input
# HACK @john_doe {2026-12-31} Remove after the migration
# TODO Fix this bug                                             (nothing but the message)
```

## The parts

| Part | Meaning |
|---|---|
| Tag | `TODO`, `FIXME`, `HACK` or `XXX` by default (`tags` in the [config file](reference/configuration.md), or `--tags` on the command line). Tags are matched as whole words, so `TODO_LIST`, `TODOS` and `todonotifier` are not tags, but `TODO:` and `TODO(` are. `ignore_case` also matches `todo` and `Todo`. |
| `(owner)` | The owner, right after the tag. The same as `@owner`. The owner must start with a letter, so `TODO(#123)` and `TODO(crbug.com/1)` stay part of the message. |
| `{YYYY-MM-DD}` | The due date. |
| `@username` | The owner. If both `(owner)` and `@user` are present, the one in parentheses wins. |
| `:` | One optional colon after the tag, the owner, the date or the user. It is dropped from the message, so `# TODO: fix this` has the message `fix this`. |
| message | What is left of the line. |

Only one TODO is reported per line: the first tag wins and the rest of the line is its message.

## How owners and dates are filled in

You rarely need to write everything. TODO Notifier fills the gaps from `git blame` and a default due date (turn blame off with `--no-blame`).

**Owner.** In order of preference:

1. `@user` or `TAG(user)` written in the comment (shown as the owner source `annotation`).
2. The author of the line according to `git blame`. Map git emails to the handles you want to show with the [`[authors]` table](reference/configuration.md#authors).
3. None: the TODO is *unowned* (a line that is not committed yet, or no git).

**Due date.**

1. The `{date}` written in the comment: an *explicit* date.
2. Otherwise, if `git blame` knows when the line was added: that day plus `default_due_days` (90 by default; `0` turns this off). This is a *default* due date.
3. Otherwise none.

A line that is not committed yet has no author, but counts as added today.

## Overdue versus stale

The difference matters for CI.

| Status | When | Does `--fail-on expired` fail? |
|---|---|---|
| **overdue** | an explicit `{date}` has passed | yes |
| **stale** | a *default* due date has passed (an undated TODO is older than `default_due_days`) | no, only `--fail-on stale` |

Why two words? A default date makes every old, undated TODO late on the first scan. If those failed the build, CI would go red the day a team adopted
the tool. So default dates are reported, but they fail a build only when you opt in with `--fail-on stale`. A date somebody wrote is a promise;
a default date is a nudge. See `--fail-on incomplete` in the [CLI reference](reference/cli.md) for the strict variant that wants an owner and a date on every TODO.

## Only inside comments

By default (`require_comment`), a tag counts only when it is inside a comment of the file's language, which keeps strings and prose out of the results.
`print("TODO list")` is ignored. So is a tag in a docstring (a docstring is a string) and in a Markdown code fence. Use `--no-require-comment` to find
tags anywhere. Files with an extension that is not in the table below are searched everywhere.

`require_comment` is a heuristic, not a parser. Its limits are listed in the `todonotifier.languages` module docstring: nested block comments, heredocs,
Ruby `=begin`/`=end` and a `<script>` block inside HTML can lead to a missed or a spurious TODO in unusual code. It is on in the command line and the
config file, and off in the Python library (`ScanSettings`).

## Supported languages

Languages that TODO Notifier knows the comment syntax of, generated from `todonotifier/languages.py`. The command line scans the `common` preset by
default (see [the list](reference/configuration.md#the-common-extensions)); add others with `--ext` or `extensions`.

--8<-- "site_src/reference/_languages.md"

To add a language, see [Contributing](https://github.com/ashu-tosh-kumar/todo_notifier/blob/main/CONTRIBUTING.md#how-to-add-a-languages-comment-syntax).

## The Python API reads the original format

`scan()` and the command line read the full format above. The older `driver.run` keeps the original format, in which `TODO(owner)` and the colon stay
part of the message. See [Python API](python-api.md).
