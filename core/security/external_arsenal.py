"""Read-only discovery of JARVIS external reference libraries."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_ROOT = Path("/mnt/jarvis_arsenal")

LIBRARIES = {
    "payloadsallthethings": (
        "payloads/PayloadsAllTheThings"
    ),
    "seclists": "wordlists/SecLists",
    "fuzzdb": "payloads/fuzzdb",
    "assetnote": "wordlists/assetnote",
    "nuclei_templates": "templates/nuclei",
    "trickest": "wordlists/trickest",
}


def snapshot(root: Path = DEFAULT_ROOT) -> dict:
    root = Path(root)

    # A directory alone is not evidence that the SSD is mounted.
    mounted = root.is_mount()
    libraries = []

    for name, relative in LIBRARIES.items():
        path = root / relative
        available = mounted and path.is_dir()

        libraries.append({
            "id": name,
            "available": available,
            "relative_path": relative,
        })

    return {
        "state": "ready" if (
            mounted and all(
                item["available"] for item in libraries
            )
        ) else "offline" if not mounted else "degraded",
        "mounted": mounted,
        "root": str(root),
        "libraries": libraries,
        "execution_authorized": False,
        "inspection_mode": "metadata_only",
    }


def search(
    query: str,
    root: Path = DEFAULT_ROOT,
    limit: int = 30,
) -> dict:
    root = Path(root)
    query = query.strip().casefold()
    limit = max(1, min(int(limit), 50))

    if not query or len(query) > 100:
        raise ValueError("Query must contain 1-100 characters")

    status = snapshot(root)

    if status["state"] != "ready":
        return {
            "state": status["state"],
            "results": [],
            "truncated": False,
        }

    results = []
    inspected = 0
    max_inspected = 30000

    for library_id, relative in LIBRARIES.items():
        base = root / relative

        for directory, dirs, files in os.walk(
            base, followlinks=False
        ):
            dirs[:] = sorted(
                d for d in dirs
                if d != ".git"
                and not Path(directory, d).is_symlink()
            )

            for filename in sorted(files):
                inspected += 1

                if inspected > max_inspected:
                    return {
                        "state": "ready",
                        "results": results,
                        "truncated": True,
                    }

                path = Path(directory) / filename

                if path.is_symlink() or not path.is_file():
                    continue

                relative_path = path.relative_to(base).as_posix()

                if query not in relative_path.casefold():
                    continue

                results.append({
                    "library": library_id,
                    "path": relative_path,
                    "name": filename,
                })

                if len(results) >= limit:
                    return {
                        "state": "ready",
                        "results": results,
                        "truncated": True,
                    }

    return {
        "state": "ready",
        "results": results,
        "truncated": False,
    }
