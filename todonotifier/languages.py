"""This module defines which file types TODO Notifier knows about.

For now it only holds the `"common"` extension preset and the helper that expands it. The detection workstream extends this module with the
comment markers of each language.
"""

COMMON_EXTENSIONS: list[str] = [
    "py",
    "js",
    "jsx",
    "ts",
    "tsx",
    "java",
    "kt",
    "go",
    "rs",
    "rb",
    "php",
    "c",
    "h",
    "cpp",
    "hpp",
    "cs",
    "swift",
    "scala",
    "sh",
    "sql",
    "yaml",
    "yml",
    "toml",
    "html",
    "css",
    "scss",
    "md",
]

COMMON_PRESET_NAME: str = "common"


def expand_extensions(value: str | list[str]) -> list[str]:
    """Expands the `"common"` preset and normalizes a list of file extensions

    Leading dots are stripped, blank entries are dropped and duplicates are removed, keeping the first occurrence. `"common"` (matched case
    insensitively) may be given alone or as an element of a list, and is replaced in place by `COMMON_EXTENSIONS`.

    Args:
        value (str | list[str]): A single extension or preset name, or a list of them. For example `"common"`, `"py"` or `["common", ".proto"]`

    Returns:
        list[str]: Extensions without the leading dot, without duplicates, in order of first appearance
    """
    items: list[str] = [value] if isinstance(value, str) else value
    expanded: list[str] = []
    seen: set[str] = set()

    for item in items:
        names: list[str] = COMMON_EXTENSIONS if item.strip().lower() == COMMON_PRESET_NAME else [item]
        for name in names:
            extension: str = name.strip().lstrip(".")
            if extension and extension not in seen:
                seen.add(extension)
                expanded.append(extension)

    return expanded
