from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path(
    "docs/audits/genesis_ix_a4_1b_pack1/retrieval_runtime_inventory.json"
)
DEFAULT_OUTPUT = Path(
    "docs/audits/genesis_ix_a4_1b_pack2"
)


@dataclass(frozen=True)
class DuplicateCandidate:
    category: str
    signature: str
    members: tuple[str, ...]
    recommendation: str


@dataclass(frozen=True)
class CanonicalDecision:
    component: str
    module: str
    status: str
    decision: str
    rationale: str


def load_inventory(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Pack 1 inventory not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "genesis_ix_a4_1b_pack1_v1":
        raise ValueError(
            "Unsupported Pack 1 schema: "
            f"{data.get('schema_version')!r}"
        )
    return data


def component_key(item: dict[str, Any]) -> tuple[str, str]:
    return (
        str(item.get("module") or ""),
        str(item.get("qualified_name") or ""),
    )


def function_category(item: dict[str, Any]) -> str:
    text = " ".join(
        [
            str(item.get("qualified_name") or ""),
            " ".join(item.get("terms") or []),
        ]
    ).casefold()

    if "embedding" in text or "embed" in text:
        return "embedding"
    if "rerank" in text:
        return "reranking"
    if "similarity" in text or "cosine" in text or "vector" in text:
        return "semantic_similarity"
    if "bm25" in text or "fts" in text:
        return "full_text_ranking"
    if "rank" in text or "score" in text:
        return "ranking"
    if "ground" in text:
        return "grounding"
    if "retrieve" in text or "search" in text:
        return "retrieval"
    if "chunk" in text:
        return "chunking"
    if "evidence" in text or "provenance" in text:
        return "evidence"
    return "other"


def duplicate_candidates(
    functions: list[dict[str, Any]],
) -> list[DuplicateCandidate]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for item in functions:
        if item.get("runtime_status") == "AUXILIARY":
            continue

        category = function_category(item)
        name = str(item.get("qualified_name") or "").split(".")[-1]
        signature = (
            name.casefold(),
            ",".join(item.get("parameters") or []),
            str(item.get("returns") or ""),
        )
        groups[(category, repr(signature))].append(item)

    results: list[DuplicateCandidate] = []

    for (category, signature), members in groups.items():
        unique_modules = {
            str(item.get("module") or "")
            for item in members
        }
        if len(unique_modules) < 2:
            continue

        member_labels = tuple(
            sorted(
                f"{item.get('qualified_name')} "
                f"({item.get('path')}:{item.get('line')}, "
                f"{item.get('runtime_status')})"
                for item in members
            )
        )

        canonical_members = [
            item for item in members
            if item.get("runtime_status") == "CANONICAL"
        ]

        if len(canonical_members) == 1:
            recommendation = (
                "KEEP the single canonical implementation. "
                "Review dormant implementations for adapter value, "
                "then merge or remove."
            )
        elif len(canonical_members) > 1:
            recommendation = (
                "Multiple runtime-active implementations exist. "
                "Define one owner and convert the others to explicit adapters."
            )
        else:
            recommendation = (
                "No live owner was proven. Confirm consumers before selecting "
                "or implementing a canonical service."
            )

        results.append(
            DuplicateCandidate(
                category=category,
                signature=signature,
                members=member_labels,
                recommendation=recommendation,
            )
        )

    return sorted(
        results,
        key=lambda item: (item.category, item.signature),
    )


def canonical_decisions(
    functions: list[dict[str, Any]],
) -> list[CanonicalDecision]:
    results: list[CanonicalDecision] = []

    for item in functions:
        status = str(item.get("runtime_status") or "UNKNOWN")
        module = str(item.get("module") or "")
        name = str(item.get("qualified_name") or "")
        category = function_category(item)

        if status == "CANONICAL":
            decision = "KEEP"
            rationale = (
                "Live runtime identity proves this implementation participates "
                "in the active retrieval path."
            )
        elif status == "AUXILIARY":
            decision = "KEEP-AUXILIARY"
            rationale = (
                "Development or verification utility. It is not a production "
                "runtime owner."
            )
        elif category in {
            "embedding",
            "semantic_similarity",
            "reranking",
            "ranking",
        }:
            decision = "AUDIT"
            rationale = (
                "Capability exists statically but is not proven live. "
                "Inspect callers, data coverage, and compatibility before "
                "activation or removal."
            )
        else:
            decision = "DORMANT"
            rationale = (
                "Static implementation found outside the proven live runtime path."
            )

        results.append(
            CanonicalDecision(
                component=name,
                module=module,
                status=status,
                decision=decision,
                rationale=rationale,
            )
        )

    return sorted(
        results,
        key=lambda item: (
            item.decision,
            item.module,
            item.component,
        ),
    )


def table_map(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["name"]): item
        for item in inventory.get("database", {}).get("tables", [])
    }


