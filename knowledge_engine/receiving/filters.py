from pathlib import Path

IGNORE_FILENAMES = {
    ".DS_Store",
    "Thumbs.db",
    "Desktop.ini",
    ".directory",
}

IGNORE_PREFIXES = {
    "._",
}

IGNORE_SUFFIXES = {
    "~",
    ".tmp",
    ".temp",
    ".part",
    ".download",
    ".swp",
    ".pyc",
}

IGNORE_DIRECTORIES = {
    "__pycache__",
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    "build",
    "dist",
    "bin",
    "obj",
}


def should_ignore(path: Path) -> tuple[bool, str]:

    name = path.name

    if name in IGNORE_FILENAMES:
        return True, "ignored filename"

    for prefix in IGNORE_PREFIXES:
        if name.startswith(prefix):
            return True, f"ignored prefix '{prefix}'"

    for suffix in IGNORE_SUFFIXES:
        if name.endswith(suffix):
            return True, f"ignored suffix '{suffix}'"

    for part in path.parts:
        if part in IGNORE_DIRECTORIES:
            return True, f"ignored directory '{part}'"

    return False, ""
