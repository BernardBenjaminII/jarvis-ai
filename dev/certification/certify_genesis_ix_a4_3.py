from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def locate_root() -> Path:
    current = Path(__file__).resolve()

    for candidate in (current.parent, *current.parents):
        if all(
            (candidate / name).is_dir()
            for name in ("core", "dev", "docs")
        ):
            candidate_text = str(candidate)
            if candidate_text not in sys.path:
                sys.path.insert(0, candidate_text)
            return candidate

    raise RuntimeError("Unable to locate the JARVIS project root.")


PROJECT_ROOT = locate_root()

from core.certification.runtime import CertificationRuntime
from core.retrieval.certification import EndToEndRetrievalTracer


def render_certification(data: dict) -> str:
    lines = [
        "# Genesis IX-A4.3 — End-to-End Retrieval Certification",
        "",
        f"**Status:** **{data['status']}**",
        f"**Generated:** {data['generated_at']}",
        f"**Known query:** `{data['known_query']}`",
        f"**Gap query:** `{data['gap_query']}`",
        "",
        "## Summary",
        "",
        f"- Checks executed: **{data['checks_executed']}**",
        f"- Checks passed: **{data['checks_passed']}**",
        f"- Checks failed: **{data['checks_failed']}**",
        "",
        "## Certified Path",
        "",
        "```text",
        "Operator question",
        "    ↓",
        "ExecutiveConversationService",
        "    ↓",
        "ExecutiveConversationOrchestrator",
        "    ↓",
        "CatalogGroundingService",
        "    ↓",
        "search_catalog",
        "    ↓",
        "search_runtime_knowledge",
        "    ↓",
        "runtime_chunks_fts",
        "    ↓",
        "GroundingResult / KnowledgeGap",
        "    ↓",
        "ExecutiveKnowledgeAwarenessService",
        "    ↓",
        "ExecutiveDirector",
        "    ↓",
        "grounded synthesis prompt",
        "```",
        "",
        "## Checks",
        "",
        "| Code | Check | Status | Detail |",
        "|---|---|---|---|",
    ]

    for item in data["checks"]:
        lines.append(
            f"| `{item['code']}` | {item['label']} | "
            f"**{item['status']}** | {item['detail']} |"
        )

    return "\n".join(lines) + "\n"


def render_trace(title: str, trace: dict) -> str:
    lines = [
        f"# {title}",
        "",
        f"**Query:** `{trace.get('query')}`",
        f"**Prompt length:** {trace.get('prompt_length')}",
        f"**Prompt SHA-256:** `{trace.get('prompt_sha256')}`",
        "",
        "## Conversation Trace",
        "",
        "```json",
        json.dumps(trace.get("trace") or [], indent=2, sort_keys=True),
        "```",
        "",
        "## Grounding Metadata",
        "",
        "```json",
        json.dumps(trace.get("grounding") or {}, indent=2, sort_keys=True),
        "```",
        "",
        "## Captured Grounded Prompt",
        "",
        "```text",
        str(trace.get("prompt") or ""),
        "```",
    ]
    return "\n".join(lines) + "\n"


def render_stage_matrix(data: dict) -> str:
    stage_checks = {
        "Conversation": "RUNTIME-CONVERSATION",
        "Orchestration": "RUNTIME-ORCHESTRATOR",
        "Grounding": "RUNTIME-GROUNDING",
        "Catalog retrieval": "KNOWN-EVIDENCE",
        "Grounded prompt": "KNOWN-GROUNDING-MARKER",
        "Knowledge awareness": "RUNTIME-AWARENESS",
        "Executive Director": "RUNTIME-DIRECTOR",
        "Synthesis": "KNOWN-SYNTHESIS",
        "Gap handling": "GAP-DECLARATION",
    }
    checks = {
        item["code"]: item
        for item in data["checks"]
    }

    lines = [
        "# Genesis IX-A4.3 — Stage Matrix",
        "",
        "| Stage | Certified | Evidence |",
        "|---|---|---|",
    ]

    for stage, code in stage_checks.items():
        item = checks.get(code, {})
        lines.append(
            f"| {stage} | {item.get('status') == 'PASS'} | "
            f"`{code}` — {item.get('detail', '')} |"
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/audits/genesis_ix_a4_3"),
    )
    args = parser.parse_args()

    runtime = CertificationRuntime(start=args.root).bootstrap()
    bootstrap = runtime.certify()

    catalog = (
        Path(bootstrap.catalog_database)
        if bootstrap.catalog_database
        else None
    )

    report = EndToEndRetrievalTracer(
        repository_root=Path(bootstrap.repository_root),
        catalog_database=catalog,
    ).certify()

    data = report.to_dict()

    output = args.output_dir
    if not output.is_absolute():
        output = Path(bootstrap.repository_root) / output
    output.mkdir(parents=True, exist_ok=True)

    (output / "end_to_end_certification.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "end_to_end_certification.md").write_text(
        render_certification(data),
        encoding="utf-8",
    )
    (output / "known_retrieval_trace.md").write_text(
        render_trace("Known Retrieval Trace", data["known_trace"]),
        encoding="utf-8",
    )
    (output / "gap_retrieval_trace.md").write_text(
        render_trace("Knowledge Gap Trace", data["gap_trace"]),
        encoding="utf-8",
    )
    (output / "stage_matrix.md").write_text(
        render_stage_matrix(data),
        encoding="utf-8",
    )
    (output / "grounded_prompt_contract.md").write_text(
        "# Grounded Prompt Contract\n\n"
        "The known and gap traces preserve the exact prompt supplied to the "
        "temporary deterministic synthesis handler. No external model is "
        "invoked during certification.\n",
        encoding="utf-8",
    )

    print("=" * 76)
    print("GENESIS IX-A4.3 — END-TO-END RETRIEVAL CERTIFICATION")
    print("=" * 76)
    print("Known query     :", data["known_query"])
    print("Checks executed :", data["checks_executed"])
    print("Checks passed   :", data["checks_passed"])
    print("Checks failed   :", data["checks_failed"])
    print("Overall status  :", data["status"])
    print("Output          :", output)
    print("=" * 76)

    return 0 if data["status"] == "EXCELLENT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
