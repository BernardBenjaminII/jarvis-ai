from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sqlite3
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB = Path(os.environ.get(
    "JARVIS_CATALOG_DB",
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite",
))

TERMS = (
    "search", "retrieve", "retrieval", "ground", "grounding", "evidence",
    "source", "citation", "provenance", "chunk", "embedding", "vector",
    "similarity", "rank", "catalog", "registry", "librarian", "awareness",
    "assimilat", "materializ", "synthesis",
)

EXCLUDED = {
    ".git", ".migration_backups", "__pycache__", ".pytest_cache",
    ".mypy_cache", "node_modules", "dist", "build", "htmlcov", ".venv",
    "venv",
}

@dataclass
class Symbol:
    path: str
    line: int
    kind: str
    name: str
    qualified_name: str
    terms: list[str] = field(default_factory=list)

@dataclass
class Route:
    path: str
    line: int
    method: str
    route: str
    function: str

@dataclass
class Finding:
    code: str
    severity: str
    title: str
    detail: str
    recommendation: str

def source_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED for part in path.parts):
            continue
        if path.suffix.lower() in {".py", ".js", ".html", ".css", ".md", ".sh"}:
            yield path

def matched_terms(text: str) -> list[str]:
    lowered = text.casefold()
    return sorted({term for term in TERMS if term in lowered})

def symbols(root: Path) -> list[Symbol]:
    records: list[Symbol] = []
    for path in source_files(root):
        if path.suffix != ".py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        stack: list[str] = []

        class Visitor(ast.NodeVisitor):
            def visit_ClassDef(self, node):
                qualified = ".".join([*stack, node.name])
                terms = matched_terms(node.name + " " + (ast.get_docstring(node) or ""))
                if terms:
                    records.append(Symbol(
                        str(path.relative_to(root)), node.lineno, "class",
                        node.name, qualified, terms,
                    ))
                stack.append(node.name)
                self.generic_visit(node)
                stack.pop()

            def visit_FunctionDef(self, node):
                qualified = ".".join([*stack, node.name])
                terms = matched_terms(node.name + " " + (ast.get_docstring(node) or ""))
                if terms:
                    records.append(Symbol(
                        str(path.relative_to(root)), node.lineno, "function",
                        node.name, qualified, terms,
                    ))
                stack.append(node.name)
                self.generic_visit(node)
                stack.pop()

            visit_AsyncFunctionDef = visit_FunctionDef

        Visitor().visit(tree)
    return sorted(records, key=lambda item: (item.path, item.line, item.name))

def references(root: Path) -> dict[str, list[dict[str, Any]]]:
    result = {term: [] for term in TERMS}
    for path in source_files(root):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        relative = str(path.relative_to(root))
        for number, line in enumerate(lines, 1):
            lowered = line.casefold()
            for term in TERMS:
                if term in lowered:
                    result[term].append({
                        "path": relative,
                        "line": number,
                        "text": line.strip()[:400],
                    })
    return result

ROUTE_RE = re.compile(
    r"""@router\.(get|post|put|patch|delete|websocket)\(\s*["']([^"']+)["']"""
)
DEF_RE = re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)")

def routes(root: Path) -> list[Route]:
    result: list[Route] = []
    route_root = root / "core/src/routes"
    if not route_root.exists():
        return result
    for path in route_root.rglob("*.py"):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for index, line in enumerate(lines):
            match = ROUTE_RE.search(line)
            if not match:
                continue
            function = "<unknown>"
            for probe in lines[index + 1:index + 12]:
                found = DEF_RE.match(probe)
                if found:
                    function = found.group(1)
                    break
            result.append(Route(
                str(path.relative_to(root)),
                index + 1,
                match.group(1).upper(),
                match.group(2),
                function,
            ))
    return sorted(result, key=lambda item: (item.route, item.method))

