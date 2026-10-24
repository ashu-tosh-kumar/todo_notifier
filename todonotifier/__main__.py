"""Lets `python -m todonotifier` run the command line, the same as the `todonotifier` command"""

from todonotifier.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
