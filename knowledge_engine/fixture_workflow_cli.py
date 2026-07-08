from __future__ import annotations

import argparse

from knowledge_engine.workflows.fixture_ingest import run_fixture_ingest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the Phase 3A fixture Knowledge Workflow."
    )
    parser.add_argument("source_path")

    args = parser.parse_args()

    context, report = run_fixture_ingest(args.source_path)
    report.print()

    if context.ok:
        print()
        print("Context Summary")
        print("-" * 70)
        print(f"Content type : {context.content_type}")
        print(f"Text length  : {len(context.extracted_text)}")
        print(f"Chunks       : {len(context.chunks)}")
        print(f"Embeddings   : {len(context.embeddings)}")
        print(f"Registry IDs : {len(context.registry_ids)}")
        print(f"Retrieval OK : {context.metadata.get('retrieval_verified', False)}")

    return 0 if report.passed and context.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
