# Good first issues (ready to paste)

Creating GitHub issues is a maintainer action, so these are drafted here. For each one: create a new issue, paste the **title** and the **body** (everything under the heading, up to the next `---`), and add the labels listed. Create the label `good first issue` first if it does not exist (GitHub creates it in new repositories; a colour such as `#7057ff` is conventional). Every item comes from a real follow-up or a "left unfixed on purpose" entry in [PROGRESS.md](PROGRESS.md), and was checked against the code on the `roadmap/1.4-discoverability` branch.

Every issue ends with the same pointer: read [CONTRIBUTING.md](../CONTRIBUTING.md), run the checks, keep 100% coverage.

| # | Title | Labels | Size |
|---|---|---|---|
| 1 | Support Ruby `=begin` / `=end` block comments | `good first issue`, `enhancement`, `detection` | S |
| 2 | Add Lua to the `common` extension preset and cover its comment syntax with a fixture | `good first issue`, `enhancement`, `detection` | S |
| 3 | Mark default due dates in the `DUE` column of the table output | `good first issue`, `enhancement`, `cli` | S |
| 4 | Handle Ctrl-C without a Python traceback | `good first issue`, `bug`, `cli` | S |
| 5 | Hint to git-ignore `.report/` after `todonotifier report` | `good first issue`, `enhancement`, `cli` | S |
| 6 | Align the table output for wide (CJK) characters | `good first issue`, `bug`, `cli` | S |
| 7 | Add `notify --only-if-items` to skip empty digests | `good first issue`, `enhancement`, `notifications` | S |
| 8 | Document the directories that are skipped by default | `good first issue`, `documentation` | XS |
| 9 | Merge `@alice` annotations and blame names `Alice` with owner aliases | `good first issue`, `enhancement`, `owners` | M (stretch) |

---

## 1. Support Ruby `=begin` / `=end` block comments

**Labels:** `good first issue`, `enhancement`, `detection`

### Background

`todonotifier scan` counts a tag only when it sits inside a comment (the `require_comment` option, on by default in the command line tool). The comment syntax of each language is a table in `todonotifier/languages.py` (`COMMENT_SYNTAX`). For Ruby (`.rb`) only the `#` line comment is known, so a TODO inside a block comment is missed:

```ruby
=begin
TODO {2030-01-01} @alice rewrite this module
=end
```

The module docstring of `languages.py` lists "Ruby `=begin`/`=end`" under "Not handled".

### What to do

Teach the comment lexer that, in Ruby, a block comment starts with `=begin` **at the start of a line** and ends with `=end` at the start of a line. Because the markers must be at column 0, the existing `block_comments` pairs (which match anywhere on the line) are not enough: add a small, backwards compatible option to `CommentSyntax` (for example `line_start_block_comments`), handle it in `CommentLexer`, and use it for `rb`.

### Acceptance criteria

- [ ] A tag inside `=begin ... =end` is reported, with the right line number; a tag on the `=begin` line itself is handled sensibly (a comment, because Ruby allows text after `=begin`).
- [ ] `x = "=begin"` or an indented `  =begin` is **not** treated as a block comment start.
- [ ] Tags after the closing `=end` and ordinary `#` comments keep working.
- [ ] `tests/fixtures/languages/` gets a `sample.rb` with real TODOs and decoys, and `EXPECTED_FIXTURE_ITEMS` in `tests/test_languages.py` lists its items.
- [ ] The "Not handled" list in the `languages.py` module docstring no longer mentions Ruby.
- [ ] The lexer stays linear in the length of a line (see the note in AGENTS.md); coverage stays at 100%.
- [ ] A bullet in the README changelog.

### Hints

`CommentLexer` and `CommentIndex` in `todonotifier/languages.py`; existing tests in `tests/test_languages.py`.

New here? Read [CONTRIBUTING.md](../CONTRIBUTING.md) ("How to add a language's comment syntax"), run the checks listed there, and keep coverage at 100%.