def embedding_coverage(inventory: dict[str, Any]) -> dict[str, Any]:
    tables = table_map(inventory)

    chunk_counts = {
        name: int(item.get("row_count") or 0)
        for name, item in tables.items()
        if "chunk" in name.casefold()
        and "embedding" not in name.casefold()
        and not name.casefold().endswith("_fts_config")
        and not name.casefold().endswith("_fts_data")
        and not name.casefold().endswith("_fts_docsize")
        and not name.casefold().endswith("_fts_idx")
        and not name.casefold().endswith("_fts_content")
    }
    embedding_counts = {
        name: int(item.get("row_count") or 0)
        for name, item in tables.items()
        if "embedding" in name.casefold()
    }

    primary_chunks = 0
    for candidate in (
        "runtime_chunks",
        "chunks",
        "document_chunks",
    ):
        if candidate in chunk_counts:
            primary_chunks = max(primary_chunks, chunk_counts[candidate])

    primary_embeddings = max(embedding_counts.values(), default=0)

    coverage = (
        round((primary_embeddings / primary_chunks) * 100.0, 3)
        if primary_chunks
        else 0.0
    )

    return {
        "chunk_tables": chunk_counts,
        "embedding_tables": embedding_counts,
        "primary_chunk_count": primary_chunks,
        "primary_embedding_count": primary_embeddings,
        "coverage_percent": coverage,
        "status": (
            "complete"
            if primary_chunks and primary_embeddings >= primary_chunks
            else "partial"
            if primary_embeddings
            else "absent"
        ),
    }


def certified_runtime_edges(
    inventory: dict[str, Any],
) -> list[tuple[str, str, str]]:
    runtime = inventory.get("runtime", {})
    edges: list[tuple[str, str, str]] = []

    objects = {
        (
            str(item.get("owner") or ""),
            str(item.get("attribute") or ""),
        ): item
        for item in runtime.get("objects", [])
    }

    service = objects.get(("application", "conversation_service"))
    orchestrator = objects.get(("conversation_service", "orchestrator"))
    grounding = objects.get(("orchestrator", "grounding_service"))
    awareness = objects.get(("orchestrator", "awareness_service"))
    director = objects.get(("orchestrator", "director"))
    synthesis = objects.get(("orchestrator", "synthesis_handler"))

    def label(item: dict[str, Any] | None, fallback: str) -> str:
        if not item or not item.get("type_name"):
            return fallback
        return (
            f"{item['module']}.{item['type_name']}"
            if item.get("module")
            else str(item["type_name"])
        )

    service_label = label(
        service,
        "core.conversation.service.ExecutiveConversationService",
    )
    orchestrator_label = label(
        orchestrator,
        "core.conversation.orchestrator.ExecutiveConversationOrchestrator",
    )
    grounding_label = label(
        grounding,
        "core.conversation.grounding.CatalogGroundingService",
    )
    awareness_label = label(
        awareness,
        "core.knowledge_awareness.service.ExecutiveKnowledgeAwarenessService",
    )
    director_label = label(
        director,
        "core.executive.director.ExecutiveDirector",
    )
    synthesis_label = label(
        synthesis,
        "synthesis_handler",
    )

    edges.extend(
        [
            (
                service_label,
                orchestrator_label,
                "live dependency injection",
            ),
            (
                orchestrator_label,
                grounding_label,
                "live dependency injection",
            ),
            (
                orchestrator_label,
                awareness_label,
                "live dependency injection",
            ),
            (
                orchestrator_label,
                director_label,
                "live dependency injection",
            ),
            (
                orchestrator_label,
                synthesis_label,
                "live dependency injection",
            ),
        ]
    )

    search_functions = runtime.get("search_functions", [])
    by_qualname = {
        str(item.get("qualname")): item
        for item in search_functions
    }

    canonical_search = by_qualname.get("search_catalog")
    runtime_search = by_qualname.get("search_runtime_knowledge")

    if canonical_search:
        search_label = (
            f"{canonical_search.get('module')}."
            f"{canonical_search.get('qualname')}"
        )
        edges.append(
            (
                grounding_label,
                search_label,
                "bound search handler",
            )
        )
    else:
        search_label = "core.knowledge_catalog.search.search_catalog"

    if runtime_search:
        runtime_label = (
            f"{runtime_search.get('module')}."
            f"{runtime_search.get('qualname')}"
        )
        edges.append(
            (
                search_label,
                runtime_label,
                "canonical search delegation",
            )
        )

    edges.extend(
        [
            (
                "core.knowledge_catalog.materialization.search.search_runtime_knowledge",
                "SQLite runtime_chunks_fts",
                "full-text retrieval",
            ),
            (
                grounding_label,
                awareness_label,
                "grounding assessment",
            ),
            (
                grounding_label,
                synthesis_label,
                "grounding.synthesis_input()",
            ),
        ]
    )

    return edges


