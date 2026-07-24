from __future__ import annotations

import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from core.knowledge_catalog.config import DEFAULT_CATALOG_DB, DEFAULT_KNOWLEDGE_ROOT
from core.knowledge_catalog.database import connect, migrate


DOC_EXT = {".pdf", ".epub", ".txt", ".md", ".html", ".htm", ".xml"}
DATA_EXT = {".tif", ".tiff", ".img", ".dem", ".hgt", ".csv", ".geojson", ".json", ".zip", ".7z", ".tar", ".gz"}
ZIM_EXT = {".zim"}

IGNORE_DIRS = {".git", "__pycache__", ".jarvis", "AUXFILES", "INFO", "PREVIEW"}


@dataclass
class CollectionCandidate:
    collection_id: str
    name: str
    collection_type: str
    domain: str
    discipline: str | None
    subject: str | None
    file_count: int


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def humanize(text: str) -> str:
    return text.replace("_", " ").replace("-", " ").title()


def classify_folder(path: Path, root: Path) -> tuple[str, str | None, str | None, str]:
    rel_parts = path.relative_to(root).parts

    domain = rel_parts[0] if len(rel_parts) >= 1 else "unknown"
    discipline = rel_parts[1] if len(rel_parts) >= 2 else None
    subject = rel_parts[2] if len(rel_parts) >= 3 else discipline

    if domain == "geography" and len(rel_parts) >= 2 and rel_parts[1] == "geodata":
        collection_type = "dataset"
    elif domain == "zim":
        collection_type = "knowledge_archive"
    else:
        collection_type = "knowledge"

    return domain, discipline, subject, collection_type


def count_assets(path: Path) -> Counter:
    counts: Counter = Counter()

    for f in path.rglob("*"):
        if not f.is_file():
            continue

        if any(part in IGNORE_DIRS for part in f.parts):
            continue

        ext = f.suffix.lower()

        if ext in DOC_EXT:
            counts["documents"] += 1
        elif ext in DATA_EXT:
            counts["datasets"] += 1
        elif ext in ZIM_EXT:
            counts["zim"] += 1
        else:
            counts["other"] += 1

    return counts


def discover_collections(root: Path = DEFAULT_KNOWLEDGE_ROOT) -> list[CollectionCandidate]:
    candidates: list[CollectionCandidate] = []

    for folder in sorted(root.rglob("*")):
        if not folder.is_dir():
            continue

        if any(part in IGNORE_DIRS for part in folder.parts):
            continue

        counts = count_assets(folder)
        total = sum(counts.values())

        if total == 0:
            continue

        rel = folder.relative_to(root)
        parts = rel.parts

        # Avoid thousands of tiny geodata tile folders becoming collections.
        if "Copernicus_DSM" in str(rel):
            continue

        # Prefer meaningful collection levels.
        if len(parts) > 3 and parts[0] != "zim":
            continue

        domain, discipline, subject, collection_type = classify_folder(folder, root)

        collection_id = str(rel).lower().replace("/", ".").replace(" ", "_")
        name = humanize(parts[-1])

        candidates.append(
            CollectionCandidate(
                collection_id=collection_id,
                name=name,
                collection_type=collection_type,
                domain=domain,
                discipline=discipline,
                subject=subject,
                file_count=total,
            )
        )

    return candidates


def upsert_collections(db_path: Path = DEFAULT_CATALOG_DB, root: Path = DEFAULT_KNOWLEDGE_ROOT) -> int:
    migrate(db_path)
    now = utc_now()
    candidates = discover_collections(root)

    with connect(db_path) as conn:
        for c in candidates:
            conn.execute(
                """
                INSERT INTO collections (
                    id, name, collection_type, domain, discipline, subject,
                    description, authority_score, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    collection_type=excluded.collection_type,
                    domain=excluded.domain,
                    discipline=excluded.discipline,
                    subject=excluded.subject,
                    updated_at=excluded.updated_at
                """,
                (
                    c.collection_id,
                    c.name,
                    c.collection_type,
                    c.domain,
                    c.discipline,
                    c.subject,
                    f"Auto-discovered from Knowledge/{c.collection_id.replace('.', '/')}",
                    0,
                    now,
                    now,
                ),
            )
        conn.commit()

    return len(candidates)


def print_collections(db_path: Path = DEFAULT_CATALOG_DB) -> None:
    migrate(db_path)

    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, collection_type, domain, discipline, subject
            FROM collections
            ORDER BY domain, discipline, subject, id
            """
        ).fetchall()

    print("=" * 80)
    print("JARVIS KNOWLEDGE CATALOG COLLECTIONS")
    print("=" * 80)

    for row in rows:
        print(
            f"{row['id']:<45} "
            f"{row['collection_type']:<18} "
            f"{row['domain'] or '-':<15} "
            f"{row['discipline'] or '-':<20} "
            f"{row['subject'] or '-'}"
        )
