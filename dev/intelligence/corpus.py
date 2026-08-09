from __future__ import annotations
import hashlib, sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SQLITE_HEADER = b"SQLite format 3\x00"
PATTERNS = ("*.sqlite", "*.sqlite3", "*.db")

def _q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _candidate(path: Path) -> dict[str, Any]:
    result = {
        "path": str(path.resolve()), "name": path.name,
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "header_valid": False, "sqlite_valid": False,
        "classification": "missing", "error": None,
    }
    if not path.is_file():
        return result
    try:
        result["header_valid"] = path.open("rb").read(16) == SQLITE_HEADER
    except OSError as exc:
        result["classification"] = "unreadable"
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result
    if not result["header_valid"]:
        result["classification"] = "non_sqlite_candidate"
        return result
    try:
        c = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
        c.execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
        c.close()
    except sqlite3.DatabaseError as exc:
        result["classification"] = "invalid_sqlite"
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result
    result["sqlite_valid"] = True
    result["classification"] = "verified_sqlite"
    return result

def _roles(name: str, columns: list[str], is_fts: bool) -> list[str]:
    text = " ".join([name.casefold(), *[x.casefold() for x in columns]])
    roles = []
    rules = {
        "runtime_search": ("runtime_", "fts", "embedding", "vector"),
        "document_registry": ("documents", "library_catalog", "knowledge_index"),
        "document_content": ("chunk", "document_text", "document_page", "document_structure"),
        "taxonomy_ontology": ("taxonomy", "topic", "concept", "relationship", "ontology"),
        "assimilation_acquisition": ("acquisition", "provider", "inspection", "assimilation"),
        "conversation": ("conversation", "message", "thread"),
        "executive_mission": ("mission", "executive", "task"),
        "telemetry_audit": ("telemetry", "audit", "trace", "metric"),
    }
    if is_fts:
        roles.append("runtime_search")
    for role, tokens in rules.items():
        if any(token in text for token in tokens):
            roles.append(role)
    return list(dict.fromkeys(roles or ["unclassified"]))

def _pipeline(roles: list[str]) -> list[str]:
    mapping = {
        "assimilation_acquisition": "assimilation",
        "document_registry": "catalog",
        "document_content": "extraction_chunking",
        "runtime_search": "materialization_retrieval",
        "taxonomy_ontology": "semantic_enrichment",
        "executive_mission": "executive",
        "conversation": "conversation",
        "telemetry_audit": "observability",
    }
    return list(dict.fromkeys(mapping[r] for r in roles if r in mapping))

def _inspect(path: Path) -> dict[str, Any]:
    c = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    try:
        objects = c.execute("""
            SELECT type,name,tbl_name,sql FROM sqlite_master
            WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name
        """).fetchall()
        tables, views, indexes, triggers = [], [], [], []
        for row in objects:
            typ, name, sql = row["type"], row["name"], row["sql"] or ""
            if typ == "table":
                cols = [dict(x) for x in c.execute(f"PRAGMA table_info({_q(name)})")]
                colnames = [str(x["name"]) for x in cols]
                fks = [dict(x) for x in c.execute(f"PRAGMA foreign_key_list({_q(name)})")]
                idx = [dict(x) for x in c.execute(f"PRAGMA index_list({_q(name)})")]
                virtual = "create virtual table" in sql.casefold()
                fts = virtual and "fts" in sql.casefold()
                try:
                    rows = int(c.execute(f"SELECT COUNT(*) FROM {_q(name)}").fetchone()[0])
                except sqlite3.DatabaseError:
                    rows = None
                roles = _roles(name, colnames, fts)
                tables.append({
                    "name": name, "row_count": rows, "columns": cols,
                    "primary_key": [x["name"] for x in cols if x["pk"]],
                    "foreign_keys": fks, "indexes": idx,
                    "is_virtual": virtual, "is_fts": fts,
                    "roles": roles, "pipeline_stages": _pipeline(roles),
                    "sql": sql,
                })
            elif typ == "view":
                views.append({"name": name, "sql": sql})
            elif typ == "index":
                indexes.append({"name": name, "table": row["tbl_name"], "sql": sql})
            elif typ == "trigger":
                triggers.append({"name": name, "table": row["tbl_name"], "sql": sql})
        return {
            "path": str(path.resolve()), "name": path.name,
            "size_bytes": path.stat().st_size, "sha256": _sha256(path),
            "sqlite_version": sqlite3.sqlite_version,
            "page_size": c.execute("PRAGMA page_size").fetchone()[0],
            "page_count": c.execute("PRAGMA page_count").fetchone()[0],
            "schema_version": c.execute("PRAGMA schema_version").fetchone()[0],
            "user_version": c.execute("PRAGMA user_version").fetchone()[0],
            "integrity_check": c.execute("PRAGMA quick_check").fetchone()[0],
            "tables": tables, "views": views,
            "indexes": indexes, "triggers": triggers,
            "fts_tables": [x["name"] for x in tables if x["is_fts"]],
        }
    finally:
        c.close()

