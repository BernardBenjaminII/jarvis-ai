from __future__ import annotations

import argparse
from collections import Counter

from knowledge_engine.integrity.auditor import KnowledgeIntegrityAuditor


DEFAULT_DB = (
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit JARVIS Knowledge Engine data integrity."
    )

    parser.add_argument(
        "--db",
        default=DEFAULT_DB,
    )

    parser.add_argument(
        "--document-limit",
        type=int,
        default=100,
    )

    parser.add_argument(
        "--chunk-limit",
        type=int,
        default=500,
    )

    parser.add_argument(
        "--show-issues",
        type=int,
        default=25,
    )

    args = parser.parse_args()

    auditor = KnowledgeIntegrityAuditor(args.db)

    report = auditor.run(
        document_limit=args.document_limit,
        chunk_limit=args.chunk_limit,
    )

    print()
    print("=" * 80)
    print("JARVIS KNOWLEDGE INTEGRITY AUDIT")
    print("=" * 80)
    print(f"Database           : {report.database_path}")
    print(f"Documents checked  : {report.documents_checked}")
    print(f"Chunks checked     : {report.chunks_checked}")
    print(f"Embeddings checked : {report.embeddings_checked}")
    print(f"Errors             : {len(report.errors)}")
    print(f"Warnings           : {len(report.warnings)}")
    print(f"Passed             : {report.passed}")

    stage_counts = Counter(
        issue.stage
        for issue in report.issues
    )

    if stage_counts:
        print()
        print("Issues by Stage")
        print("-" * 80)

        for stage, count in sorted(stage_counts.items()):
            print(f"{stage}: {count}")

    if report.issues:
        print()
        print("Issue Details")
        print("-" * 80)

        for index, issue in enumerate(
            report.issues[: args.show_issues],
            start=1,
        ):
            print(
                f"{index}. "
                f"[{issue.severity.upper()}] "
                f"{issue.stage}: {issue.message}"
            )

            if issue.file_path:
                print(f"   File   : {issue.file_path}")

            if issue.record_id:
                print(f"   Record : {issue.record_id}")

            if issue.preview:
                print(f"   Preview: {issue.preview}")

            print()

    print("=" * 80)

    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
