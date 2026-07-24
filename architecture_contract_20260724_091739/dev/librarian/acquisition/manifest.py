from __future__ import annotations

import csv
import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def append_manifest(manifest_path: Path, row: dict[str, str]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not manifest_path.exists()

    fields = [
        "course",
        "source_zip",
        "source_path",
        "normalized_path",
        "sha256",
        "size_bytes",
        "kind",
    ]

    with manifest_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if is_new:
            writer.writeheader()
        writer.writerow(row)