def _relationships(databases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rels = []
    for db in databases:
        tables = db["tables"]
        names = {t["name"] for t in tables}
        for table in tables:
            for fk in table["foreign_keys"]:
                rels.append({
                    "source": f"{db['name']}:{table['name']}",
                    "target": f"{db['name']}:{fk['table']}",
                    "relation": "foreign_key",
                    "evidence": {"from": fk["from"], "to": fk["to"]},
                    "confidence": 1.0,
                })
        if {"runtime_documents", "runtime_chunks"} <= names:
            rels.append({
                "source": f"{db['name']}:runtime_documents",
                "target": f"{db['name']}:runtime_chunks",
                "relation": "materializes_to_chunks",
                "evidence": {"observed_tables": True}, "confidence": .95,
            })
        if {"runtime_chunks", "runtime_chunks_fts"} <= names:
            rels.append({
                "source": f"{db['name']}:runtime_chunks",
                "target": f"{db['name']}:runtime_chunks_fts",
                "relation": "indexed_by_fts",
                "evidence": {"observed_tables": True}, "confidence": .95,
            })
    return rels

@dataclass(frozen=True)
class CorpusInventoryReport:
    data: dict[str, Any]
    def to_dict(self) -> dict[str, Any]:
        return self.data

class CorpusIntelligenceFramework:
    def __init__(self, *, roots: tuple[Path, ...]):
        self.roots = tuple(Path(x).resolve() for x in roots)

    def execute(self) -> CorpusInventoryReport:
        found = set()
        for root in self.roots:
            if not root.exists():
                continue
            if root.is_file():
                found.add(root.resolve())
            else:
                for pattern in PATTERNS:
                    for path in root.rglob(pattern):
                        if path.is_file() and ".migration_backups" not in path.parts:
                            found.add(path.resolve())
        candidates = [_candidate(path) for path in sorted(found)]
        databases = [_inspect(Path(x["path"])) for x in candidates if x["sqlite_valid"]]
        corpora = []
        for db in databases:
            for table in db["tables"]:
                corpora.append({
                    "corpus_id": f"{db['name']}:{table['name']}",
                    "database": db["name"], "database_path": db["path"],
                    "table": table["name"], "row_count": table["row_count"],
                    "roles": table["roles"], "pipeline_stages": table["pipeline_stages"],
                    "searchable": bool(table["is_fts"] or set(table["roles"]) & {
                        "runtime_search","document_content","document_registry"
                    }),
                    "runtime": "runtime_search" in table["roles"],
                    "fts": table["is_fts"], "virtual": table["is_virtual"],
                })
        relationships = _relationships(databases)
        invalid = [x for x in candidates if not x["sqlite_valid"]]
        summary = {
            "candidate_count": len(candidates),
            "verified_database_count": len(databases),
            "invalid_candidate_count": len(invalid),
            "table_count": len(corpora),
            "searchable_corpus_count": sum(x["searchable"] for x in corpora),
            "runtime_corpus_count": sum(x["runtime"] for x in corpora),
            "fts_corpus_count": sum(x["fts"] for x in corpora),
            "view_count": sum(len(x["views"]) for x in databases),
            "index_count": sum(len(x["indexes"]) for x in databases),
            "trigger_count": sum(len(x["triggers"]) for x in databases),
            "relationship_count": len(relationships),
            "total_rows_across_corpora": sum(int(x["row_count"] or 0) for x in corpora),
            "invalid_candidates": invalid,
        }
        if not candidates:
            classification = "NO_DATABASE_CANDIDATES"
        elif not databases:
            classification = "NO_VERIFIED_SQLITE_DATABASES"
        elif not summary["searchable_corpus_count"]:
            classification = "NO_SEARCHABLE_CORPORA"
        elif not summary["runtime_corpus_count"]:
            classification = "CATALOG_ONLY_NO_RUNTIME_CORPUS"
        elif not summary["fts_corpus_count"]:
            classification = "RUNTIME_CORPUS_WITHOUT_FTS"
        else:
            classification = "CORPUS_INTELLIGENCE_OPERATIONAL"
        data = {
            "status": "EXCELLENT" if classification == "CORPUS_INTELLIGENCE_OPERATIONAL" else "FAILED",
            "classification": classification,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "roots": [str(x) for x in self.roots],
            "database_candidates": candidates, "databases": databases,
            "corpora": corpora, "relationships": relationships,
            "summary": summary,
            "recommendations": [
                "Use this inventory as the canonical input to IX-A5.7 Pack 2.",
                "Do not infer metadata quality from table existence alone.",
                "Classify invalid database candidates without aborting the audit.",
            ],
        }
        return CorpusInventoryReport(data)
