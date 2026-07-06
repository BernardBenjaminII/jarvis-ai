from __future__ import annotations

import argparse
import json
from pathlib import Path

from knowledge_engine.doctor.checks import run_checks
from knowledge_engine.doctor.report import render_report
from knowledge_engine.storage.database import KnowledgeDatabase


def main() -> None:
    parser = argparse.ArgumentParser(description="Run JARVIS Knowledge Engine Doctor")
    parser.add_argument("--db", required=True)
    parser.add_argument(
        "--faiss-dir",
        default="/media/abdullah/JARVIS_RUNTIME_L/vector_db/faiss",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", default=None)

    args = parser.parse_args()

    db = KnowledgeDatabase(args.db)

    with db.connect() as conn:
        report = run_checks(conn, faiss_dir=args.faiss_dir)

    if args.json:
        output = json.dumps(report, indent=2)
    else:
        output = render_report(report)

    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding="utf-8")
        print(f"Wrote {path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
