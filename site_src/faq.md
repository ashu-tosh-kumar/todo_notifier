# FAQ

## Shallow clones

**Why does the scan warn that the repository is a shallow clone, or why is every TODO owned by the same person?**

CI systems often check out only the latest commit. `git blame` then attributes every line to that commit, and `--since` cannot find the base commit. The
scan still works, but owners and ages are wrong or missing, and it logs one warning. Check out the full history:

- GitHub Actions: `actions/checkout` with `fetch-depth: 0`.
- GitLab CI: the variable `GIT_DEPTH: "0"`.
- Elsewhere: `git fetch --unshallow`.

If your CI cannot fetch the history, use `--no-blame` and rely on `{date}`s written in the comments: `--fail-on expired` does not need blame.

**"Dubious ownership" or "not a git repository" in a container?** Git refuses repositories owned by another user. Run
`git config --global --add safe.directory "$PWD"` first (the GitHub Action does this for you).

## Monorepos

- **One config at the root** applies to everything. Discovery walks up from the scan path to the git root, so running from a subdirectory finds it.
- **A different config per package:** put a `.todonotifier.toml` in the package and scan it with `todonotifier scan packages/api`. The nearest file wins.
  `--config PATH` forces one.
- **Scan only part of the repository:** pass the paths (`todonotifier scan services/api libs/shared`) or set `paths` in the config file (relative to the
  file). In the GitHub Action, use `working-directory`.
- **Skip generated or vendored code:** `exclude_dirs` and `exclude_files` in the [config file](reference/configuration.md#exclusions) are added to the
  built-in exclusions. Files ignored by git are skipped anyway (`respect_gitignore`).
- **Owners across packages:** map git emails to handles once, in the `[authors]` table.

## Performance

A scan of this repository (about 130 files, 80 TODOs, blame on) takes about 0.3 s. Blame costs about 2 ms per file *that contains a TODO*, because one
`git blame` runs per such file (restricted to the TODO lines, in parallel). Files without TODOs cost no git call, and neither do files git ignores.
Files over 10 MB are read line by line, binary files are skipped, and a minified one-line bundle or a file with tens of thousands of TODOs is scanned in
linear time. If a very large repository is slow:

- Narrow the scan: pass paths, set `extensions`, add `exclude_dirs`.
- `--no-blame` skips git entirely (no owners, ages or default due dates).
- `--since REF` in pull requests keeps the output short, though the scan itself still reads every file.
- In pre-commit, only the staged files are scanned (about 0.4 s for 10 files).

## False positives

- **A tag inside a string, a docstring or a Markdown code fence** is ignored by default (`require_comment`). If you still see a wrong hit, the comment
  detection is a heuristic with [known limits](syntax.md#only-inside-comments); please open an issue with the line.
- **A word that merely contains a tag** (`TODOS`, `TODO_LIST`, `todonotifier`) is not a tag: tags are matched as whole words.
- **A tag in a prose comment** (`# the TODO item is ...`) is reported. Tags are matched anywhere inside a comment; reword the comment or exclude the file.
- **Test fixtures with deliberate TODOs:** add the folder to `exclude_dirs` (this repository does that for `tests`).
- **Missing a TODO?** Check the extension is scanned (`common` is the default; add yours with `--ext`), that the file is not git-ignored
  (`--no-gitignore`), and that the tag is inside a comment (`--no-require-comment` to test).
- **Old undated TODOs are "stale", but CI is green.** That is deliberate: only `--fail-on stale` fails on them. See
  [overdue versus stale](syntax.md#overdue-versus-stale).

## Windows

TODO Notifier is pure Python and is written to be OS independent, and `git` must be on `PATH` for owners and ages. Paths in the results are POSIX paths
with forward slashes. It was developed and tested on Linux only; if you hit a Windows problem, please
[open an issue](https://github.com/ashu-tosh-kumar/todo_notifier/issues/new/choose).

## Which Python versions?

Python 3.10 and newer (CI runs 3.10 to 3.14). Python 3.9 users stay on release 1.x (1.4.0).

## Privacy

**Nothing leaves your machine unless you configure a notifier.** A scan reads your files and runs `git` locally. There is no telemetry, no account and no
network call. The only network traffic is what you set up yourself:

- a Slack, Teams or webhook URL you configure, which receives the digest (TODO texts, file names and owners);
- an SMTP server you configure, for email;
- a repository URL that you hand to the Python API to clone (`ConnectMethod.GIT_CLONE`; the command line never clones);
- your CI system, if you run it there.

Webhook URLs and passwords are never stored in config files: you name an environment variable. They are never written to logs or error messages either.

## Can it create issues from TODOs?

No. For that, use a tool such as [todo-to-issue-action](https://github.com/alstr/todo-to-issue-action); it combines well with this one. See
[How it compares](comparison.md).

## Where do I report a bug or ask a question?

[Open an issue](https://github.com/ashu-tosh-kumar/todo_notifier/issues/new/choose) for bugs and feature requests, and use
[Discussions](https://github.com/ashu-tosh-kumar/todo_notifier/discussions) for questions and ideas. Security problems go through
[SECURITY.md](https://github.com/ashu-tosh-kumar/todo_notifier/blob/main/SECURITY.md).