---

## 2. Add Lua to the `common` extension preset and cover its comment syntax with a fixture

**Labels:** `good first issue`, `enhancement`, `detection`

### Background

`COMMENT_SYNTAX` in `todonotifier/languages.py` already knows Lua (`--` line comments and `--[[ ... ]]` block comments), but:

1. `lua` is not in `COMMON_EXTENSIONS`, so `todonotifier scan .` does not look at `.lua` files unless the user adds `extensions = ["common", "lua"]`;
2. there is no `tests/fixtures/languages/sample.lua`, so the syntax is not covered by the language fixtures;
3. Lua's *level* long brackets (`--[=[ ... ]=]`, `--[==[ ... ]==]`) are not recognised, and a TODO inside them is missed.

### What to do

Add `lua` to `COMMON_EXTENSIONS` (and to the list printed in the README configuration section), add a fixture with real TODOs and decoys (a tag inside a string, inside `[[ long string ]]`, in a URL), and support level-N long brackets for block comments.

### Acceptance criteria

- [ ] `expand_extensions("common")` contains `lua`, and the README's description of the `common` preset lists it.
- [ ] `tests/fixtures/languages/sample.lua` exists; its items are listed in `EXPECTED_FIXTURE_ITEMS` (`tests/test_languages.py`) and pass.
- [ ] `--[==[ TODO ... ]==]` is a comment; a `[[ TODO ]]` long **string** is not.
- [ ] Existing tests that assert the size or content of the preset are updated; coverage stays at 100%.
- [ ] A bullet in the README changelog.

New here? Read [CONTRIBUTING.md](../CONTRIBUTING.md) ("How to add a language's comment syntax"), run the checks listed there, and keep coverage at 100%.

---

## 3. Mark default due dates in the `DUE` column of the table output

**Labels:** `good first issue`, `enhancement`, `cli`

### Background

A TODO without a `{date}` gets a *default* due date: the day it was added (from `git blame`) plus `default_due_days` (90 by default). The table output shows it like an explicit date:

```text
src/misc.py:1   TODO  carol  2027-01-21 due in 90d   Think about naming
```

The JSON and `github` outputs say that the date is a default (`due_source`), but the table does not, so a reader cannot tell a deadline someone chose from one the tool made up.

### What to do

In `describe_due` (`todonotifier/formatters.py`) mark default dates, for example `2027-01-21~ due in 90d` or `due in 90d (default)`. Pick one short form, explain it in the table's footer or the README ("Output formats") and keep explicit dates unchanged. Stale items (`stale 120d`) are always default dates, so they need no extra marker.

### Acceptance criteria

- [ ] A not-yet-due *default* date is visibly different from an explicit one in `--format table`; explicit dates, overdue and stale texts are unchanged.
- [ ] The marker is explained in the README and in `todonotifier scan --help` if it mentions the table.
- [ ] Snapshots are updated on purpose (`UPDATE_SNAPSHOTS=1 pytest tests/test_formatters.py`) and the diff is small and reviewed; the README example output is updated to match.
- [ ] Other formats (`json`, `github`, `markdown`, `sarif`) do not change.
- [ ] Coverage stays at 100%; a README changelog bullet.

New here? Read [CONTRIBUTING.md](../CONTRIBUTING.md), run the checks listed there, and keep coverage at 100%.

---

## 4. Handle Ctrl-C without a Python traceback

**Labels:** `good first issue`, `bug`, `cli`

### Background

Pressing Ctrl-C during a long scan (a big repository with `git blame`) ends with Python's `KeyboardInterrupt` traceback. A command line tool should stop quietly. The convention is exit code 130 (128 + SIGINT) and, at most, a one-line message.

### What to do

