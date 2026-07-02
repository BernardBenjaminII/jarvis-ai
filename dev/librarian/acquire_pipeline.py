#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from dev.librarian.acquisition.normalize import copy_useful_assets, extract_zip


DEFAULT_STAGED = Path(
    "/media/abdullah/JARVISDATA/Jarvis_Downloaded_Knowledge/staged/mit_targeted/ocw_courses"
)

DEFAULT_WORK = Path(
    "/media/abdullah/JARVISDATA/Jarvis_Downloaded_Knowledge/work/mit_ocw_extracted"
)

DEFAULT_NORMALIZED = Path(
    "/media/abdullah/JARVISDATA/Jarvis_Downloaded_Knowledge/normalized/mit_ocw"
)

DEFAULT_MANIFEST = Path(
    "/media/abdullah/JARVISDATA/Jarvis_Downloaded_Knowledge/normalized/mit_ocw/normalized_manifest.csv"
)


def process_zip(zip_path: Path, work_root: Path, normalized_root: Path, manifest_path: Path) -> None:
    course_name = zip_path.parent.name
    print(f"\n[COURSE] {course_name}")
    print(f"[ZIP   ] {zip_path}")

    extracted = extract_zip(zip_path, work_root / course_name)
    print(f"[EXTRACTED] {extracted}")

    count = copy_useful_assets(
        course_name=course_name,
        zip_path=zip_path,
        extracted_root=extracted,
        normalized_root=normalized_root,
        manifest_path=manifest_path,
    )

    print(f"[KEPT] {count} useful assets")


def main() -> None:
    ap = argparse.ArgumentParser(description="JARVIS knowledge acquisition normalization pipeline")
    ap.add_argument("--staged", default=str(DEFAULT_STAGED))
    ap.add_argument("--work", default=str(DEFAULT_WORK))
    ap.add_argument("--normalized", default=str(DEFAULT_NORMALIZED))
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    ap.add_argument("--course", help="Process only one course directory name")
    args = ap.parse_args()

    staged = Path(args.staged)
    work = Path(args.work)
    normalized = Path(args.normalized)
    manifest = Path(args.manifest)

    if not staged.exists():
        raise SystemExit(f"Staged directory not found: {staged}")

    zips = sorted(staged.glob("*/**/*.zip"))

    if args.course:
        zips = [z for z in zips if args.course in str(z)]

    if not zips:
        raise SystemExit("No ZIP files found.")

    print(f"[FOUND] {len(zips)} ZIP files")

    for z in zips:
        process_zip(z, work, normalized, manifest)

    print(f"\n[DONE]")
    print(f"Normalized: {normalized}")
    print(f"Manifest:   {manifest}")


if __name__ == "__main__":
    main()