def render_runtime_graph(
    inventory: dict[str, Any],
) -> str:
    edges = certified_runtime_edges(inventory)

    node_ids: dict[str, str] = {}
    for source, target, _ in edges:
        for value in (source, target):
            if value not in node_ids:
                node_ids[value] = f"N{len(node_ids) + 1}"

    lines = [
        "# Genesis IX-A4.1B — Certified Retrieval Runtime Graph",
        "",
        "```mermaid",
        "flowchart TD",
    ]

    for label, node_id in node_ids.items():
        safe = label.replace('"', "'")
        lines.append(f'    {node_id}["{safe}"]')

    for source, target, evidence in edges:
        lines.append(
            f"    {node_ids[source]} -->|{evidence}| {node_ids[target]}"
        )

    lines.extend(
        [
            "```",
            "",
            "## Certified edges",
            "",
            "| Source | Target | Evidence |",
            "|---|---|---|",
        ]
    )
    for source, target, evidence in edges:
        lines.append(
            f"| `{source}` | `{target}` | {evidence} |"
        )

    return "\n".join(lines)


def render_component_matrix(
    decisions: list[CanonicalDecision],
) -> str:
    lines = [
        "# Genesis IX-A4.1B — Retrieval Component Matrix",
        "",
        "| Component | Module | Runtime status | Decision | Rationale |",
        "|---|---|---|---|---|",
    ]

    for item in decisions:
        lines.append(
            f"| `{item.component}` | `{item.module}` | "
            f"{item.status} | **{item.decision}** | "
            f"{item.rationale} |"
        )

    return "\n".join(lines)


def render_duplicates(
    duplicates: list[DuplicateCandidate],
) -> str:
    lines = [
        "# Genesis IX-A4.1B — Production Duplicate Analysis",
        "",
    ]

    if not duplicates:
        lines.append(
            "No production duplicate candidates were identified after "
            "historical trees, tests, archives, and payloads were excluded."
        )
        return "\n".join(lines)

    for item in duplicates:
        lines.extend(
            [
                f"## {item.category.replace('_', ' ').title()}",
                "",
                f"**Signature:** `{item.signature}`",
                "",
            ]
        )
        for member in item.members:
            lines.append(f"- `{member}`")
        lines.extend(
            [
                "",
                f"**Recommendation:** {item.recommendation}",
                "",
            ]
        )

    return "\n".join(lines)


def render_embedding_report(
    coverage: dict[str, Any],
) -> str:
    lines = [
        "# Genesis IX-A4.1B — Embedding Coverage",
        "",
        f"- Primary chunks: **{coverage['primary_chunk_count']}**",
        f"- Primary embeddings: **{coverage['primary_embedding_count']}**",
        f"- Coverage: **{coverage['coverage_percent']}%**",
        f"- Status: **{coverage['status']}**",
        "",
        "## Chunk tables",
        "",
        "| Table | Rows |",
        "|---|---:|",
    ]

    for name, count in sorted(coverage["chunk_tables"].items()):
        lines.append(f"| `{name}` | {count} |")

    lines.extend(
        [
            "",
            "## Embedding tables",
            "",
            "| Table | Rows |",
            "|---|---:|",
        ]
    )

    for name, count in sorted(coverage["embedding_tables"].items()):
        lines.append(f"| `{name}` | {count} |")

    return "\n".join(lines)


