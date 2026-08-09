from __future__ import annotations

import ast
import json
import os
import re
import sqlite3
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

PRODUCTION_ROOTS = ("core", "knowledge_engine")
EXCLUDED = {
    ".git", ".migration_backups", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".venv", "venv", "node_modules", "dist", "build",
    "archive", "archives", "artifacts", "payload", "payloads", "tests",
}
EXCLUDED_PREFIXES = ("genesis_", "jarvis_convergence_", "architecture_contract_")
TERMS = (
    "search", "retrieve", "retrieval", "rank", "rerank", "score",
    "similarity", "cosine", "vector", "embedding", "embed", "fts",
    "bm25", "chunk", "catalog", "registry", "grounding", "evidence",
    "citation", "provenance", "cache", "memoize", "lru_cache", "redis",
    "semantic", "hybrid", "fusion",
)
TABLE_HINTS = (
    "document", "chunk", "embedding", "vector", "index", "catalog",
    "registry", "source", "page", "fts", "assimilation",
)
READ_RE = re.compile(r"\b(?:FROM|JOIN)\s+[\"'`]?([A-Za-z_][A-Za-z0-9_]*)", re.I)
WRITE_RE = re.compile(
    r"\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM|REPLACE\s+INTO)\s+[\"'`]?"
    r"([A-Za-z_][A-Za-z0-9_]*)",
    re.I,
)

def _excluded(path: Path, root: Path) -> bool:
    for part in path.relative_to(root).parts:
        if part in EXCLUDED:
            return True
        if any(part.casefold().startswith(prefix) for prefix in EXCLUDED_PREFIXES):
            return True
    return False

def _files(root: Path):
    for name in PRODUCTION_ROOTS:
        base = root / name
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if path.is_file() and not _excluded(path, root):
                yield path

def _terms(text: str):
    lowered = text.casefold()
    return sorted({term for term in TERMS if term in lowered})

def _category(name: str, terms: list[str]) -> str:
    text = " ".join([name, *terms]).casefold()
    if "embedding" in text or "embed" in text:
        return "embedding"
    if "rerank" in text:
        return "reranking"
    if "similarity" in text or "cosine" in text or "vector" in text:
        return "semantic_similarity"
    if "bm25" in text or "fts" in text:
        return "full_text"
    if "hybrid" in text or "fusion" in text:
        return "hybrid"
    if "rank" in text or "score" in text:
        return "ranking"
    if "cache" in text or "memoize" in text or "lru_cache" in text or "redis" in text:
        return "cache"
    if "ground" in text:
        return "grounding"
    if "citation" in text or "evidence" in text or "provenance" in text:
        return "evidence"
    if "registry" in text:
        return "registry"
    if "chunk" in text:
        return "chunking"
    if "search" in text or "retrieve" in text:
        return "retrieval"
    return "other"

