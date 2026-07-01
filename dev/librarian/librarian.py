#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DEFAULT_KNOWLEDGE_ROOT = Path("/media/abdullah/JARVISDATA/Knowledge")
DEFAULT_DB = Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/librarian.sqlite")

SUPPORTED_EXTENSIONS = {
    ".pdf", ".epub", ".txt", ".md", ".zim", ".html", ".htm", ".csv", ".json", ".xml"
}

PDF_MIN_SIZE_BYTES = 1024


DESIRED_TOPICS = {
    "medical": [
        "anatomy", "community_health", "dentistry", "emergency", "field_medicine",
        "first_aid", "medications", "mental_health", "obstetrics", "pediatrics",
        "public_health", "reference", "surgery", "radiology", "pharmacology",
        "tropical_medicine", "wilderness_medicine", "prolonged_field_care",
    ],
    "computing": [
        "ai", "cybersecurity", "databases", "linux", "networking",
        "operating_systems", "programming", "reverse_engineering",
        "software_engineering", "virtualization", "distributed_systems",
        "compilers", "cryptography",
    ],
    "engineering": [
        "civil", "electrical", "electronics", "manufacturing", "materials",
        "mechanical", "control_systems", "hydraulics", "thermodynamics",
        "robotics", "embedded_systems",
    ],
    "mathematics": [
        "algebra", "calculus", "discrete_math", "linear_algebra", "statistics",
        "probability", "optimization", "numerical_methods",
    ],
    "science": ["biology", "chemistry", "earth_science", "physics", "astronomy"],
    "aviation": ["aircraft", "maintenance", "navigation", "regulations", "rotorcraft", "systems"],
    "emergency": [
        "agriculture", "bushcraft", "civil_defense", "communications",
        "disaster_response", "food", "search_and_rescue", "shelter",
        "survival", "water", "wilderness",
    ],
    "military": ["doctrine", "engineering", "field_manuals", "logistics", "navigation", "tactics", "training"],
    "reference": ["handbooks", "manuals", "quick_reference", "standards"],
    "repair": ["appliances", "automotive", "electronics", "machinery", "tools"],
    "geography": ["geodata", "gis", "maps", "terrain", "weather"],
    "zim": ["electronics", "engineering", "ifixit", "libretexts", "stackexchange", "wikibooks", "wikipedia"],
}


TRUST_HINTS = {
    "mit": 100,
    "openstax": 100,
    "libretexts": 95,
    "who": 95,
    "cdc": 95,
    "nih": 95,
    "pubmed": 95,
    "nist": 95,
    "nasa": 95,
    "faa": 95,
    "fema": 90,
    "us_army": 85,
    "army": 85,
    "usmc": 85,
    "mcrp": 85,
    "fm_": 80,
    "tc_": 80,
    "hesperian": 80,
    "stackexchange": 75,
    "ifixit": 75,
    "wikibooks": 70,
    "anonymous": 20,
}


@dataclass
class VerificationResult:
    status: str
    severity: str
    message: str
    magic_type: str | None = None


@dataclass
class Document:
    path: Path
    rel_path: str
    extension: str
    size_bytes: int
    sha256: str
    top_category: str
    subcategory: str
    title_guess: str
    trust_score: int
    verification: VerificationResult


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(block_size):
            digest.update(chunk)
    return digest.hexdigest()


def guess_trust_score(path: Path) -> int:
    text = str(path).lower()
    for key, score in TRUST_HINTS.items():
        if key in text:
            return score
    return 50


def guess_categories(root: Path, path: Path) -> tuple[str, str]:
    parts = path.relative_to(root).parts
    top = parts[0] if len(parts) >= 1 else "unknown"
    sub = parts[1] if len(parts) >= 2 else "uncategorized"
    return top, sub


def read_magic(path: Path, n: int = 16) -> bytes:
    try:
        with path.open("rb") as f:
            return f.read(n)
    except OSError:
        return b""


