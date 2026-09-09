from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ACK = "JOURNALED_SAME_DRIVE_MOVE"
PATH_COLUMNS = {
    "catalog_documents": ("file_path",),
    "chunk_concepts": ("file_path",),
    "chunks": ("document_path",),
    "collection_documents": ("file_path",),
    "concepts": ("document_path",),
    "discovered_files": ("file_path",),
    "document_assimilation": ("file_path",),
    "document_chunks": ("file_path",),
    "document_concepts": ("file_path",),
    "document_keywords": ("file_path",),
    "document_pages": ("document_path",),
    "document_pages_fts": ("document_path",),
    "document_structure": ("document_path", "source"),
    "document_subjects": ("file_path",),
    "document_text": ("file_path",),
    "file_assets": ("file_path",),
    "inspections": ("document_path",),
    "knowledge_assimilation_queue": ("object_path",),
    "knowledge_classifications": ("file_path",),
    "knowledge_index": ("document_path",),
    "knowledge_object_files": ("file_path",),
    "knowledge_object_members": ("file_path",),
    "knowledge_objects": ("object_path", "primary_file_path"),
    "knowledge_registry": ("object_path", "source"),
    "knowledge_validation": ("object_path",),
    "librarian_catalog": ("object_path",),
    "library_catalog": ("document_path",),
    "promotion_history": ("source_path", "destination_path"),
    "resource_inspections": ("object_path",),
    "runtime_chunks_fts": ("file_path",),
    "runtime_documents": ("file_path",),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def find_latest_plan(directory: Path) -> Path:
    matches = sorted(directory.glob("jarvis_knowledge_migration_dry_run_*.zip"))
    if not matches:
        raise SystemExit("No migration dry-run zip found; pass --plan PATH.")
    return matches[-1]


def load_plan(path: Path) -> dict:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            return json.loads(archive.read("migration_dry_run.json"))
    return json.loads(path.read_text())


@dataclass(frozen=True)
class Config:
    root: Path
    plan: Path
    catalog: Path
    state_root: Path
    apply: bool = False
    acknowledge: str | None = None
    canary: int | None = None
    batch_size: int = 250
    run_id: str | None = None
    run_as1: bool = True


class AssimilationController:
    def __init__(self, config: Config):
        self.c = config
        self.plan = load_plan(config.plan)
        fingerprint = hashlib.sha256(config.plan.read_bytes()).hexdigest()[:12]
        self.run_id = config.run_id or f"migration-{fingerprint}"
        self.run_dir = config.state_root / self.run_id
        self.journal_path = self.run_dir / "journal.sqlite"

    def _ops(self) -> list[dict]:
        return [o for o in self.plan.get("operations", []) if o.get("status") == "COPY_CANDIDATE"]

    def preflight(self) -> dict:
        issues: list[str] = []
        ops = self._ops()
        summary = self.plan.get("summary", {})
        if Path(summary.get("knowledge_root", "")).resolve() != self.c.root:
            issues.append("plan knowledge_root does not match requested root")
        if not self.c.root.is_dir():
            issues.append("knowledge root is not a directory")
        if not self.c.catalog.is_file():
            issues.append("production catalog is missing")
        elif sqlite3.connect(f"file:{self.c.catalog}?mode=ro", uri=True).execute(
            "PRAGMA integrity_check"
        ).fetchone()[0] != "ok":
            issues.append("production catalog integrity_check failed")
        missing = collisions = cross_device = 0
        root_device = self.c.root.stat().st_dev if self.c.root.exists() else None
        for op in ops:
            source, destination = Path(op["source"]), Path(op["destination"])
            if not source.exists() and not destination.exists():
                missing += 1
            if source.exists() and destination.exists() and source.resolve() != destination.resolve():
                collisions += 1
            ancestor = destination.parent
            while not ancestor.exists() and ancestor != ancestor.parent:
                ancestor = ancestor.parent
            if root_device is not None and ancestor.exists() and ancestor.stat().st_dev != root_device:
                cross_device += 1
        if missing:
            issues.append(f"{missing} operations have neither source nor destination")
        if collisions:
            issues.append(f"{collisions} destination collisions")
        if cross_device:
            issues.append(f"{cross_device} operations cross filesystem devices")
        if self.c.batch_size < 1:
            issues.append("batch-size must be positive")
        return {
            "decision": "BLOCKED" if issues else "READY",
            "mode": "APPLY" if self.c.apply else "STRICT_READ_ONLY",
            "run_id": self.run_id,
            "plan": str(self.c.plan),
            "operations": len(ops),
            "already_canonical": int(summary.get("status_counts", {}).get("ALREADY_CANONICAL", 0)),
            "issues": issues,
        }

    def _open_journal(self) -> sqlite3.Connection:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.journal_path)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("""CREATE TABLE IF NOT EXISTS operations(
          seq INTEGER PRIMARY KEY, source TEXT NOT NULL, destination TEXT NOT NULL,
          bytes INTEGER NOT NULL, action TEXT, state TEXT NOT NULL,
          error TEXT, updated_utc TEXT NOT NULL)""")
        db.commit()
        return db

    def _seed(self, journal: sqlite3.Connection, ops: list[dict]) -> None:
        if journal.execute("SELECT COUNT(*) FROM operations").fetchone()[0]:
            return
        journal.executemany(
            "INSERT INTO operations VALUES(?,?,?,?,?,'PLANNED',NULL,?)",
            [(i, o["source"], o["destination"], int(o.get("bytes", 0)), o.get("action"), utc_now())
             for i, o in enumerate(ops)],
        )
        journal.commit()

    def _backup_catalog(self) -> Path:
        baseline = (
            self.c.state_root
            / "migration-048d8b30393a"
            / "catalog-before.sqlite"
        )

        if baseline.is_file():
            reference = self.run_dir / "catalog-backup-reference.txt"
            reference.write_text(str(baseline) + "\n")
            return baseline

        backup = self.run_dir / "catalog-before.sqlite"

        if backup.exists():
            return backup

        source = sqlite3.connect(
            f"file:{self.c.catalog}?mode=ro",
            uri=True,
        )
        target = sqlite3.connect(backup)

        try:
            source.backup(target)
        finally:
            target.close()
            source.close()

        return backup

    @staticmethod
    def _existing_columns(db: sqlite3.Connection) -> dict[str, tuple[str, ...]]:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
        result = {}
        for table, wanted in PATH_COLUMNS.items():
            if table not in tables:
                continue
            actual = {r[1] for r in db.execute(f'PRAGMA table_info("{table}")')}
            found = tuple(c for c in wanted if c in actual)
            if found:
                result[table] = found
        return result

    def _remap_catalog(self, pairs: list[tuple[str, str]]) -> int:
        db = sqlite3.connect(self.c.catalog, timeout=60)
        changed = 0
        try:
            db.execute("BEGIN IMMEDIATE")
            db.execute("CREATE TEMP TABLE path_map(old TEXT PRIMARY KEY, new TEXT NOT NULL)")
            db.executemany("INSERT INTO path_map VALUES(?,?)", pairs)
            for table, columns in self._existing_columns(db).items():
                for column in columns:
                    before = db.total_changes
                    db.execute(f'''UPDATE "{table}" SET "{column}"=(
                      SELECT new FROM path_map WHERE old="{table}"."{column}"
                    ) WHERE "{column}" IN (SELECT old FROM path_map)''')
                    changed += db.total_changes - before
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return changed

    def _rollback_files(self, moved: list[tuple[Path, Path]]) -> None:
        for source, destination in reversed(moved):
            if destination.exists() and not source.exists():
                source.parent.mkdir(parents=True, exist_ok=True)
                os.replace(destination, source)

    def _process_batch(self, journal: sqlite3.Connection, rows: list[tuple]) -> int:
        moved: list[tuple[Path, Path]] = []
        catalog_remapped = False
        seqs = [int(r[0]) for r in rows]
        try:
            for _, source_s, destination_s, *_ in rows:
                source, destination = Path(source_s), Path(destination_s)
                if destination.exists() and not source.exists():
                    moved.append((source, destination))
                    continue
                if not source.is_file() or destination.exists():
                    raise RuntimeError(f"unsafe move state: {source} -> {destination}")
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.replace(source, destination)
                moved.append((source, destination))
            journal.executemany("UPDATE operations SET state='MOVED',updated_utc=? WHERE seq=?",
                                [(utc_now(), s) for s in seqs]); journal.commit()
            self._remap_catalog([(str(a), str(b)) for a, b in moved])
            catalog_remapped = True
            if not all(b.is_file() and not a.exists() for a, b in moved):
                raise RuntimeError("post-move filesystem verification failed")
            journal.executemany("UPDATE operations SET state='VERIFIED',updated_utc=? WHERE seq=?",
                                [(utc_now(), s) for s in seqs]); journal.commit()
            return len(rows)
        except Exception as exc:
            try:
                if catalog_remapped:
                    self._remap_catalog([(str(b), str(a)) for a, b in moved])
                self._rollback_files(moved)
            finally:
                journal.executemany("UPDATE operations SET state='ROLLED_BACK',error=?,updated_utc=? WHERE seq=?",
                                    [(str(exc), utc_now(), s) for s in seqs]); journal.commit()
            raise

    def _run_as1(self) -> dict:
        project = Path(os.environ.get("JARVIS_PROJECT", "/media/abdullah/JARVISDATA/Projects/jarvis-ai"))
        script = project / "dev/run_genesis_as1.py"
        if not script.exists():
            return {"status": "SKIPPED", "reason": "AS1 entrypoint not found"}
        report = self.run_dir / "as1-output.txt"
        legacy_db = self.c.root / ".jarvis" / "catalog.sqlite"
        relocated_legacy_db = (
            self.c.root.parent
            / "Knowledge_Operations"
            / "legacy_jarvis"
            / "catalog.sqlite"
        )
        if not legacy_db.exists() and relocated_legacy_db.exists():
            legacy_db = relocated_legacy_db

        with report.open("w") as out:
            proc = subprocess.run([sys.executable, str(script),
                                   "--knowledge-root", str(self.c.root),
                                   "--runtime-db", str(self.c.catalog),
                                   "--legacy-db", str(legacy_db),
                                   "--json", str(self.run_dir / "as1-report.json")],
                                  cwd=project, stdout=out, stderr=subprocess.STDOUT, text=True)
        return {"status": "COMPLETE" if proc.returncode == 0 else "FAILED",
                "returncode": proc.returncode, "report": str(report)}

    def run(self) -> dict:
        report = self.preflight()
        if not self.c.apply or report["decision"] == "BLOCKED":
            return report
        if self.c.acknowledge != ACK:
            report["decision"] = "BLOCKED"
            report["issues"].append(f"apply requires --acknowledge {ACK}")
            return report
        ops = self._ops()
        journal = self._open_journal()
        try:
            self._seed(journal, ops)
            self._backup_catalog()
            limit = self.c.canary
            completed = 0
            while limit is None or completed < limit:
                take = self.c.batch_size if limit is None else min(self.c.batch_size, limit - completed)
                rows = journal.execute(
                    "SELECT seq,source,destination,bytes,action,state,error,updated_utc "
                    "FROM operations WHERE state IN ('PLANNED','MOVED') ORDER BY seq LIMIT ?", (take,)
                ).fetchall()
                if not rows:
                    break
                completed += self._process_batch(journal, rows)
            counts = dict(journal.execute("SELECT state,COUNT(*) FROM operations GROUP BY state"))
            remaining = sum(v for k, v in counts.items() if k != "VERIFIED")
            report.update({"decision": "COMPLETE" if not remaining else "PARTIAL",
                           "processed_this_invocation": completed,
                           "journal": str(self.journal_path), "states": counts})
            if not remaining and self.c.run_as1:
                report["as1"] = self._run_as1()
            (self.run_dir / "run-report.json").write_text(json.dumps(report, indent=2, sort_keys=True))
            return report
        finally:
            journal.close()
