#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dev.librarian.cko.database import DEFAULT_CKO_DB, connect, migrate


DEFAULT_WORK_ROOT = Path(
    "/media/abdullah/JARVISDATA/Jarvis_Downloaded_Knowledge/work/mit_ocw_extracted"
)

DEFAULT_CKO_ROOT = Path(
    "/media/abdullah/JARVISDATA/Jarvis_Downloaded_Knowledge/cko/mit_ocw"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_name(text: str) -> str:
    text = text.strip().replace("/", "-")
    text = re.sub(r"[^A-Za-z0-9._ -]+", "_", text)
    text = re.sub(r"\s+", " ", text)
    return text[:160].strip() or "resource"


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def guess_type(title: str, slug: str) -> str:
    t = f"{title} {slug}".lower()

    if "exam" in t and ("sol" in t or "answer" in t):
        return "exam_solution"
    if "exam" in t or "quiz" in t or "final" in t:
        return "exam"
    if "pset" in t or "problem set" in t or "assignment" in t:
        if "sol" in t or "solution" in t:
            return "assignment_solution"
        return "assignment"
    if "lecture" in t or re.search(r"\bl\d{1,2}\b", t):
        return "lecture"
    if "syllabus" in t:
        return "syllabus"
    if "reading" in t:
        return "reading"
    return "resource"


def find_course_root(course_dir: Path) -> Path | None:
    candidates = [p for p in course_dir.rglob("data.json")]
    for c in candidates:
        if (c.parent / "content_map.json").exists() or (c.parent / "resources").exists():
            return c.parent
    for p in course_dir.iterdir():
        if p.is_dir() and (p / "resources").exists():
            return p
    return None


def extract_title(data: dict, fallback: str) -> str:
    for key in ["title", "name", "resource_title"]:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    metadata = data.get("metadata")
    if isinstance(metadata, dict):
        for key in ["title", "name"]:
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return fallback


def collect_static_pdfs(course_root: Path) -> dict[str, Path]:
    static = course_root / "static_resources"
    pdfs = {}
    if not static.exists():
        return pdfs

    for p in static.rglob("*.pdf"):
        pdfs[p.name.lower()] = p

    return pdfs


def find_pdf_for_resource(resource_dir: Path, static_pdfs: dict[str, Path]) -> Path | None:
    data = load_json(resource_dir / "data.json") if (resource_dir / "data.json").exists() else {}
    haystack = json.dumps(data).lower()

    for name, path in static_pdfs.items():
        if name in haystack:
            return path

    slug = resource_dir.name.lower()

    # Match useful MIT filenames like MIT18_06S10_L14.pdf or pset/exam names.
    for name, path in static_pdfs.items():
        if slug in name:
            return path

    return None


def add_cko(
    conn: sqlite3.Connection,
    cko_id: str,
    source: str,
    course: str,
    title: str,
    object_type: str,
    topic: str | None,
) -> None:
    now = utc_now()
    conn.execute(
        """
        INSERT INTO knowledge_objects (
            cko_id, source, course, title, object_type, topic, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(cko_id) DO UPDATE SET
            title=excluded.title,
            object_type=excluded.object_type,
            topic=excluded.topic,
            updated_at=excluded.updated_at
        """,
        (cko_id, source, course, title, object_type, topic, now, now),
    )


def add_representation(
    conn: sqlite3.Connection,
    cko_id: str,
    rep_type: str,
    file_path: Path,
) -> None:
    now = utc_now()
    conn.execute(
        """
        INSERT OR IGNORE INTO representations (
            cko_id, representation_type, file_path, sha256,
            size_bytes, mime_guess, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cko_id,
            rep_type,
            str(file_path),
            sha256_file(file_path),
            file_path.stat().st_size,
            file_path.suffix.lower().lstrip("."),
            now,
        ),
    )


def materialize_representation(src: Path, dest_dir: Path, rep_type: str, clean_title: str) -> Path:
    suffix = src.suffix.lower()
    dest = dest_dir / f"{clean_title}.{rep_type}{suffix}"
    counter = 1

    while dest.exists():
        dest = dest_dir / f"{clean_title}.{rep_type}.{counter}{suffix}"
        counter += 1

    shutil.copy2(src, dest)
    return dest


def build_course(course_dir: Path, cko_root: Path, db_path: Path) -> None:
    migrate(db_path)

    course_name = course_dir.name
    course_root = find_course_root(course_dir)

    if not course_root:
        print(f"[MISS] no course root found: {course_dir}")
        return

    resources = course_root / "resources"
    if not resources.exists():
        print(f"[MISS] no resources dir: {course_root}")
        return

    static_pdfs = collect_static_pdfs(course_root)

    out_course = cko_root / course_name
    out_course.mkdir(parents=True, exist_ok=True)

    manifest = []

    with connect(db_path) as conn:
        for resource in sorted(resources.iterdir()):
            if not resource.is_dir():
                continue

            data_json = resource / "data.json"
            index_html = resource / "index.html"

            if not data_json.exists() and not index_html.exists():
                continue

            data = load_json(data_json) if data_json.exists() else {}
            title = extract_title(data, resource.name.replace("-", " ").title())
            object_type = guess_type(title, resource.name)
            clean_title = safe_name(title)
            cko_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"mit-ocw:{course_name}:{resource.name}"))

            cko_dir = out_course / object_type / safe_name(f"{resource.name} - {clean_title}")
            cko_dir.mkdir(parents=True, exist_ok=True)

            add_cko(
                conn,
                cko_id=cko_id,
                source="MIT OCW",
                course=course_name,
                title=title,
                object_type=object_type,
                topic=None,
            )

            reps = []

            if data_json.exists():
                dest = materialize_representation(data_json, cko_dir, "metadata", "data")
                add_representation(conn, cko_id, "metadata_json", dest)
                reps.append(str(dest))

            if index_html.exists():
                dest = materialize_representation(index_html, cko_dir, "html", "index")
                add_representation(conn, cko_id, "html", dest)
                reps.append(str(dest))

            pdf = find_pdf_for_resource(resource, static_pdfs)
            if pdf:
                dest = materialize_representation(pdf, cko_dir, "pdf", clean_title)
                add_representation(conn, cko_id, "pdf", dest)
                reps.append(str(dest))

            manifest.append(
                {
                    "cko_id": cko_id,
                    "course": course_name,
                    "resource_slug": resource.name,
                    "title": title,
                    "object_type": object_type,
                    "representations": reps,
                }
            )

        conn.commit()

    manifest_path = out_course / "cko_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[OK] Course: {course_name}")
    print(f"[OK] CKOs: {len(manifest)}")
    print(f"[OK] Output: {out_course}")
    print(f"[OK] Manifest: {manifest_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build Canonical Knowledge Objects from MIT OCW extracted courses")
    ap.add_argument("--work-root", default=str(DEFAULT_WORK_ROOT))
    ap.add_argument("--cko-root", default=str(DEFAULT_CKO_ROOT))
    ap.add_argument("--db", default=str(DEFAULT_CKO_DB))
    ap.add_argument("--course", help="Only process matching course directory")
    args = ap.parse_args()

    work_root = Path(args.work_root)
    cko_root = Path(args.cko_root)
    db_path = Path(args.db)

    courses = [p for p in work_root.iterdir() if p.is_dir()]

    if args.course:
        courses = [p for p in courses if args.course in p.name]

    if not courses:
        raise SystemExit("No courses found.")

    for course in courses:
        build_course(course, cko_root, db_path)


if __name__ == "__main__":
    main()
