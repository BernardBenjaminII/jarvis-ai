from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from core.knowledge_catalog.production_materialization.models import EngineConfig, WorkItem


ACK = "IDENTITY_AWARE_MATERIALIZATION"
SUPPORTED = {".pdf", ".md", ".txt", ".html", ".htm", ".docx", ".epub", ".json", ".csv", ".xml"}
DEFAULT_CATALOG = Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite")
DEFAULT_STATE = Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/processing")


def _current_failed_ids(engine_result: dict) -> set[str]:
    return {
        str(row["candidate_id"])
        for row in engine_result.get("results", ())
        if str(row.get("stage", "")) == "FAILED"
    }


def _compact_ocr_result(result) -> dict:
    """Serialize OCR telemetry without ever returning recovered document text."""
    return {
        "candidate_id": result.candidate_id,
        "path": result.path,
        "status": result.status,
        "strategy": result.strategy,
        "detail": result.detail,
        "characters": int(result.chars),
        "pages_total": int(result.pages_total),
        "pages_attempted": int(result.pages_attempted),
        "pages_recovered": int(result.pages_recovered),
        "quality_score": round(float(result.quality_score), 4),
    }


def run_ocr_fallback(*, catalog: Path, checkpoint: Path, state_root: Path,
                     engine_result: dict, max_pages: int,
                     languages: str) -> dict:
    """Recover only PDF failures produced by the current materialization batch."""
    failed_ids = _current_failed_ids(engine_result)
    if not failed_ids:
        return {"status": "NOT_NEEDED", "selected": 0, "recovered": 0,
                "unresolved": 0, "results": []}

    from core.knowledge_catalog.ocr_recovery.models import OCRPolicy
    from core.knowledge_catalog.ocr_recovery.service import OCRRecoveryService

    service = OCRRecoveryService(
        runtime_catalog=catalog,
        checkpoint_db=checkpoint,
        recovery_db=state_root / "ocr-recovery.sqlite",
        work_dir=state_root / "ocr-work",
        policy=OCRPolicy(max_pages=max_pages, languages=languages),
    )
    candidates = tuple(
        candidate for candidate in service.candidates()
        if candidate.candidate_id in failed_ids
        and candidate.extension.casefold() == ".pdf"
    )
    outcomes = service.recover(candidates, dry_run=False, writer_batch_size=1)
    compact = [_compact_ocr_result(outcome) for outcome in outcomes]
    recovered_ids = {
        outcome.candidate_id for outcome in outcomes
        if outcome.status in {"RECOVERABLE_NATIVE", "RECOVERABLE_OCR"}
    }
    unresolved = len(failed_ids - recovered_ids)
    return {
        "status": "COMPLETE" if unresolved == 0 else "COMPLETED_WITH_FAILURES",
        "selected": len(candidates),
        "recovered": len(recovered_ids),
        "unresolved": unresolved,
        "results": compact,
    }


def batch_checkpoint_states(path: Path, candidate_ids: set[str]) -> dict[str, int]:
    if not candidate_ids:
        return {}
    db = open_ro(path)
    try:
        placeholders = ",".join("?" for _ in candidate_ids)
        return {str(row[0]): int(row[1]) for row in db.execute(
            f"SELECT stage,COUNT(*) FROM items WHERE candidate_id IN ({placeholders}) GROUP BY stage",
            tuple(sorted(candidate_ids)),
        )}
    finally:
        db.close()


