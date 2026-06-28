from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable

from tools.filesystem.aliases import resolve_path
from tools.action import action

TOOL = {
    "name": "filesystem",
    "version": "1.0",
    "description": "Filesystem operations",
}

def ok(action: str, path: str | Path, data: Any =None) -> dict[str, Any]:
    return {
        "success": True,
        "tool": "filesystem",
        "action": action,
        "path": str(path),
        "result": data,
    }

def fail(action: str, path: str | Path, error: Exception | str) -> dict[str, Any]:
    return {
        "success": False,
        "tool": "filesystem",
        "action": action,
        "path": str(path),
        "error": str(error),
    }


@action("exists")
def exists(path: str | Path) -> dict[str, Any]:
    try:
        p = resolve_path(path)
        return ok("exists", p, {"exists": p.exists()})
    except Exception as e:
        return fail("exists", path, e)

@action("ls")
def ls(path: str | Path) -> dict[str, Any]:
    try:
        p = resolve_path(path)

        if not p.exists():
            return fail("ls", p, "Path does not exist")

        if not p.is_dir():
            return fail("ls", p, "Path is not a directory")

        directories = []
        files = []

        for item in sorted(
            p.iterdir(),
            key=lambda x: (not x.is_dir(), x.name.lower())
        ):
            entry = {
                "name": item.name,
                "path": str(item),
                "is_dir": item.is_dir(),
                "size_bytes": item.stat().st_size if item.is_file() else None,
            }

            if item.is_dir():
                directories.append(entry)
            else:
                files.append(entry)

        return ok("ls", p, {
            "directories": directories,
            "files": files,
            "count": len(directories) + len(files),
        })

    except Exception as e:
        return fail("ls", path, e)


@action("read")
def read(path: str | Path, max_chars: int = 8000) -> dict[str, Any]:
    try:
        p = resolve_path(path)

        if not p.exists():
            return fail("read", p, "File does not exist")

        if not p.is_file():
            return fail("read", p, "Path is not a file")

        text = p.read_text(errors="replace")

        return ok("read", p, {
            "content": text[:max_chars],
            "truncated": len(text) > max_chars,
            "chars_returned": min(len(text), max_chars),
            "chars_total": len(text),
        })

    except Exception as e:
        return fail("read", path, e)


@action("stat")
def stat(path: str | Path) -> dict[str, Any]:
    try:
        p = resolve_path(path)

        if not p.exists():
            return fail("stat", p, "Path does not exist")

        s = p.stat()

        return ok("stat", p, {
            "name": p.name,
            "absolute_path": str(p.resolve()),
            "is_file": p.is_file(),
            "is_dir": p.is_dir(),
            "size_bytes": s.st_size,
            "modified_time": s.st_mtime,
        })

    except Exception as e:
        return fail("stat", path, e)

@action("find")
def find(root: str | Path, pattern: str) -> dict[str, Any]:
    try:
        r = resolve_path(root)

        if not r.exists():
            return fail("find", r, "Root path does not exist")

        if not r.is_dir():
            return fail("find", r, "Root path is not a directory")

        matches = []

        for item in r.rglob(pattern):
            matches.append({
                "name": item.name,
                "path": str(item),
                "is_dir": item.is_dir(),
                "size_bytes": item.stat().st_size if item.is_file() else None,
            })

        return ok("find", r, {
            "pattern": pattern,
            "matches": matches,
            "count": len(matches),
        })

    except Exception as e:
        return fail("find", root, e)


@action("disk_usage")
def disk_usage(path: str | Path) -> dict[str, Any]:
    try:
        p = resolve_path(path)

        if not p.exists():
            return fail("disk_usage", p, "Path does not exist")

        usage = shutil.disk_usage(p)

        return ok("disk_usage", p, {
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
        })

    except Exception as e:
        return fail("disk_usage", path, e)


FILESYSTEM_ACTIONS: dict[str, Callable[..., dict[str, Any]]] = {
    "exists": exists,
    "ls": ls,
    "list": ls,
    "read": read,
    "stat": stat,
    "find": find,
    "disk_usage": disk_usage,
    "du": disk_usage,
}


def execute(action: str, path: str | Path, **kwargs: Any) -> dict[str, Any]:
    action = action.lower()

    func = FILESYSTEM_ACTIONS.get(action)

    if func is None:
        return fail(action, path, f"Unsupported filesystem action: {action}")

    return func(path, **kwargs)