def render_table_ownership(
    inventory: dict[str, Any],
) -> str:
    ownership = inventory.get("table_ownership", {})
    table_rows = {
        item["name"]: item.get("row_count")
        for item in inventory.get("database", {}).get("tables", [])
    }

    lines = [
        "# Genesis IX-A4.1B — Retrieval Table Ownership",
        "",
        "| Table | Rows | Readers | Writers | State |",
        "|---|---:|---:|---:|---|",
    ]

    for table, owners in sorted(ownership.items()):
        readers = owners.get("readers") or []
        writers = owners.get("writers") or []
        rows = table_rows.get(table)

        if readers and writers:
            state = "active"
        elif readers:
            state = "read-only"
        elif writers:
            state = "write-only"
        else:
            state = "unowned"

        lines.append(
            f"| `{table}` | {rows} | {len(readers)} | "
            f"{len(writers)} | {state} |"
        )

    lines.extend(["", "## Detailed ownership", ""])

    for table, owners in sorted(ownership.items()):
        lines.append(f"### `{table}`")
        lines.append("")
        lines.append("**Readers**")
        if owners.get("readers"):
            for reader in owners["readers"]:
                lines.append(f"- `{reader}`")
        else:
            lines.append("- None discovered")

        lines.append("")
        lines.append("**Writers**")
        if owners.get("writers"):
            for writer in owners["writers"]:
                lines.append(f"- `{writer}`")
        else:
            lines.append("- None discovered")
        lines.append("")

    return "\n".join(lines)


def render_canonicalization(
    decisions: list[CanonicalDecision],
    coverage: dict[str, Any],
) -> str:
    counts: dict[str, int] = defaultdict(int)
    for item in decisions:
        counts[item.decision] += 1

    lines = [
        "# Genesis IX-A4.1B — Retrieval Canonicalization Report",
        "",
        "## Decision summary",
        "",
        "| Decision | Count |",
        "|---|---:|",
    ]

    for decision, count in sorted(counts.items()):
        lines.append(f"| {decision} | {count} |")

    lines.extend(
        [
            "",
            "## Certified canonical path",
            "",
            "```text",
            "ExecutiveConversationService",
            "    ↓",
            "ExecutiveConversationOrchestrator",
            "    ↓",
            "CatalogGroundingService",
            "    ↓",
            "core.knowledge_catalog.search.search_catalog",
            "    ↓",
            "core.knowledge_catalog.materialization.search.search_runtime_knowledge",
            "    ↓",
            "runtime_chunks_fts",
            "    ↓",
            "GroundingResult",
            "    ↓",
            "ExecutiveKnowledgeAwarenessService",
            "    ↓",
            "ExecutiveDirector + synthesis_handler",
            "```",
            "",
            "## Immediate recommendations",
            "",
            "1. Keep the current FTS-backed retrieval path as the Mark I canonical baseline.",
            "2. Do not activate dormant semantic or reranking implementations until their contracts and consumers are certified.",
            f"3. Embedding coverage is currently **{coverage['coverage_percent']}%**; complete or intentionally scope the embedding pipeline before enabling semantic retrieval.",
            "4. Treat unowned database tables as audit targets, not automatic deletion candidates.",
            "5. Add observability only after the retrieval ownership map is accepted.",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Genesis IX-A4.1B Pack 2 report generator"
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    inventory = load_inventory(args.input)
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    functions = inventory.get("classified_functions", [])
    duplicates = duplicate_candidates(functions)
    decisions = canonical_decisions(functions)
    coverage = embedding_coverage(inventory)

    reports = {
        "retrieval_runtime_graph.md": render_runtime_graph(inventory),
        "retrieval_component_matrix.md": render_component_matrix(decisions),
        "retrieval_duplicate_report.md": render_duplicates(duplicates),
        "retrieval_embedding_coverage.md": render_embedding_report(coverage),
        "retrieval_table_ownership.md": render_table_ownership(inventory),
        "retrieval_canonicalization_report.md": render_canonicalization(
            decisions,
            coverage,
        ),
    }

    summary = {
        "schema_version": "genesis_ix_a4_1b_pack2_v1",
        "source_inventory": str(args.input),
        "duplicate_candidates": [asdict(item) for item in duplicates],
        "canonical_decisions": [asdict(item) for item in decisions],
        "embedding_coverage": coverage,
        "runtime_edges": [
            {
                "source": source,
                "target": target,
                "evidence": evidence,
            }
            for source, target, evidence in certified_runtime_edges(inventory)
        ],
        "reports": sorted(reports),
    }

    for name, content in reports.items():
        (output / name).write_text(
            content.rstrip() + "\n",
            encoding="utf-8",
        )

    (output / "retrieval_report_manifest.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("=" * 76)
    print("GENESIS IX-A4.1B PACK 2 — RETRIEVAL REPORTS")
    print("=" * 76)
    print("Duplicate candidates :", len(duplicates))
    print("Canonical decisions  :", len(decisions))
    print("Embedding coverage   :", coverage["coverage_percent"])
    print("Reports              :", len(reports))
    print("Output               :", output)
    print("=" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
