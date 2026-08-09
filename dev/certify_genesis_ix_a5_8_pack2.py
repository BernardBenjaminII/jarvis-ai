import sqlite3, tempfile
from pathlib import Path
from dev.materializer_eligibility.audit import MaterializerEligibilityAudit

def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        knowledge = root / "Knowledge"
        knowledge.mkdir()
        selected = knowledge / "selected.txt"
        eligible = knowledge / "eligible.md"
        selected.write_text("selected", encoding="utf-8")
        eligible.write_text("eligible", encoding="utf-8")

        runtime = root / "runtime.sqlite"
        c = sqlite3.connect(runtime)
        c.execute("CREATE TABLE knowledge_classifications(id INTEGER PRIMARY KEY,file_path TEXT,status TEXT)")
        c.execute("CREATE TABLE runtime_documents(id INTEGER PRIMARY KEY,file_path TEXT)")
        c.executemany(
            "INSERT INTO knowledge_classifications(file_path,status) VALUES(?,?)",
            [(str(selected), "classified"), (str(eligible), "classified")]
        )
        c.execute("INSERT INTO runtime_documents(file_path) VALUES(?)", (str(selected),))
        c.commit(); c.close()

        inventory = root / "inventory.sqlite"
        c = sqlite3.connect(inventory)
        c.execute("CREATE TABLE documents(id INTEGER PRIMARY KEY,path TEXT)")
        c.commit(); c.close()

        before = runtime.read_bytes()
        report = MaterializerEligibilityAudit(
            project_root=root,
            runtime_catalog=runtime,
            inventory_catalog=inventory,
            knowledge_root=knowledge,
        ).execute()
        checks = {
            "candidates": report.summary["candidate_count"] == 2,
            "materialized": report.summary["already_materialized"] == 1,
            "eligible": report.summary["eligible_not_selected"] == 1,
            "selection_rate": report.summary["selection_rate_among_eligible"] == .5,
            "classification": report.classification == "MATERIALIZER_SELECTION_HEALTHY",
            "read_only": before == runtime.read_bytes(),
            "serialization": report.to_dict()["summary"]["candidate_count"] == 2,
        }
    failed = [name for name, passed in checks.items() if not passed]
    print("=" * 76)
    print("GENESIS IX-A5.8 PACK 2 — CERTIFICATION")
    print("=" * 76)
    print("Checks executed :", len(checks))
    print("Checks passed   :", len(checks) - len(failed))
    print("Checks failed   :", len(failed))
    print("Overall status  :", "EXCELLENT" if not failed else "FAILED")
    if failed:
        print("Failed checks   :", ", ".join(failed))
    print("=" * 76)
    return 0 if not failed else 1

if __name__ == "__main__":
    raise SystemExit(main())
