from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .inspection import inspect_components, inspect_runtime, inspect_tables


def _graph(runtime: list[dict[str, Any]], components: list[dict[str, Any]]) -> list[dict[str, str]]:
    bindings = {(x["owner"], x["attribute"]): x for x in runtime}

    def label(owner, attr, fallback):
        item = bindings.get((owner, attr))
        if item and item.get("module") and item.get("type_name"):
            return f"{item['module']}.{item['type_name']}"
        if item and item.get("module") and item.get("callable_name"):
            return f"{item['module']}.{item['callable_name']}"
        return fallback

    conversation = label("application", "conversation_service", "ExecutiveConversationService")
    orchestrator = label("conversation_service", "orchestrator", "ExecutiveConversationOrchestrator")
    grounding = label("orchestrator", "grounding_service", "CatalogGroundingService")
    awareness = label("orchestrator", "awareness_service", "ExecutiveKnowledgeAwarenessService")
    director = label("orchestrator", "director", "ExecutiveDirector")
    synthesis = label("orchestrator", "synthesis_handler", "synthesis_handler")
    catalog = label("retrieval", "search_catalog", "search_catalog")
    runtime_search = label("retrieval", "search_runtime_knowledge", "search_runtime_knowledge")

    edges = [
        {"source": conversation, "target": orchestrator, "relation": "injects", "evidence": "runtime binding"},
        {"source": orchestrator, "target": grounding, "relation": "injects", "evidence": "runtime binding"},
        {"source": orchestrator, "target": awareness, "relation": "injects", "evidence": "runtime binding"},
        {"source": orchestrator, "target": director, "relation": "injects", "evidence": "runtime binding"},
        {"source": orchestrator, "target": synthesis, "relation": "injects", "evidence": "runtime binding"},
        {"source": grounding, "target": catalog, "relation": "calls", "evidence": "bound search handler"},
        {"source": catalog, "target": runtime_search, "relation": "delegates", "evidence": "canonical search path"},
        {"source": runtime_search, "target": "SQLite runtime_chunks_fts", "relation": "queries", "evidence": "FTS"},
        {"source": grounding, "target": awareness, "relation": "provides", "evidence": "GroundingResult"},
        {"source": grounding, "target": synthesis, "relation": "augments", "evidence": "synthesis_input"},
    ]
    seen = {(x["source"], x["target"], x["relation"]) for x in edges}
    for item in components:
        source = f"{item['module']}.{item['name']}"
        for callee in item["callees"]:
            key = (source, callee, "calls")
            if key not in seen:
                seen.add(key)
                edges.append({
                    "source": source, "target": callee, "relation": "calls",
                    "evidence": f"{item['path']}:{item['line']}",
                })
    return edges

def _capabilities(components, runtime, tables):
    by_category: dict[str, list[dict[str, Any]]] = {}
    for item in components:
        by_category.setdefault(item["category"], []).append(item)
    live_modules = {x.get("module") for x in runtime if x.get("module")}
    table_map = {x["name"]: x for x in tables}

    definitions = {
        "Executive retrieval": ("grounding",),
        "Catalog retrieval": ("retrieval",),
        "Knowledge registry": ("registry",),
        "Chunk retrieval": ("chunking", "full_text"),
        "Embedding retrieval": ("embedding", "semantic_similarity"),
        "Full-text retrieval": ("full_text",),
        "Hybrid retrieval": ("hybrid", "reranking"),
        "Citation pipeline": ("evidence",),
        "Retrieval cache": ("cache",),
    }
    result = []
    for capability, categories in definitions.items():
        members = [m for c in categories for m in by_category.get(c, [])]
        present = bool(members)
        used = any(m["module"] in live_modules or m["status"] == "LIVE" for m in members)
        if capability == "Chunk retrieval":
            used = used or ((table_map.get("runtime_chunks") or {}).get("row_count") or 0) > 0
        if capability == "Full-text retrieval":
            used = used or ((table_map.get("runtime_chunks_fts") or {}).get("row_count") or 0) > 0
        if capability == "Embedding retrieval":
            present = present or ((table_map.get("chunk_embeddings") or {}).get("row_count") or 0) > 0
        certified = used and capability in {
            "Executive retrieval", "Catalog retrieval", "Chunk retrieval",
            "Full-text retrieval", "Citation pipeline",
        }
        result.append({
            "capability": capability, "present": present, "used": used,
            "certified": certified,
            "evidence": sorted({f"{m['module']}.{m['name']}" for m in members[:20]}),
        })
    return result

def build_inventory(repository_root: Path, catalog_database: Path | None) -> dict[str, Any]:
    root = repository_root.resolve()
    components = inspect_components(root)
    runtime = inspect_runtime(root)
    tables = inspect_tables(catalog_database, components)
    graph_edges = _graph(runtime, components)
    capabilities = _capabilities(components, runtime, tables)
    return {
        "schema_version": "genesis_ix_a4_2a_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository_root": str(root),
        "catalog_database": str(catalog_database) if catalog_database else None,
        "components": components,
        "runtime_bindings": runtime,
        "tables": tables,
        "graph_edges": graph_edges,
        "capabilities": capabilities,
        "summary": {
            "component_count": len(components),
            "live_component_count": sum(x["status"] == "LIVE" for x in components),
            "runtime_binding_count": len(runtime),
            "table_count": len(tables),
            "populated_table_count": sum((x["row_count"] or 0) > 0 for x in tables),
            "graph_edge_count": len(graph_edges),
            "capability_count": len(capabilities),
            "certified_capability_count": sum(x["certified"] for x in capabilities),
        },
    }