In `main(argv)` in `todonotifier/cli.py` (it never calls `sys.exit`, it returns the exit code), catch `KeyboardInterrupt` next to the existing error handling and return 130 after printing a short message such as `Interrupted.` to stderr. Make sure no temporary files or half-written reports are left behind, and document the code in `--help` and the README's "Exit codes" table.

### Acceptance criteria

- [ ] A test makes the scan raise `KeyboardInterrupt` (patch `todonotifier.cli.scan` or similar) and asserts: return value 130, a one-line message on stderr, no traceback.
- [ ] `--help` epilog and the README "Exit codes" section mention 130.
- [ ] Other exit codes (0 to 3) are unchanged.
- [ ] Coverage stays at 100%; a README changelog bullet.

New here? Read [CONTRIBUTING.md](../CONTRIBUTING.md), run the checks listed there, and keep coverage at 100%.

---

## 5. Hint to git-ignore `.report/` after `todonotifier report`

**Labels:** `good first issue`, `enhancement`, `cli`

### Background

`todonotifier report` writes HTML files into `.report/` in the project (`--output` changes the folder). In this repository `.report/` is git-ignored, but in the repository of a new user it is not, so `git status` suddenly shows untracked files and one `git add .` later they are committed.

### What to do

After writing reports with the **default** output folder, when the folder is inside a git work tree and `git check-ignore` says it is not ignored, print one hint to stderr, for example `Tip: add ".report/" to .gitignore`. Do not edit `.gitignore` for the user, print nothing when the folder is already ignored, outside a git repository, or when `--output` is given. Use `subprocess` with a list of arguments and a timeout (see `todonotifier/git_meta.py` for the pattern; it never raises).

### Acceptance criteria

- [ ] A test with a temporary git repository (fixed `GIT_*` variables, see `tests/test_git_meta.py`): hint shown when not ignored, not shown when ignored, not shown outside git.
- [ ] Missing `git`, a timeout or a non-repository never fails the command.
- [ ] `--quiet` (if it exists) silences the hint; the exit code is unchanged.
- [ ] Coverage stays at 100%; a README changelog bullet.

New here? Read [CONTRIBUTING.md](../CONTRIBUTING.md), run the checks listed there, and keep coverage at 100%.

---

## 6. Align the table output for wide (CJK) characters

**Labels:** `good first issue`, `bug`, `cli`

### Background

`--format table` pads columns with `str.ljust`, which counts characters, not terminal cells. A message, owner or file name with Chinese, Japanese or Korean characters (two cells wide) pushes the following columns out of line:

```text
LOCATION       TAG   OWNER  DUE                     MESSAGE
src/a.py:1     TODO  山田   2026-05-03 due in 2d    ...
```

### What to do

In `todonotifier/formatters.py` (the table code that computes `widths` and calls `ljust`), measure and pad by display width using `unicodedata.east_asian_width` (`"W"` and `"F"` are two cells; combining marks are zero). Keep it in the standard library; do not add a dependency such as `wcwidth`.

### Acceptance criteria

- [ ] A helper (for example `display_width(text)`) and a `pad(text, width)` that use it, with unit tests for ASCII, CJK, combining characters and the empty string.
- [ ] A table test with a CJK owner and message where every column starts at the same cell.
- [ ] ASCII-only output is byte for byte unchanged (the existing snapshots pass without editing).
- [ ] Coverage stays at 100%; a README changelog bullet.

New here? Read [CONTRIBUTING.md](../CONTRIBUTING.md), run the checks listed there, and keep coverage at 100%.

---

## 7. Add `notify --only-if-items` to skip empty digests

**Labels:** `good first issue`, `enhancement`, `notifications`

### Background

`todonotifier notify` always sends a message, even when the (filtered) result has no TODOs. For a weekly Slack digest that is sometimes wanted ("0 TODOs, all clear"), but for a daily job it is noise. (With `--since`, nothing is sent when no TODO is on a changed line; this issue is about the other case.)

### What to do

