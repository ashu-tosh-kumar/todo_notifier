"""Print the changelog section of one version from the README, for the GitHub Release notes.

Usage: python .github/scripts/changelog_section.py v2.1.0 [README.md]

The section starts at the heading ``### v2.1.0`` (a suffix such as `` (Unreleased)`` is allowed) and ends
before the next ``###`` heading or horizontal rule. The script exits with 1 if the section is missing or empty.
"""

import re
import sys
from pathlib import Path
from typing import List


def extract_section(readme: str, tag: str) -> str:
    """Return the body of the changelog section of `tag`.

    Args:
        readme (str): Text of the README.
        tag (str): Version tag with the leading ``v``, for example ``v2.1.0``.

    Returns:
        str: The section without its heading, stripped. Empty if there is no such section.
    """
    heading: "re.Pattern[str]" = re.compile(rf"^### {re.escape(tag)}(\s.*)?$")
    end: "re.Pattern[str]" = re.compile(r"^(### |---\s*$)")
    body: List[str] = []
    inside: bool = False
    for line in readme.splitlines():
        if inside and end.match(line):
            break
        if inside:
            body.append(line)
        elif heading.match(line):
            inside = True
    return "\n".join(body).strip()


def main(argv: List[str]) -> int:
    """Print the section named by the command line arguments.

    Args:
        argv (List[str]): The tag and, optionally, the path of the README.

    Returns:
        int: Exit code, 0 on success.
    """
    if not 1 <= len(argv) <= 2:
        print(__doc__, file=sys.stderr)
        return 2
    tag: str = argv[0]
    readme: Path = Path(argv[1] if len(argv) == 2 else "README.md")
    section: str = extract_section(readme.read_text(encoding="utf-8"), tag)
    if not section:
        print(f"No changelog section '### {tag}' (or it is empty) in {readme}", file=sys.stderr)
        return 1
    print(section)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
