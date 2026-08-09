from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from core.knowledge_catalog.materialization_campaign.candidates import (
    discover_candidates,
)
from core.knowledge_catalog.materialization_campaign.checkpoint import (
    CheckpointStore,
)
from core.knowledge_catalog.materialization_campaign.contracts import (
    CandidateDisposition,
    CandidateResult,
)


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        knowledge = root / "Knowledge"
        knowledge.mkdir()
        selected = knowledge / "selected.txt"
        pending = knowledge / "pending.md"
        selected.write_text(
            "selected",
            encoding="utf-8",
        )
        pending.write_text(
            "pending",
            encoding="utf-8",
        )

        runtime = root / "runtime.sqlite"
        connection = sqlite3.connect(runtime)
        connection.execute(
            """
            CREATE TABLE knowledge_classifications(
                id INTEGER PRIMARY KEY,
                file_path TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE runtime_documents(
                id INTEGER PRIMARY KEY,
                file_path TEXT
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO knowledge_classifications(
                file_path
            )
            VALUES(?)
            """,
            (
                (str(selected),),
                (str(pending),),
            ),
        )
        connection.execute(
            """
            INSERT INTO runtime_documents(file_path)
            VALUES(?)
            """,
            (str(selected),),
        )
        connection.commit()
        connection.close()

        inventory = root / "inventory.sqlite"
        connection = sqlite3.connect(inventory)
        connection.execute(
            "CREATE TABLE documents(id INTEGER PRIMARY KEY,path TEXT)"
        )
        connection.commit()
        connection.close()

        before = runtime.read_bytes()
        candidates = discover_candidates(
            runtime_catalog=runtime,
            inventory_catalog=inventory,
            knowledge_root=knowledge,
        )
        checkpoint = CheckpointStore(
            root / "checkpoint.sqlite"
        )
        inserted = checkpoint.register_candidates(
            candidates
        )
        next_batch = checkpoint.next_candidates(
            limit=100,
            retry_failures=False,
        )
        checkpoint.record_result(
            CandidateResult(
                candidate_id=next_batch[0].candidate_id,
                path=next_batch[0].path,
                disposition=(
                    CandidateDisposition.MATERIALIZED
                ),
                detail="certified",
            )
        )

        checks = {
            "candidate_discovery": len(candidates) == 1,
            "existing_excluded": (
                candidates[0].path == str(pending)
            ),
            "checkpoint_insert": inserted == 1,
            "batch_resume": len(next_batch) == 1,
            "result_recorded": (
                checkpoint.disposition_counts().get(
                    "MATERIALIZED"
                )
                == 1
            ),
            "production_catalog_unchanged": (
                before == runtime.read_bytes()
            ),
            "checkpoint_separate": (
                checkpoint.path != runtime
            ),
            "checkpoint_exists": (
                checkpoint.path.is_file()
            ),
        }

    failed = [
        name
        for name, passed in checks.items()
        if not passed
    ]

    print("=" * 76)
    print("GENESIS IX-A6 — FULL CORPUS MATERIALIZATION CERTIFICATION")
    print("=" * 76)
    print("Checks executed :", len(checks))
    print("Checks passed   :", len(checks) - len(failed))
    print("Checks failed   :", len(failed))
    print(
        "Overall status  :",
        "EXCELLENT" if not failed else "FAILED",
    )

    if failed:
        print(
            "Failed checks   :",
            ", ".join(failed),
        )

    print("=" * 76)

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
