from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

CATALOG_DB = Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite")
KNOWLEDGE_ROOT = Path("/media/abdullah/JARVISDATA/Knowledge")
RULES_FILE = Path("knowledge/ontology/assimilation_rules.yaml")

SUPPORTED = {".pdf", ".txt", ".md", ".html", ".htm", ".xml", ".json", ".csv", ".zim", ".epub"}
MAX_CHARS = 120_000


@dataclass
class AssimilationResult:
    file_path: str
    sha256: str
    title: str
    domain: str | None
    discipline: str | None
    subject: str | None
    collection_id: str | None
    confidence: float
    evidence: dict
    content_chars: int


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[_/\\\-]+", " ", text)
    text = re.sub(r"[^a-z0-9+.# ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_rules() -> dict:
    data = yaml.safe_load(RULES_FILE.read_text(encoding="utf-8")) or {}
    return data.get("rules", {})


def infer_collection_id(path: Path) -> str | None:
    try:
        idx = path.parts.index("Knowledge")
        rel = path.parts[idx + 1 : -1]
    except ValueError:
        rel = path.relative_to(KNOWLEDGE_ROOT).parts[:-1] if path.is_relative_to(KNOWLEDGE_ROOT) else ()

    if not rel:
        return None

    return ".".join(p.lower().replace(" ", "_") for p in rel[:3])


def read_text(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix in {".txt", ".md", ".html", ".htm", ".xml", ".json", ".csv"}:
        return path.read_text(encoding="utf-8", errors="ignore")[:MAX_CHARS]

    if suffix == ".pdf":
        try:
            from knowledge_engine.extraction.extractors.pdf import PDFExtractor

            pages = PDFExtractor().extract(path)
            chunks = []
            for page in pages[:40]:
                chunks.append(getattr(page, "text", str(page)))
            return "\n".join(chunks)[:MAX_CHARS]
        except Exception:
            try:
                from pypdf import PdfReader

                reader = PdfReader(str(path))
                chunks = []
                for page in reader.pages[:40]:
                    chunks.append(page.extract_text() or "")
                return "\n".join(chunks)[:MAX_CHARS]
            except Exception:
                return ""

    return ""


def score_document(path: Path, text: str) -> AssimilationResult:
    title = path.stem.replace("_", " ").replace("-", " ").strip()
    collection_id = infer_collection_id(path)

    haystack = normalize(" ".join([str(path), title, str(path.parent), text]))
    rules = load_rules()

    best_key = None
    best_score = 0
    evidence = {}

    for key, rule in rules.items():
        hits = []
        for kw in rule.get("keywords", []):
            nkw = normalize(kw)
            if nkw and nkw in haystack:
                hits.append(kw)

        path_boost = 0
        subject = rule.get("subject", "")
        discipline = rule.get("discipline", "")
        domain = rule.get("domain", "")

        path_text = normalize(str(path.parent))
        for token in [subject, discipline, domain, key]:
            if token and normalize(token) in path_text:
                path_boost += 2

        score = len(hits) + path_boost

        if score > best_score:
            best_score = score
            best_key = key
            evidence = {
                "rule": key,
                "keyword_hits": hits,
                "path_boost": path_boost,
                "score": score,
            }

    if not best_key:
        rule = {}
        confidence = 0.0
    else:
        rule = rules[best_key]
        confidence = min(0.35 + best_score * 0.10, 0.98)

    return AssimilationResult(
        file_path=str(path),
        sha256=sha256_file(path),
        title=title,
        domain=rule.get("domain"),
        discipline=rule.get("discipline"),
        subject=rule.get("subject"),
        collection_id=collection_id,
        confidence=confidence,
        evidence=evidence,
        content_chars=len(text),
    )


def migrate() -> None:
    CATALOG_DB.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(CATALOG_DB) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS catalog_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
                sha256 TEXT NOT NULL,
                title TEXT,
                file_type TEXT,
                size_bytes INTEGER,
                source_name TEXT,
                collection_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS document_subjects (
                file_path TEXT NOT NULL,
                sha256 TEXT,
                subject TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 1.0,
                assigned_by TEXT NOT NULL DEFAULT 'assimilation',
                created_at TEXT NOT NULL,
                PRIMARY KEY(file_path, subject)
            );

            CREATE TABLE IF NOT EXISTS document_assimilation (
                file_path TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL,
                title TEXT,
                domain TEXT,
                discipline TEXT,
                subject TEXT,
                collection_id TEXT,
                confidence REAL,
                evidence_json TEXT,
                content_chars INTEGER DEFAULT 0,
                assigned_by TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS collection_documents (
                collection_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                sha256 TEXT,
                confidence REAL NOT NULL DEFAULT 1.0,
                assigned_by TEXT NOT NULL DEFAULT 'assimilation',
                created_at TEXT NOT NULL,
                PRIMARY KEY(collection_id, file_path)
            );

            CREATE INDEX IF NOT EXISTS idx_document_assimilation_subject
            ON document_assimilation(subject);

            CREATE INDEX IF NOT EXISTS idx_document_assimilation_domain
            ON document_assimilation(domain);

            CREATE INDEX IF NOT EXISTS idx_document_subjects_subject
            ON document_subjects(subject);
            """
        )


def store(result: AssimilationResult) -> None:
    now = utc_now()
    path = Path(result.file_path)

    with sqlite3.connect(CATALOG_DB) as conn:
        conn.execute(
            """
            INSERT INTO catalog_documents (
                file_path, sha256, title, file_type, size_bytes,
                source_name, collection_id, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                sha256=excluded.sha256,
                title=excluded.title,
                file_type=excluded.file_type,
                size_bytes=excluded.size_bytes,
                collection_id=excluded.collection_id,
                updated_at=excluded.updated_at
            """,
            (
                result.file_path,
                result.sha256,
                result.title,
                path.suffix.lower().lstrip("."),
                path.stat().st_size,
                None,
                result.collection_id,
                now,
                now,
            ),
        )

        conn.execute(
            """
            INSERT OR REPLACE INTO document_assimilation (
                file_path, sha256, title, domain, discipline, subject,
                collection_id, confidence, evidence_json, content_chars,
                assigned_by, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.file_path,
                result.sha256,
                result.title,
                result.domain,
                result.discipline,
                result.subject,
                result.collection_id,
                result.confidence,
                json.dumps(result.evidence, ensure_ascii=False),
                result.content_chars,
                "knowledge_assimilation_v1",
                now,
            ),
        )

        if result.subject:
            conn.execute(
                """
                INSERT OR REPLACE INTO document_subjects (
                    file_path, sha256, subject, confidence, assigned_by, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    result.file_path,
                    result.sha256,
                    result.subject,
                    result.confidence,
                    "knowledge_assimilation_v1",
                    now,
                ),
            )

        if result.collection_id:
            conn.execute(
                """
                INSERT OR IGNORE INTO collection_documents (
                    collection_id, file_path, sha256, confidence, assigned_by, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    result.collection_id,
                    result.file_path,
                    result.sha256,
                    0.85,
                    "knowledge_assimilation_v1",
                    now,
                ),
            )

        conn.commit()


def assimilate_file(path: Path) -> AssimilationResult:
    path = Path(path)
    text = read_text(path)
    result = score_document(path, text)
    store(result)
    return result


def assimilate_tree(root: Path = KNOWLEDGE_ROOT) -> dict:
    migrate()

    total = 0
    assimilated = 0
    unclassified = 0
    skipped = 0

    for path in Path(root).rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in SUPPORTED:
            skipped += 1
            continue

        total += 1
        result = assimilate_file(path)

        if result.subject:
            assimilated += 1
        else:
            unclassified += 1

    return {
        "total_supported": total,
        "assimilated": assimilated,
        "unclassified": unclassified,
        "skipped": skipped,
    }
