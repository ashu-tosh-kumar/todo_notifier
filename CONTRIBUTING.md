# Contributing to TODO Notifier

Thank you for helping! TODO Notifier is a small Python library and command line tool that finds `TODO`/`FIXME` comments, works out who owns them and when they are due, and tells you about the overdue ones. Bug reports, ideas, docs fixes and code are all welcome.

New here? Look for issues labelled [`good first issue`](https://github.com/ashu-tosh-kumar/todo_notifier/labels/good%20first%20issue). Questions and ideas that are not bugs belong in [Discussions](https://github.com/ashu-tosh-kumar/todo_notifier/discussions). Security problems go through [SECURITY.md](SECURITY.md), not a public issue.

## Development setup

You need Git and Python 3.10 or newer. 3.10 is the minimum supported version, so develop on it to catch accidental use of newer features (CI runs 3.10 to 3.14).

```bash
git clone https://github.com/ashu-tosh-kumar/todo_notifier.git
cd todo_notifier

# Optional: a virtual environment on Python 3.10 (pyenv shown; any tool works)
pyenv virtualenv 3.10 todonotifier

pip install poetry
poetry install --with dev     # the package plus black, flake8, isort, pytest, coverage, pdoc, ...
poetry run pre-commit install # run the hooks on every commit

poetry run todonotifier scan . # try the command line tool on this repository
```

Use `poetry run <command>` for everything below, or activate the environment first.

## Running the checks

CI runs exactly these on every pull request, on Python 3.10 to 3.14. Run them before you push:

```bash
poetry run pytest -q                                                   # tests
poetry run coverage run -m pytest && poetry run coverage report -m     # 100% line coverage is required
poetry run black --check .                                             # formatting (line length 160)
poetry run isort --check-only .                                        # import order
poetry run flake8 . --config ./tox.ini                                 # lint
poetry run todonotifier scan . --fail-on expired                       # this repository checks its own TODOs
```

To fix formatting instead of only checking it: `poetry run black .` and `poetry run isort .`.

### Pre-commit hooks

`pre-commit install` (see above) runs black, isort, flake8 and a few hygiene hooks (a `requirements.txt` fixer, leftover debug statements, AWS credentials and private keys) on the files you commit. `poetry run pre-commit run --all-files` runs them on everything. The hooks pin the same black, flake8 and isort versions as `poetry.lock`, so they should never change a file that CI accepts. If you bump one of those tools, bump both places.

### Tests and coverage

- Tests live in `tests/` as `unittest.TestCase` classes and run with pytest. A new module gets a `tests/test_<module>.py`.
- **Every line of the `todonotifier` package must be covered** (`fail_under = 100` in `pyproject.toml`). A new feature or a bug fix comes with tests; a fix should include a test that fails without it. Use `# pragma: no cover` only for code that cannot run in tests, with a comment that says why.
- Never touch the network or a real mail server in tests: mock `todonotifier.notifier._post_json` and `smtplib`. Tests that need git build a temporary repository with fixed `GIT_AUTHOR_*` and `GIT_COMMITTER_*` variables and never write outside a temporary directory. Do not make a test depend on today's date: use explicit past dates such as `{2020-01-01}`, or pass `today`.
- Some outputs are compared with files in `tests/snapshots/`. After an intended change, run `UPDATE_SNAPSHOTS=1 poetry run pytest tests/test_formatters.py tests/test_digest.py tests/test_notifier.py` and review the diff before you commit it.
- `tests/sample_test_file*.py` and `tests/mocks.py` are fixtures whose TODO contents are asserted on elsewhere. Edit them with care.

## Code style

- Python 3.10 syntax is fine (`X | None`, `list[str]`); do not modernise existing code just for the sake of it.
- Type hints on all arguments, return values and variables. Google-style docstrings. Match the comment density of the surrounding code.
- Keep runtime dependencies minimal: standard library first. A new dependency needs a strong reason.
- Never put secrets in config files, logs or exception messages. Use `subprocess` with a list of arguments (never `shell=True`) and a timeout on every subprocess and network call.
- Keep changes small and focused. [AGENTS.md](AGENTS.md) describes the architecture and the gotchas in more detail (it is written for AI agents, but it is the best map of the code).

## Commit messages and pull requests

Use [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): summary`, in the imperative mood, for example `feat(cli): add --since to notify` or `fix(languages): handle Ruby block comments`. Common types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`.

Open pull requests against the `development` branch (`main` only receives releases). Fill in the checklist of the pull request template: tests, a changelog bullet under the unreleased version in the README, and docs. CI must be green.

## How to add a language's comment syntax

The `require_comment` option (on by default in the command line tool) counts a tag only when it sits inside a comment. The syntax of each language is in `todonotifier/languages.py`.

1. Add the extension, without the dot, to `COMMENT_SYNTAX` with a `CommentSyntax`: `line_markers` (for example `("//",)`), `block_comments` as `(open, close)` pairs, `multiline_strings` for string literals that can span lines, and `spaced_line_markers=True` when `#` only starts a comment after whitespace (YAML and shell). Reuse the shared values such as `_HASH` or `_C_LIKE` when they fit.
2. If the language should be scanned by default, add the extension to `COMMON_EXTENSIONS` and to the `common` list in the README's configuration section.
3. Add `tests/fixtures/languages/sample.<ext>` with real TODOs in comments **and decoys** (a tag in a string, in a URL, in prose). The fixture's TODOs are asserted by line number, so add its expected items to `EXPECTED_FIXTURE_ITEMS` in `tests/test_languages.py`.
4. Update the list of known limits in the module docstring of `languages.py` if the new syntax has quirks the lexer does not handle.
5. Run the full checks, and note the new language in the README changelog.

The lexer is a heuristic, not a parser. Keep it linear in the length of a line.

## How to add a notifier

Notifiers receive the scan result and send it somewhere. They live in `todonotifier/notifier.py`.

1. Subclass `DigestNotifier` (or `_HttpNotifier` when you only POST JSON to a URL) and override `notify_result(result, reports)`. Build the message from `self.make_digest(result)` so every channel shows the same sections. For an HTTP service, set `label` and implement `_result_payload` and `_reports_payload`, and the retries, timeouts and secret handling come for free.
2. Escape untrusted text (TODO messages and file names) for your channel.
3. Never let a secret reach a log message, an exception message or `repr()`. Raise `NotificationError` for delivery failures and `NotifierConfigError` for bad settings.
4. To make it configurable from the config file: add an entry to `_NOTIFIER_SCHEMA` in `todonotifier/settings_file.py` (secrets are only ever the *names* of environment variables, with keys ending in `_env`) and build it in `build_notifiers` in `notifier.py`. Document the table in the README's "Notifications" section.
5. Test it in `tests/test_notifier.py` with the network mocked, add a snapshot under `tests/snapshots/` if it has a payload, and add a test that the secret does not appear in logs or errors (see `TestNoSecretsInLogsOrErrors`).

Anyone can also write a private notifier without touching this repository: subclass `BaseNotifier` and pass an instance in a custom config (see "Custom notifiers" in the README).

## License

By contributing you agree that your contributions are licensed under the [MIT License](LICENSE).
