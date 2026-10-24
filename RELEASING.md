# Releasing

How to publish a version of `todonotifier`. Tagging and publishing are maintainer steps: the release workflow
([.github/workflows/release.yml](.github/workflows/release.yml)) does the rest. These steps are written for **v2.1.0**;
replace the version for later releases.

## One-time setup

1. **PyPI trusted publisher** (no API token is used or needed): on PyPI, open the `todonotifier` project, then
   *Manage > Publishing* and add a GitHub trusted publisher with these values:
   - Owner: `ashu-tosh-kumar`
   - Repository: `todo_notifier`
   - Workflow name: `release.yml`
   - Environment name: `pypi`
2. **GitHub environment**: in the repository, *Settings > Environments*, create an environment named `pypi`. Optionally
   require a reviewer, so that a publish needs a click.

## Release steps

1. Check that the release branch has what you want: the version in `pyproject.toml` (`2.1.0`) and a `### v2.1.0` section
   in the README changelog (the workflow uses it as the GitHub Release notes). CI must be green. The `version` default in
   [integrations/github-action/action.yml](integrations/github-action/action.yml) must be the same version (a test checks it): the GitHub Action
   installs that release from PyPI, so publish to PyPI before anyone uses the action without `package:`.
2. Merge the roadmap stack into `development`, then merge `development` into `main`. Do the second merge soon after the first: GitHub shows `development`
   (the default branch) to visitors, but the README demo GIF is served from `main`, the docs deploy from `main` (`docs.yml`) and releases are tagged on `main`.
3. Tag the merge commit on `main` and push the tag. (The release workflow runs for every pushed tag that matches `v*`, whatever branch it is on, so tag
   only `main`; the `pypi` environment's required reviewer is the safety net.)

   ```bash
   git checkout main && git pull
   git tag -a v2.1.0 -m "v2.1.0"
   git push origin v2.1.0
   ```

4. Watch the **Release** workflow in the Actions tab. It builds the package, fails if the tag does not match the
   version in `pyproject.toml`, runs `twine check`, publishes to PyPI (approve the `pypi` environment if you
   required a reviewer) and then creates the GitHub Release with the changelog section and the built files.
5. Verify from PyPI in a clean environment:

   ```bash
   pipx install todonotifier==2.1.0 && todonotifier --version
   ```

   It should print `todonotifier 2.1.0`. Also check that the GitHub Release exists and its notes are right.

## After the release

1. **Remove the "release status" notes** that exist only because the release was not published yet:
   `grep -rn "release-note" README.md site_src integrations/github-action/README.md` (the Quickstart admonition, a line each in the README and the
   pre-commit page, and a block in the Action README). Also search the docs for `@v2.1.0` and `rev: v2.1.0` if you released a different version.
2. **GitHub Pages:** *Settings > Pages > Source* must be "GitHub Actions". The docs workflow deploys on every push to `main`. The `github-pages` environment
   (*Settings > Environments*) may restrict deployments to the default branch, which is `development` here: if the deploy job is rejected, add `main` to its
   deployment branches. Check <https://ashu-tosh-kumar.github.io/todo_notifier/> afterwards.
3. **GitHub Action:** `uses: ashu-tosh-kumar/todo_notifier/integrations/github-action@v2.1.0` resolves to the tag from step 3 of the release steps, and the
   action installs the same version from PyPI. Run it once in a scratch repository (`mode: pr` and the pre-commit hook; `pre-commit try-repo` works too).

## If something fails

- **Tag does not match the version**: nothing was published. Delete the tag (`git push --delete origin v2.1.0`,
  `git tag -d v2.1.0`), fix `pyproject.toml`, and tag again.
- **PyPI rejects the upload** (for example a misconfigured trusted publisher): fix the setting and re-run the failed
  job in the Actions tab. A version number can be uploaded to PyPI only once, so never reuse a version that reached PyPI.
- **Publish worked but the GitHub Release failed**: re-run the failed job, or create the release by hand with
  `gh release create v2.1.0 --notes-file <notes> dist/*` (get the notes from
  `python .github/scripts/changelog_section.py v2.1.0`).