def verify_file(path: Path) -> VerificationResult:
    suffix = path.suffix.lower()

    if not path.exists():
        return VerificationResult("unreadable", "error", "File does not exist")

    size = path.stat().st_size

    if size == 0:
        return VerificationResult("empty_file", "error", "File is zero bytes")

    magic = read_magic(path)

    if suffix == ".pdf":
        if not magic.startswith(b"%PDF-"):
            return VerificationResult("fake_pdf", "error", "PDF extension but missing %PDF magic bytes", "not_pdf")
        if size < PDF_MIN_SIZE_BYTES:
            return VerificationResult("suspicious_small_file", "warning", f"PDF is unusually small: {size} bytes", "pdf")
        return VerificationResult("verified", "info", "Valid PDF magic bytes", "pdf")

    if suffix == ".json":
        try:
            json.loads(path.read_text(encoding="utf-8"))
            return VerificationResult("verified", "info", "Valid JSON", "json")
        except Exception as exc:
            return VerificationResult("corrupt", "error", f"Invalid JSON: {exc}", "json")

    if suffix in {".txt", ".md", ".csv", ".xml", ".html", ".htm"}:
        try:
            path.read_text(encoding="utf-8", errors="strict")
            return VerificationResult("verified", "info", "Readable UTF-8 text", "text")
        except UnicodeDecodeError:
            return VerificationResult("unreadable", "error", "Text file is not valid UTF-8", "text")

    if suffix == ".epub":
        try:
            if zipfile.is_zipfile(path):
                return VerificationResult("verified", "info", "Valid EPUB ZIP container", "epub")
            return VerificationResult("corrupt", "error", "EPUB is not a valid ZIP container", "epub")
        except Exception as exc:
            return VerificationResult("corrupt", "error", f"EPUB verification failed: {exc}", "epub")

    if suffix == ".zim":
        if size < 1024 * 1024:
            return VerificationResult("suspicious_small_file", "warning", f"ZIM is unusually small: {size} bytes", "zim")
        return VerificationResult("verified", "info", "ZIM basic size check passed", "zim")

    return VerificationResult("unsupported_type", "info", f"Unsupported type: {suffix}", None)


def iter_documents(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    existing = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
                rel_path TEXT NOT NULL,
                title_guess TEXT,
                extension TEXT,
                size_bytes INTEGER,
                sha256 TEXT,
                top_category TEXT,
                subcategory TEXT,
                trust_score INTEGER,
                ingested INTEGER DEFAULT 0,
                embedded INTEGER DEFAULT 0,
                ocr_required INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT,
                knowledge_root TEXT,
                document_count INTEGER,
                total_size_bytes INTEGER
            );

            CREATE TABLE IF NOT EXISTS duplicates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sha256 TEXT,
                file_path TEXT,
                duplicate_group_count INTEGER,
                detected_at TEXT
            );

            CREATE TABLE IF NOT EXISTS coverage_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                top_category TEXT,
                subcategory TEXT,
                document_count INTEGER,
                avg_trust_score REAL,
                status TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS gaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                top_category TEXT,
                subcategory TEXT,
                reason TEXT,
                priority INTEGER,
                detected_at TEXT
            );

            CREATE TABLE IF NOT EXISTS collection_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT,
                detected_at TEXT
            );
            """
        )

        ensure_column(conn, "documents", "verification_status", "TEXT")
        ensure_column(conn, "documents", "verification_message", "TEXT")
        ensure_column(conn, "documents", "verified_at", "TEXT")
        ensure_column(conn, "documents", "magic_type", "TEXT")
        ensure_column(conn, "documents", "page_count", "INTEGER")


def inventory(root: Path, db_path: Path) -> None:
    init_db(db_path)

    if not root.exists():
        raise FileNotFoundError(f"Knowledge root does not exist: {root}")

    docs: list[Document] = []
    print(f"[JARVIS Librarian] Scanning: {root}")

    for path in iter_documents(root):
        rel_path = str(path.relative_to(root))
        top, sub = guess_categories(root, path)
        size = path.stat().st_size
        digest = sha256_file(path)
        title = path.stem.replace("_", " ").replace("-", " ").strip()
        trust = guess_trust_score(path)
        verification = verify_file(path)

        docs.append(
            Document(
                path=path,
                rel_path=rel_path,
                extension=path.suffix.lower(),
                size_bytes=size,
                sha256=digest,
                top_category=top,
                subcategory=sub,
                title_guess=title,
                trust_score=trust,
                verification=verification,
            )
        )

    now = utc_now()

    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM collection_issues")

        for doc in docs:
            conn.execute(
                """
                INSERT INTO documents (
                    file_path, rel_path, title_guess, extension, size_bytes,
                    sha256, top_category, subcategory, trust_score,
                    created_at, updated_at, verification_status,
                    verification_message, verified_at, magic_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    rel_path=excluded.rel_path,
                    title_guess=excluded.title_guess,
                    extension=excluded.extension,
                    size_bytes=excluded.size_bytes,
                    sha256=excluded.sha256,
                    top_category=excluded.top_category,
                    subcategory=excluded.subcategory,
                    trust_score=excluded.trust_score,
                    updated_at=excluded.updated_at,
                    verification_status=excluded.verification_status,
                    verification_message=excluded.verification_message,
                    verified_at=excluded.verified_at,
                    magic_type=excluded.magic_type
                """,
                (
                    str(doc.path),
                    doc.rel_path,
                    doc.title_guess,
                    doc.extension,
                    doc.size_bytes,
                    doc.sha256,
                    doc.top_category,
                    doc.subcategory,
                    doc.trust_score,
                    now,
                    now,
                    doc.verification.status,
                    doc.verification.message,
                    now,
                    doc.verification.magic_type,
                ),
            )

            if doc.verification.status != "verified":
                conn.execute(
                    """
                    INSERT INTO collection_issues (
                        file_path, issue_type, severity, message, detected_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        str(doc.path),
                        doc.verification.status,
                        doc.verification.severity,
                        doc.verification.message,
                        now,
                    ),
                )

        conn.execute(
            """
            INSERT INTO audit_runs (
                started_at, knowledge_root, document_count, total_size_bytes
            )
            VALUES (?, ?, ?, ?)
            """,
            (now, str(root), len(docs), sum(d.size_bytes for d in docs)),
        )

    print(f"[OK] Cataloged {len(docs)} documents.")
    print(f"[OK] Database: {db_path}")