def open_ro(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return db


def select_admissions(catalog: Path, root: Path) -> tuple[tuple[WorkItem, ...], dict[str, int]]:
    db = open_ro(catalog)
    counts = Counter()
    items = []
    try:
        runtime_paths = set()
        runtime_hashes = set()
        for row in db.execute("SELECT file_path,sha256 FROM runtime_documents"):
            if row["file_path"]:
                runtime_paths.add(str(row["file_path"]))
            if row["sha256"]:
                runtime_hashes.add(str(row["sha256"]))

        rows = db.execute("""
            SELECT kc.discovered_file_id, kc.file_path, kc.domain, kc.subject,
                   df.filename, df.extension, df.sha256, df.size_bytes
            FROM knowledge_classifications kc
            JOIN discovered_files df ON df.id=kc.discovered_file_id
            WHERE kc.action='candidate'
              AND kc.file_path LIKE ?
            ORDER BY kc.file_path
        """, (str(root) + "/%",))

        for row in rows:
            counts["classified_candidates"] += 1
            path = Path(str(row["file_path"]))
            extension = str(row["extension"] or path.suffix).casefold()
            sha = str(row["sha256"] or "")
            if path.name.startswith("._"):
                counts["appledouble_sidecar"] += 1
                continue
            if extension not in SUPPORTED:
                counts["unsupported"] += 1
                continue
            if not path.is_file() or int(row["size_bytes"] or 0) <= 0:
                counts["missing_or_empty"] += 1
                continue
            if str(path) in runtime_paths:
                counts["existing_path"] += 1
                continue
            if sha and sha in runtime_hashes:
                counts["existing_sha"] += 1
                continue
            candidate_id = f"discovered:{int(row['discovered_file_id'])}:{sha[:16]}"
            items.append(WorkItem(
                candidate_id=candidate_id,
                path=str(path),
                title=str(row["filename"] or path.name),
                category=str(row["domain"] or row["subject"] or "") or None,
                extension=extension,
                sha256=sha or None,
            ))
            counts["admitted"] += 1
    finally:
        db.close()
    return tuple(items), dict(counts)


def checkpoint_counts(path: Path) -> dict[str, int]:
    if not path.is_file():
        return {}
    db = open_ro(path)
    try:
        return {str(row[0]): int(row[1]) for row in db.execute(
            "SELECT stage,COUNT(*) FROM items GROUP BY stage"
        )}
    finally:
        db.close()


def runtime_integrity(catalog: Path) -> dict[str, object]:
    db = open_ro(catalog)
    try:
        counts = {
            table: int(db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
            for table in ("runtime_documents", "runtime_chunks", "runtime_chunks_fts")
        }
        integrity = str(db.execute("PRAGMA integrity_check").fetchone()[0])
        counts["integrity_check"] = integrity
        counts["fts_balanced"] = counts["runtime_chunks"] == counts["runtime_chunks_fts"]
        return counts
    finally:
        db.close()


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="jarvis assimilate process",
        description="Identity-aware, checkpointed production materialization.")
    p.add_argument("root", type=Path)
    p.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    p.add_argument("--state-root", type=Path, default=DEFAULT_STATE)
    p.add_argument("--apply", action="store_true")
    p.add_argument("--refresh-admission", action="store_true")
    p.add_argument("--batch-size", type=int, default=10)
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--retry-failures", action="store_true")
    p.add_argument("--no-ocr", action="store_true",
                   help="Disable automatic OCR recovery for failed PDFs.")
    p.add_argument("--ocr-max-pages", type=int, default=300)
    p.add_argument("--ocr-languages", default="eng")
    p.add_argument("--acknowledge")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root, catalog, state_root = args.root.resolve(), args.catalog.resolve(), args.state_root.resolve()
    issues = []
    if not root.is_dir(): issues.append("knowledge root missing")
    if not catalog.is_file(): issues.append("catalog missing")
    if args.batch_size < 1: issues.append("batch-size must be positive")
    if args.workers < 1: issues.append("workers must be positive")
    if args.ocr_max_pages < 1: issues.append("ocr-max-pages must be positive")
    if not args.ocr_languages.strip(): issues.append("ocr-languages must not be empty")
    if catalog.is_file():
        db = open_ro(catalog)
        try:
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                issues.append("catalog integrity_check failed")
        finally: db.close()
    checkpoint = state_root / "materialization-checkpoint.sqlite"
    result = {
        "mode": "APPLY" if args.apply else "STRICT_READ_ONLY",
        "decision": "BLOCKED" if issues else "READY",
        "root": str(root), "catalog": str(catalog), "issues": issues,
        "checkpoint": str(checkpoint), "checkpoint_states": checkpoint_counts(checkpoint),
    }
    if not args.apply or issues:
        print(json.dumps(result, indent=2, sort_keys=True))
        print("\nRead-only processing status. No discovery, catalog, chunk, or embedding writes were made.")
        return 0 if not issues else 2
    if args.acknowledge != ACK:
        result["decision"] = "BLOCKED"
        result["issues"].append(f"apply requires --acknowledge {ACK}")
        print(json.dumps(result, indent=2, sort_keys=True)); return 2

    state_root.mkdir(parents=True, exist_ok=True)
    if args.refresh_admission:
        from knowledge_engine.classification.classifier import classify_discovered
        from knowledge_engine.discovery.service import DiscoveryService
        result["discovery"] = DiscoveryService(str(catalog)).run(str(root))
        result["classification"] = classify_discovered(str(catalog), root_filter=str(root))
    items, admission = select_admissions(catalog, root)
    result["admission"] = admission
    from core.knowledge_catalog.production_materialization.checkpoint import CheckpointStore
    from core.knowledge_catalog.production_materialization.engine import ProductionMaterializationEngine
    store = CheckpointStore(checkpoint)
    result["checkpoint_registered"] = store.register(items)
    report_dir = state_root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    config = EngineConfig(
        runtime_catalog=catalog, inventory_catalog=catalog, knowledge_root=root,
        checkpoint_db=checkpoint, report_dir=report_dir, workers=args.workers,
        batch_size=args.batch_size, dry_run=False, stop_on_error=False,
        retry_failures=args.retry_failures,
    )
    engine_result = ProductionMaterializationEngine(config).run()
    result["materialization"] = engine_result
    batch_ids = {
        str(row["candidate_id"])
        for row in engine_result.get("results", ())
        if row.get("candidate_id")
    }
    if args.no_ocr:
        result["ocr_fallback"] = {
            "status": "DISABLED", "selected": 0, "recovered": 0,
            "unresolved": len(_current_failed_ids(engine_result)), "results": [],
        }
    else:
        result["ocr_fallback"] = run_ocr_fallback(
            catalog=catalog, checkpoint=checkpoint, state_root=state_root,
            engine_result=engine_result, max_pages=args.ocr_max_pages,
            languages=args.ocr_languages,
        )
    batch_states = batch_checkpoint_states(checkpoint, batch_ids)
    result["batch_checkpoint_states"] = batch_states
    result["checkpoint_states"] = checkpoint_counts(checkpoint)
    result["runtime_integrity"] = runtime_integrity(catalog)
    failed = bool(batch_states.get("FAILED", 0) or batch_states.get("QUARANTINED", 0))
    if (result["runtime_integrity"]["integrity_check"] != "ok"
            or not result["runtime_integrity"]["fts_balanced"]):
        failed = True
    result["decision"] = "FAILED" if failed else "COMPLETE"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = report_dir / f"processing-{stamp}.json"
    report.write_text(json.dumps(result, indent=2, sort_keys=True))
    result["report"] = str(report)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