def inspect_components(root: Path) -> list[dict[str, Any]]:
    components = []
    callers: dict[str, set[str]] = defaultdict(set)

    for path in _files(root):
        rel = str(path.relative_to(root))
        module = rel[:-3].replace("/", ".")
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        stack: list[str] = []

        class Visitor(ast.NodeVisitor):
            def visit_ClassDef(self, node):
                qualified = ".".join([*stack, node.name])
                terms = _terms(qualified + " " + (ast.get_docstring(node) or ""))
                if terms:
                    components.append({
                        "name": qualified, "module": module, "path": rel,
                        "line": node.lineno, "kind": "class",
                        "category": _category(qualified, terms),
                        "parameters": [], "returns": None, "callees": [],
                        "sql_reads": [], "sql_writes": [], "terms": terms,
                    })
                stack.append(node.name)
                self.generic_visit(node)
                stack.pop()

            def visit_FunctionDef(self, node):
                qualified = ".".join([*stack, node.name])
                params = [
                    arg.arg for arg in
                    [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
                    if arg.arg != "self"
                ]
                terms = _terms(
                    " ".join([qualified, ast.get_docstring(node) or "", *params, *stack])
                )
                if terms:
                    callees, reads, writes = set(), set(), set()
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            try:
                                target = ast.unparse(child.func)
                            except Exception:
                                target = "<unknown>"
                            if _terms(target):
                                callees.add(target)
                                callers[target].add(f"{module}.{qualified}")
                        if isinstance(child, ast.Constant) and isinstance(child.value, str):
                            reads.update(READ_RE.findall(child.value))
                            writes.update(WRITE_RE.findall(child.value))
                    components.append({
                        "name": qualified, "module": module, "path": rel,
                        "line": node.lineno, "kind": "function",
                        "category": _category(qualified, terms),
                        "parameters": params,
                        "returns": ast.unparse(node.returns) if node.returns else None,
                        "callees": sorted(callees),
                        "sql_reads": sorted(reads),
                        "sql_writes": sorted(writes),
                        "terms": terms,
                    })
                stack.append(node.name)
                self.generic_visit(node)
                stack.pop()

            visit_AsyncFunctionDef = visit_FunctionDef

        Visitor().visit(tree)

    runtime_modules = {
        item.get("module") for item in inspect_runtime(root)
        if item.get("module")
    }
    for item in components:
        item["status"] = "LIVE" if item["module"] in runtime_modules else "DORMANT"
        item["callers"] = sorted(callers.get(item["name"], set()))
        item["component_id"] = f"{item['module']}:{item['name']}"

    return sorted(components, key=lambda x: (x["module"], x["line"], x["name"]))

def inspect_runtime(root: Path) -> list[dict[str, Any]]:
    lines = [
        "import inspect, json",
        "result=[]",
        "def record(owner, attribute, value, details=None):",
        "    result.append({'owner':owner,'attribute':attribute,"
        "'type_name':None if value is None else type(value).__name__,"
        "'module':None if value is None else type(value).__module__,"
        "'callable_name':getattr(value,'__qualname__',None) if callable(value) else None,"
        "'signature':str(inspect.signature(value)) if callable(value) else None,"
        "'details':details or {}})",
        "try:",
        "    from core.src.routes.api import conversation_service",
        "    record('application','conversation_service',conversation_service)",
        "    for name in ('compiler','repository','orchestrator','answer_handler'):",
        "        record('conversation_service',name,getattr(conversation_service,name,None))",
        "    orchestrator=getattr(conversation_service,'orchestrator',None)",
        "    if orchestrator is not None:",
        "        for name in ('director','grounding_service','awareness_service','observability_service','synthesis_handler'):",
        "            value=getattr(orchestrator,name,None)",
        "            details={}",
        "            if name=='grounding_service' and value is not None:",
        "                details['database_path']=str(getattr(value,'database_path',''))",
        "                handler=getattr(value,'search_handler',None)",
        "                if handler is not None:",
        "                    details['search_handler_module']=getattr(handler,'__module__',None)",
        "                    details['search_handler_qualname']=getattr(handler,'__qualname__',None)",
        "            record('orchestrator',name,value,details)",
        "    from core.knowledge_catalog.search import search_catalog",
        "    from core.knowledge_catalog.materialization.search import search_runtime_knowledge",
        "    record('retrieval','search_catalog',search_catalog)",
        "    record('retrieval','search_runtime_knowledge',search_runtime_knowledge)",
        "except Exception as exc:",
        "    result.append({'owner':'runtime','attribute':'error','type_name':type(exc).__name__,"
        "'module':type(exc).__module__,'callable_name':None,'signature':None,"
        "'details':{'message':str(exc)}})",
        "print(json.dumps(result))",
    ]
    completed = subprocess.run(
        [os.environ.get("PYTHON_BIN", "python"), "-c", "\n".join(lines)],
        cwd=root, capture_output=True, text=True, timeout=45,
    )
    candidates = [line for line in completed.stdout.splitlines() if line.strip().startswith("[")]
    if not candidates:
        return [{
            "owner": "runtime", "attribute": "error", "type_name": None,
            "module": None, "callable_name": None, "signature": None,
            "details": {"message": completed.stderr.strip() or completed.stdout.strip()},
        }]
    return json.loads(candidates[-1])

def inspect_tables(database: Path | None, components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if database is None or not database.is_file():
        return []

    readers: dict[str, set[str]] = defaultdict(set)
    writers: dict[str, set[str]] = defaultdict(set)
    for item in components:
        source = f"{item['module']}.{item['name']}"
        for table in item["sql_reads"]:
            readers[table].add(source)
        for table in item["sql_writes"]:
            writers[table].add(source)

    result = []
    with sqlite3.connect(database) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        ).fetchall()
        for row in rows:
            name = str(row[0])
            if not any(hint in name.casefold() for hint in TABLE_HINTS):
                continue
            columns = [
                str(x[1]) for x in conn.execute(f'PRAGMA table_info("{name}")')
            ]
            indexes = [
                str(x[1]) for x in conn.execute(f'PRAGMA index_list("{name}")')
            ]
            try:
                count = int(conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
            except sqlite3.Error:
                count = None
            has_r, has_w = bool(readers.get(name)), bool(writers.get(name))
            state = "ACTIVE" if has_r and has_w else "READ_ONLY" if has_r else "WRITE_ONLY" if has_w else "UNOWNED"
            result.append({
                "name": name, "row_count": count, "columns": columns,
                "indexes": indexes, "readers": sorted(readers.get(name, set())),
                "writers": sorted(writers.get(name, set())),
                "classification": state,
            })
    return result