def dedupe(db_path: Path) -> None:
    init_db(db_path)
    now = utc_now()

    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM duplicates")

        duplicate_rows = conn.execute(
            """
            SELECT sha256, COUNT(*) AS count
            FROM documents
            WHERE verification_status = 'verified'
            GROUP BY sha256
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            """
        ).fetchall()

        for sha256, count in duplicate_rows:
            paths = conn.execute(
                """
                SELECT file_path
                FROM documents
                WHERE sha256 = ?
                AND verification_status = 'verified'
                ORDER BY file_path
                """,
                (sha256,),
            ).fetchall()

            for (file_path,) in paths:
                conn.execute(
                    """
                    INSERT INTO duplicates (
                        sha256, file_path, duplicate_group_count, detected_at
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (sha256, file_path, count, now),
                )

    print(f"[OK] Verified duplicate hash groups found: {len(duplicate_rows)}")


def coverage(db_path: Path) -> None:
    init_db(db_path)
    now = utc_now()

    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM coverage_scores")

        rows = conn.execute(
            """
            SELECT top_category, subcategory, COUNT(*) AS count, AVG(trust_score)
            FROM documents
            WHERE verification_status = 'verified'
            GROUP BY top_category, subcategory
            ORDER BY top_category, subcategory
            """
        ).fetchall()

        for top, sub, count, avg_trust in rows:
            if count >= 10 and avg_trust >= 75:
                status = "strong"
            elif count >= 5 and avg_trust >= 60:
                status = "moderate"
            elif count >= 1:
                status = "weak"
            else:
                status = "missing"

            conn.execute(
                """
                INSERT INTO coverage_scores (
                    top_category, subcategory, document_count,
                    avg_trust_score, status, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (top, sub, count, avg_trust or 0, status, now),
            )

        saved = conn.execute(
            """
            SELECT top_category, subcategory, document_count, avg_trust_score, status
            FROM coverage_scores
            ORDER BY top_category, subcategory
            """
        ).fetchall()

    print("\n[JARVIS Librarian] Coverage Report\n")
    for top, sub, count, avg_trust, status in saved:
        print(f"{top}/{sub:<30} docs={count:<4} trust={avg_trust:5.1f} status={status}")

    print("\n[OK] Coverage report complete.")


def gaps(db_path: Path) -> None:
    init_db(db_path)
    now = utc_now()

    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM gaps")

        existing = {
            (top, sub): count
            for top, sub, count in conn.execute(
                """
                SELECT top_category, subcategory, COUNT(*)
                FROM documents
                WHERE verification_status = 'verified'
                GROUP BY top_category, subcategory
                """
            ).fetchall()
        }

        inserted = 0

        for top, wanted_subtopics in DESIRED_TOPICS.items():
            for sub in wanted_subtopics:
                count = existing.get((top, sub), 0)

                if count == 0:
                    reason = "missing"
                    priority = 100
                elif count < 3:
                    reason = "underdeveloped"
                    priority = 70
                else:
                    continue

                conn.execute(
                    """
                    INSERT INTO gaps (
                        top_category, subcategory, reason, priority, detected_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (top, sub, reason, priority, now),
                )
                inserted += 1

        rows = conn.execute(
            """
            SELECT top_category, subcategory, reason, priority
            FROM gaps
            ORDER BY priority DESC, top_category, subcategory
            """
        ).fetchall()

    print("\n[JARVIS Librarian] Knowledge Gaps\n")
    for top, sub, reason, priority in rows:
        print(f"{priority:3}  {top}/{sub:<32} {reason}")

    print(f"\n[OK] Gap analysis complete. Gaps found: {inserted}")


def doctor(db_path: Path) -> None:
    init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        total = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        verified = conn.execute(
            "SELECT COUNT(*) FROM documents WHERE verification_status = 'verified'"
        ).fetchone()[0]

        issue_rows = conn.execute(
            """
            SELECT issue_type, COUNT(*)
            FROM collection_issues
            GROUP BY issue_type
            ORDER BY COUNT(*) DESC, issue_type
            """
        ).fetchall()

        duplicate_groups = conn.execute(
            """
            SELECT COUNT(DISTINCT sha256)
            FROM duplicates
            """
        ).fetchone()[0]

        examples = conn.execute(
            """
            SELECT issue_type, severity, file_path, message
            FROM collection_issues
            ORDER BY severity DESC, issue_type, file_path
            LIMIT 30
            """
        ).fetchall()

    health = (verified / total * 100) if total else 0

    print("\nJARVIS Librarian Integrity Report")
    print("--------------------------------")
    print(f"Documents scanned:        {total}")
    print(f"Verified:                 {verified}")
    print(f"Problem files:            {total - verified}")
    print(f"Verified duplicate groups:{duplicate_groups}")
    print(f"Collection health:        {health:.1f}%")

    print("\nIssues")
    print("------")
    if not issue_rows:
        print("No collection issues found.")
    else:
        for issue_type, count in issue_rows:
            print(f"{issue_type:<24} {count}")

    print("\nExamples")
    print("--------")
    if not examples:
        print("No issue examples.")
    else:
        for issue_type, severity, file_path, message in examples:
            print(f"{severity.upper():<8} {issue_type:<24} {file_path}")
            print(f"         {message}")


def export_json(db_path: Path, output: Path) -> None:
    init_db(db_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        data = {
            "exported_at": utc_now(),
            "documents": [dict(row) for row in conn.execute("SELECT * FROM documents")],
            "duplicates": [dict(row) for row in conn.execute("SELECT * FROM duplicates")],
            "coverage_scores": [dict(row) for row in conn.execute("SELECT * FROM coverage_scores")],
            "gaps": [dict(row) for row in conn.execute("SELECT * FROM gaps")],
            "collection_issues": [dict(row) for row in conn.execute("SELECT * FROM collection_issues")],
        }

    output.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"[OK] Exported JSON: {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS Librarian ADR-0006/0007")
    parser.add_argument(
        "command",
        choices=["inventory", "verify", "doctor", "dedupe", "coverage", "gaps", "audit", "export"],
    )
    parser.add_argument("--knowledge-root", default=str(DEFAULT_KNOWLEDGE_ROOT))
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--output", default="librarian_export.json")

    args = parser.parse_args()

    root = Path(args.knowledge_root)
    db_path = Path(args.db)

    if args.command in {"inventory", "verify"}:
        inventory(root, db_path)
    elif args.command == "doctor":
        doctor(db_path)
    elif args.command == "dedupe":
        dedupe(db_path)
    elif args.command == "coverage":
        coverage(db_path)
    elif args.command == "gaps":
        gaps(db_path)
    elif args.command == "audit":
        inventory(root, db_path)
        dedupe(db_path)
        coverage(db_path)
        gaps(db_path)
        doctor(db_path)
    elif args.command == "export":
        export_json(db_path, Path(args.output))


if __name__ == "__main__":
    main()
