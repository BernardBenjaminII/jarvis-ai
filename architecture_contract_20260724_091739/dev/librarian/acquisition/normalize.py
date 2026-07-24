from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from dev.librarian.acquisition.filter import should_keep
from dev.librarian.acquisition.manifest import append_manifest, sha256_file
from dev.librarian.acquisition.metadata import extract_course_metadata, write_metadata


def extract_zip(zip_path: Path, extract_root: Path) -> Path:
    course_extract_dir = extract_root / zip_path.stem

    if course_extract_dir.exists():
        shutil.rmtree(course_extract_dir)

    course_extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as z:
        z.extractall(course_extract_dir)

    return course_extract_dir


def classify_kind(path: Path) -> str:
    parts = {p.lower() for p in path.parts}
    name = path.name.lower()

    if "exams" in parts or "exam" in name:
        return "exam"
    if "assignments" in parts or "pset" in name or "problem" in name:
        return "assignment"
    if "readings" in parts:
        return "reading"
    if "syllabus" in parts or "syllabus" in name:
        return "syllabus"
    if "lecture" in name or "lecture" in parts:
        return "lecture"
    if path.suffix.lower() == ".json":
        return "metadata"
    if path.suffix.lower() == ".pdf":
        return "pdf"
    return "resource"


def copy_useful_assets(
    course_name: str,
    zip_path: Path,
    extracted_root: Path,
    normalized_root: Path,
    manifest_path: Path,
) -> int:
    count = 0
    course_out = normalized_root / course_name
    course_out.mkdir(parents=True, exist_ok=True)

    metadata = extract_course_metadata(extracted_root)
    metadata["course_name"] = course_name
    metadata["source_zip"] = str(zip_path)
    write_metadata(course_out / "course_metadata.json", metadata)

    for src in extracted_root.rglob("*"):
        if not src.is_file():
            continue

        if not should_keep(src):
            continue

        rel = src.relative_to(extracted_root)

        if rel.parts and rel.parts[0] in {"static_resources", "static_shared"}:
            continue

        dest = course_out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

        digest = sha256_file(dest)
        append_manifest(
            manifest_path,
            {
                "course": course_name,
                "source_zip": str(zip_path),
                "source_path": str(src),
                "normalized_path": str(dest),
                "sha256": digest,
                "size_bytes": str(dest.stat().st_size),
                "kind": classify_kind(dest),
            },
        )
        count += 1

    return count
