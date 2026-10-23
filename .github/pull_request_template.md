## What and why

<!-- A short description of the change and the problem it solves. Link the issue: "Closes #123". -->

## Checklist

- [ ] Tests added or updated (`poetry run pytest -q`), and the package is still at 100% coverage (`poetry run coverage run -m pytest && poetry run coverage report -m`)
- [ ] `black --check .`, `isort --check-only .` and `flake8 . --config ./tox.ini` pass
- [ ] Changelog: a bullet under the unreleased version in the `README.md` changelog (not needed for tests- or CI-only changes)
- [ ] Docs updated if behaviour, flags or config keys changed (README, docstrings, `AGENTS.md`)
- [ ] No secrets, tokens or webhook URLs in the code, tests, logs or examples
- [ ] Commits follow Conventional Commits (`feat(scope): ...`, `fix(scope): ...`)