def database_inventory(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False, "tables": []}
    tables = []
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        for row in conn.execute(
            "SELECT name, sql FROM sqlite_master "
            "WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        ):
            name = str(row["name"])
            if not any(token in name.casefold() for token in (
                "document", "chunk", "embedding", "index", "catalog",
                "registry", "source", "topic", "concept", "page", "fts",
            )):
                continue
            columns = [
                str(column[1])
                for column in conn.execute(f'PRAGMA table_info("{name}")')
            ]
            try:
                count = int(conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
            except sqlite3.Error:
                count = None
            tables.append({
                "name": name,
                "row_count": count,
                "columns": columns,
                "sql": row["sql"],
            })
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": path.stat().st_size,
        "tables": tables,
    }

def composition(root: Path) -> dict[str, Any]:
    probe = (
        "import json\n"
        "result={}\n"
        "try:\n"
        " from core.src.routes.api import conversation_service\n"
        " result['conversation_service']=type(conversation_service).__name__\n"
        " o=getattr(conversation_service,'orchestrator',None)\n"
        " result['orchestrator']=type(o).__name__ if o else None\n"
        " if o:\n"
        "  for a in ('grounding_service','awareness_service','observability_service','synthesis_handler','director'):\n"
        "   v=getattr(o,a,None); result[a]=type(v).__name__ if v is not None else None\n"
        "  g=getattr(o,'grounding_service',None)\n"
        "  if g:\n"
        "   result['catalog_database']=str(getattr(g,'database_path',''))\n"
        "   result['catalog_exists']=bool(getattr(g,'database_path',None) and g.database_path.exists())\n"
        "except Exception as e:\n"
        " result['error']=type(e).__name__+': '+str(e)\n"
        "print(json.dumps(result))\n"
    )
    completed = subprocess.run(
        [os.environ.get("PYTHON_BIN", "python"), "-c", probe],
        cwd=root, capture_output=True, text=True, timeout=45,
    )
    json_lines = [line for line in completed.stdout.splitlines() if line.strip().startswith("{")]
    if not json_lines:
        return {"error": completed.stderr.strip() or completed.stdout.strip()}
    try:
        return json.loads(json_lines[-1])
    except Exception:
        return {"error": "composition probe returned invalid JSON"}

def findings(symbol_list, ref_map, route_list, db, live):
    found = []
    names = {item.name for item in symbol_list}
    tables = {item["name"]: item for item in db.get("tables", [])}

    expected = {
        "ExecutiveConversationOrchestrator": "conversation orchestration",
        "CatalogGroundingService": "catalog grounding",
        "ExecutiveKnowledgeAwarenessService": "knowledge awareness",
        "RuntimeKnowledgeMaterializer": "runtime materialization",
    }
    for name, purpose in expected.items():
        if name in names:
            found.append(Finding(
                "EXISTING-" + name, "info",
                "Existing " + purpose + " component found",
                name + " already exists.",
                "Reuse and certify it before adding another implementation.",
            ))
        else:
            found.append(Finding(
                "UNPROVEN-" + name, "high",
                purpose.capitalize() + " component not proven",
                "The audit did not identify " + name + ".",
                "Search alternate names and composition paths before writing new code.",
            ))

    if live.get("grounding_service"):
        found.append(Finding(
            "LIVE-GROUNDING-ACTIVE", "info",
            "Grounding is active in the live composition",
            "The orchestrator uses " + str(live["grounding_service"]) + ".",
            "Preserve this integration seam.",
        ))
    else:
        found.append(Finding(
            "LIVE-GROUNDING-INACTIVE", "critical",
            "Grounding is absent from the live composition",
            "No active grounding service was discovered.",
            "Repair dependency injection before retrieval implementation.",
        ))

    rd = tables.get("runtime_documents", {}).get("row_count")
    rc = tables.get("runtime_chunks", {}).get("row_count")
    if rd is not None or rc is not None:
        severity = "info" if (rd or 0) > 0 and (rc or 0) > 0 else "critical"
        found.append(Finding(
            "RUNTIME-CORPUS", severity,
            "Runtime corpus inventory",
            f"runtime_documents={rd}, runtime_chunks={rc}.",
            "Audit retrieval quality next." if severity == "info"
            else "Materialize content before ranking work.",
        ))

    embedding_tables = [
        item for name, item in tables.items()
        if "embedding" in name.casefold()
    ]
    if embedding_tables:
        found.append(Finding(
            "EMBEDDING-ASSETS", "info",
            "Embedding storage already exists",
            ", ".join(
                f"{item['name']}={item.get('row_count')}"
                for item in embedding_tables
            ),
            "Audit producers, dimensions, models, and consumers before adding a new vector store.",
        ))

    route_paths = {item.route for item in route_list}
    if "/api/knowledge/conversation" in route_paths:
        found.append(Finding(
            "WORKSPACE-ENDPOINT", "info",
            "Knowledge Workspace API exists",
            "POST /api/knowledge/conversation is present.",
            "Keep this external contract stable.",
        ))

    if ref_map.get("rank"):
        found.append(Finding(
            "RANKING-REFERENCES", "info",
            "Ranking-related code already exists",
            f"{len(ref_map['rank'])} ranking references were identified.",
            "Inspect and consolidate existing ranking implementations.",
        ))
    else:
        found.append(Finding(
            "RANKING-NOT-PROVEN", "medium",
            "No ranking implementation was proven",
            "No rank references were found.",
            "Verify manually, then define one canonical ranking owner only if needed.",
        ))
    return found

def matrix(symbol_list, ref_map, db):
    names = {item.name for item in symbol_list}
    tables = {item["name"] for item in db.get("tables", [])}
    def state(value): return "existing" if value else "not proven"
    return {
        "Conversation orchestration": {
            "evidence": "ExecutiveConversationOrchestrator",
            "status": state("ExecutiveConversationOrchestrator" in names),
        },
        "Catalog grounding": {
            "evidence": "CatalogGroundingService",
            "status": state("CatalogGroundingService" in names),
        },
        "Knowledge awareness": {
            "evidence": "ExecutiveKnowledgeAwarenessService",
            "status": state("ExecutiveKnowledgeAwarenessService" in names),
        },
        "Runtime materialization": {
            "evidence": "RuntimeKnowledgeMaterializer/runtime_documents",
            "status": state(
                "RuntimeKnowledgeMaterializer" in names
                or "runtime_documents" in tables
            ),
        },
        "Full-text retrieval": {
            "evidence": "search_runtime_knowledge/runtime_chunks_fts",
            "status": state(
                "search_runtime_knowledge" in names
                or "runtime_chunks_fts" in tables
            ),
        },
        "Embedding storage": {
            "evidence": "embedding tables",
            "status": state(any("embedding" in name for name in tables)),
        },
        "Semantic similarity": {
            "evidence": "vector/similarity references",
            "status": state(bool(ref_map.get("vector")) or bool(ref_map.get("similarity"))),
        },
        "Ranking": {
            "evidence": "rank references",
            "status": state(bool(ref_map.get("rank"))),
        },
        "Provenance": {
            "evidence": "source/citation/provenance references",
            "status": state(
                bool(ref_map.get("source"))
                or bool(ref_map.get("citation"))
                or bool(ref_map.get("provenance"))
            ),
        },
    }

def markdown(report):
    lines = [
        "# Genesis IX-A4 — Retrieval Architecture Audit",
        "",
        f"**Generated:** {report['generated_at']}",
        f"**Repository:** `{report['repository_root']}`",
        f"**Catalog:** `{report['database']['path']}`",
        f"**Fingerprint:** `{report['fingerprint']}`",
        "",
        "## Executive Summary",
        "",
    ]
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    ordered = sorted(report["findings"], key=lambda x: (order.get(x["severity"], 99), x["code"]))
    for item in ordered:
        lines.append(f"- **{item['severity'].upper()} — {item['title']}**: {item['detail']}")

    lines += ["", "## Live Composition", ""]
    for key, value in report["composition"].items():
        lines.append(f"- **{key}:** `{value}`")

    lines += [
        "", "## Capability Matrix", "",
        "| Capability | Existing evidence | Status |",
        "|---|---|---|",
    ]
    for capability, data in report["capability_matrix"].items():
        lines.append(f"| {capability} | {data['evidence']} | {data['status']} |")

    lines += [
        "", "## Existing Retrieval Symbols", "",
        "| Source | Line | Kind | Symbol | Terms |",
        "|---|---:|---|---|---|",
    ]
    for item in report["symbols"][:400]:
        lines.append(
            f"| `{item['path']}` | {item['line']} | {item['kind']} | "
            f"`{item['qualified_name']}` | {', '.join(item['terms'])} |"
        )

    lines += [
        "", "## API Routes", "",
        "| Method | Route | Function | Source |",
        "|---|---|---|---|",
    ]
    for item in report["routes"]:
        lines.append(
            f"| {item['method']} | `{item['route']}` | `{item['function']}` | "
            f"`{item['path']}:{item['line']}` |"
        )

    lines += ["", "## Knowledge Database", ""]
    if not report["database"].get("exists"):
        lines.append("Database was not available.")
    else:
        lines += ["| Table | Rows | Columns |", "|---|---:|---|"]
        for item in report["database"]["tables"]:
            lines.append(
                f"| `{item['name']}` | {item['row_count']} | "
                f"{', '.join(item['columns'])} |"
            )

    lines += [
        "", "## Recommended IX-A4 Boundary", "",
        "1. Preserve the existing conversation, grounding, awareness, materialization, and UI contracts.",
        "2. Select one canonical query-planning owner.",
        "3. Consolidate existing FTS, embedding, vector, and ranking implementations.",
        "4. Add new retrieval code only where this audit proves a gap.",
        "5. Project actual evidence, confidence, trace, and provenance into Mission Control.",
        "6. Require grounded-answer end-to-end acceptance tests.",
        "", "## Findings and Actions", "",
    ]
    for item in ordered:
        lines += [
            f"### {item['code']} — {item['title']}",
            "",
            f"- **Severity:** {item['severity']}",
            f"- **Detail:** {item['detail']}",
            f"- **Recommendation:** {item['recommendation']}",
            "",
        ]
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output-dir", type=Path, default=Path("docs/audits"))
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    symbol_list = symbols(root)
    ref_map = references(root)
    route_list = routes(root)
    db = database_inventory(args.database)
    live = composition(root)
    finding_list = findings(symbol_list, ref_map, route_list, db, live)

    report = {
        "schema_version": "genesis_ix_a4_audit_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository_root": str(root),
        "database": db,
        "composition": live,
        "symbols": [asdict(item) for item in symbol_list],
        "routes": [asdict(item) for item in route_list],
        "references": ref_map,
        "capability_matrix": matrix(symbol_list, ref_map, db),
        "findings": [asdict(item) for item in finding_list],
    }
    canonical = json.dumps(report, sort_keys=True)
    report["fingerprint"] = hashlib.sha256(canonical.encode()).hexdigest()

    json_path = output / "genesis_ix_a4_retrieval_architecture.json"
    md_path = output / "genesis_ix_a4_retrieval_architecture.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(markdown(report) + "\n", encoding="utf-8")

    print("=" * 72)
    print("GENESIS IX-A4 — RETRIEVAL ARCHITECTURE AUDIT")
    print("=" * 72)
    print("Symbols    :", len(symbol_list))
    print("Routes     :", len(route_list))
    print("Findings   :", len(finding_list))
    print("Markdown   :", md_path)
    print("JSON       :", json_path)
    print("Fingerprint:", report["fingerprint"])
    print("=" * 72)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
