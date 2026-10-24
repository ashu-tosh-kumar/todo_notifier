# Demo of TODO Notifier for the README: `todonotifier scan`, `--fail-on expired` with its exit code, and `--format github`.
#
# Regenerate the GIF (a maintainer step) with Charm's VHS (https://github.com/charmbracelet/vhs), from the repository root:
#
#     pipx install todonotifier        # or `pip install .`: the `todonotifier` command must be on PATH
#     vhs assets/demo.tape             # writes assets/demo.gif
#
# VHS needs ttyd and ffmpeg on PATH. The tape builds its own small sample repository in a temporary directory (hidden from the recording), so it
# does not touch your project. Output paths are relative to the directory you run `vhs` in.

Output assets/demo.gif

Set Shell "bash"
Set FontSize 18
Set Width 1200
Set Height 620
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 45ms

# Setup, not recorded: a sample repository with three authors' TODOs, one with an expired date
Hide
Type 'export PS1="$ " && cd $(mktemp -d) && git init -q -b main && mkdir src' Enter
Type "printf 'def main():\n    # TODO {2020-04-01} @alice Remove the legacy path\n    return 0\n' > src/app.py" Enter
Type "printf '# FIXME Rewrite this module\ndef parse(text):\n    return text.split()\n' > src/old.py" Enter
Type "printf 'def lookup(key):\n    # TODO(carol) {2030-01-15}: Cache the lookup\n    return key\n' > src/api.py" Enter
Type "git add . && GIT_AUTHOR_DATE=2020-01-10T10:00:00 GIT_COMMITTER_DATE=2020-01-10T10:00:00 git -c user.name=alice -c user.email=a@example.com commit -qm app" Enter
Type "printf '\n# HACK Think about naming\n' >> src/api.py && git add . && git -c user.name=bob -c user.email=b@example.com commit -qm api" Enter
Ctrl+L
Show

Type "todonotifier scan ." Enter
Sleep 4s

Ctrl+L
Type "todonotifier scan . --fail-on expired; echo exit code: $?" Enter
Sleep 4s

Ctrl+L
Type "todonotifier scan . --format github" Enter
Sleep 5s