Add a flag `--only-if-items` to `todonotifier notify` (in `todonotifier/cli.py`). When the scan result has no items, log one INFO line, send nothing and exit 0. Without the flag nothing changes. Document it in `--help` and the README "Notifications" section.

### Acceptance criteria

- [ ] With the flag and an empty result: no notifier is called, exit code 0, one INFO message.
- [ ] With the flag and at least one TODO: the notifiers are called as before.
- [ ] Without the flag: behaviour unchanged (empty digests are still sent).
- [ ] Tests mock `todonotifier.notifier._post_json` (never the real network); coverage stays at 100%; a README changelog bullet.

New here? Read [CONTRIBUTING.md](../CONTRIBUTING.md), run the checks listed there, and keep coverage at 100%.

---

## 8. Document the directories that are skipped by default

**Labels:** `good first issue`, `documentation`

### Background

`DEFAULT_EXCLUDE_DIRS` (in `todonotifier/constants.py`) skips directories with names such as `build`, `dist`, `var`, `wheels`, `htmlcov` and `__pycache__`, and others, **even in a git repository**. A first-time user whose TODOs live in one of those folders sees none and gets no hint about why. Nothing in the README lists them.

### What to do

Add a short section ("What is skipped by default") to the README's configuration section: the built-in excluded directory names and patterns, the fact that `exclude_dirs` / `exclude_files` in the config file are **added** to them, and the way to scan a folder that is skipped (for example by naming it as a PATH argument, if that works; verify by running it, and say so if not). Read the list from the code so it is exact. Optionally, add a test that fails when a name is added to `DEFAULT_EXCLUDE_DIRS` without being listed in the README.

### Acceptance criteria

- [ ] The README lists every name and pattern of `DEFAULT_EXCLUDE_DIRS` and `DEFAULT_EXCLUDE_FILES`, and explains how to add exclusions.
- [ ] The text says how to get TODOs from a skipped folder, verified with a real command.
- [ ] (Optional) a test keeps the README list and the constants in sync.
- [ ] A README changelog bullet is not needed for a docs-only change.

New here? Read [CONTRIBUTING.md](../CONTRIBUTING.md) and run the checks listed there.

---

## 9. Merge `@alice` annotations and blame names `Alice` with owner aliases

**Labels:** `good first issue`, `enhancement`, `owners` (a stretch for a first contribution; ask in the issue before you start)

### Background

An owner comes from the annotation (`TODO @alice ...`, `TODO(alice): ...`) or from `git blame` (the author name, e.g. `Alice`). The config table `[tool.todonotifier.authors]` maps git **emails** to a handle, but only blame results go through it. So the same person can appear as two owners, `alice` and `Alice`, in the digest and the reports.

### What to do

Make owner names comparable. A proposal to discuss in the issue: let the existing `authors` table also be applied to annotation handles (case-insensitively), or add a small `owner_aliases` table (`"alice" = "Alice Example"`), and use one normalised owner everywhere (`TodoItem.author`, digest grouping, table, JSON). Keep the original spelling available if you can (do not lose information that JSON consumers see today), and keep `schema_version` unchanged unless a field is removed or changes meaning.

### Acceptance criteria

- [ ] Design agreed in the issue comments before coding (config key name, precedence, case rules).
- [ ] With the alias configured, `@alice` and a blamed `Alice` are **one** owner in the digest sections and the table.
- [ ] Without the alias, output is unchanged.
- [ ] Config validation accepts the new key with a helpful error for a wrong type; the README configuration example and `todonotifier init` starter document it (the starter must not contain a default tag, see AGENTS.md).
- [ ] Tests in `tests/test_git_meta.py`, `tests/test_digest.py` and `tests/test_settings_file.py`; the JSON Schema still validates; coverage stays at 100%; a README changelog bullet.

New here? Read [CONTRIBUTING.md](../CONTRIBUTING.md), run the checks listed there, and keep coverage at 100%.
