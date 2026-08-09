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
from typing import Any, Iterable


DEFAULT_DB = Path(
    os.environ.get(
        "JARVIS_CATALOG_DB",
        "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite",
    )
)

CANONICAL_ROOTS = ("core", "knowledge_engine")
AUXILIARY_ROOTS = ("dev",)

EXCLUDED_NAMES = {
    ".git", ".migration_backups", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".venv", "venv", "node_modules", "dist",
    "build", "htmlcov", "archive", "artifacts", "tests",
}

EXCLUDED_PREFIXES = (
    "genesis_",
    "jarvis_convergence_",
    "architecture_contract_",
)

TERMS = (
    "search", "retrieve", "retrieval", "rank", "rerank", "score",
    "similarity", "cosine", "vector", "embedding", "embed", "fts",
    "bm25", "chunk", "catalog", "grounding", "evidence", "provenance",
)

TABLE_HINTS = (
    "document", "chunk", "embedding", "vector", "index", "catalog",
    "registry", "source", "page", "fts",
)

SQL_READ_RE = re.compile(
    r"\b(?:FROM|JOIN)\s+[\"'`]?([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)
SQL_WRITE_RE = re.compile(
    r"\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM|REPLACE\s+INTO)\s+"
    r"[\"'`]?([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)


@dataclass
class FunctionRecord:
    path: str
    line: int
    qualified_name: str
    parameters: list[str]
    returns: str | None
    terms: list[str]
    calls: list[str] = field(default_factory=list)
    sql_reads: list[str] = field(default_factory=list)
    sql_writes: list[str] = field(default_factory=list)


@dataclass
class ClassRecord:
    path: str
    line: int
    qualified_name: str
    bases: list[str]
    terms: list[str]


@dataclass
class ImportRecord:
    path: str
    line: int
    module: str
    names: list[str]


def is_excluded(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    for part in relative.parts:
        if part in EXCLUDED_NAMES:
            return True
        lowered = part.casefold()
        if any(lowered.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
            return True
    return False


def iter_python_files(root: Path, include_auxiliary: bool = True) -> Iterable[Path]:
    roots = list(CANONICAL_ROOTS)
    if include_auxiliary:
        roots.extend(AUXILIARY_ROOTS)

    for name in roots:
        base = root / name
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if path.is_file() and not is_excluded(path, root):
                yield path


def annotation(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def terms_for(text: str) -> list[str]:
    lowered = text.casefold()
    return sorted({term for term in TERMS if term in lowered})


def function_inventory(
    root: Path,
) -> tuple[list[FunctionRecord], list[ClassRecord], list[ImportRecord]]:
    functions: list[FunctionRecord] = []
    classes: list[ClassRecord] = []
    imports: list[ImportRecord] = []

    for path in iter_python_files(root):
        relative = str(path.relative_to(root))
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source)
        except Exception:
            continue

        stack: list[str] = []

        class Visitor(ast.NodeVisitor):
            def visit_Import(self, node: ast.Import) -> Any:
                names = [alias.name for alias in node.names]
                if terms_for(" ".join(names)):
                    imports.append(
                        ImportRecord(relative, node.lineno, "", names)
                    )

            def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
                module = node.module or ""
                names = [alias.name for alias in node.names]
                if terms_for(" ".join([module, *names])):
                    imports.append(
                        ImportRecord(relative, node.lineno, module, names)
                    )

            def visit_ClassDef(self, node: ast.ClassDef) -> Any:
                qualified = ".".join([*stack, node.name])
                matched = terms_for(
                    " ".join(
                        [
                            qualified,
                            ast.get_docstring(node) or "",
                            *(annotation(base) or "" for base in node.bases),
                        ]
                    )
                )
                if matched:
                    classes.append(
                        ClassRecord(
                            path=relative,
                            line=node.lineno,
                            qualified_name=qualified,
                            bases=[
                                annotation(base) or "<unknown>"
                                for base in node.bases
                            ],
                            terms=matched,
                        )
                    )
                stack.append(node.name)
                self.generic_visit(node)
                stack.pop()

            def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
                qualified = ".".join([*stack, node.name])
                params = [
                    arg.arg
                    for arg in (
                        [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
                    )
                    if arg.arg != "self"
                ]
                matched = terms_for(
                    " ".join(
                        [
                            qualified,
                            ast.get_docstring(node) or "",
                            " ".join(params),
                            annotation(node.returns) or "",
                        ]
                    )
                )

                if matched:
                    calls: set[str] = set()
                    reads: set[str] = set()
                    writes: set[str] = set()

                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            try:
                                target = ast.unparse(child.func)
                            except Exception:
                                target = "<unknown>"
                            if terms_for(target):
                                calls.add(target)

                        if isinstance(child, ast.Constant) and isinstance(child.value, str):
                            reads.update(SQL_READ_RE.findall(child.value))
                            writes.update(SQL_WRITE_RE.findall(child.value))

                    functions.append(
                        FunctionRecord(
                            path=relative,
                            line=node.lineno,
                            qualified_name=qualified,
                            parameters=params,
                            returns=annotation(node.returns),
                            terms=matched,
                            calls=sorted(calls),
                            sql_reads=sorted(reads),
                            sql_writes=sorted(writes),
                        )
                    )

                stack.append(node.name)
                self.generic_visit(node)
                stack.pop()

            visit_AsyncFunctionDef = visit_FunctionDef

        Visitor().visit(tree)

    return (
        sorted(functions, key=lambda item: (item.path, item.line)),
        sorted(classes, key=lambda item: (item.path, item.line)),
        sorted(imports, key=lambda item: (item.path, item.line)),
    )


def database_inventory(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "error": "database does not exist",
            "tables": [],
        }

    tables: list[dict[str, Any]] = []
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type IN ('table', 'view')
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        for row in rows:
            name = str(row[0])
            if not any(hint in name.casefold() for hint in TABLE_HINTS):
                continue

            columns = [
                str(item[1])
                for item in conn.execute(f'PRAGMA table_info("{name}")').fetchall()
            ]
            indexes = [
                str(item[1])
                for item in conn.execute(f'PRAGMA index_list("{name}")').fetchall()
            ]
            try:
                count = int(
                    conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                )
            except sqlite3.Error:
                count = None

            tables.append(
                {
                    "name": name,
                    "row_count": count,
                    "columns": columns,
                    "indexes": indexes,
                }
            )

    return {
        "path": str(path),
        "exists": True,
        "size_bytes": path.stat().st_size,
        "tables": tables,
    }


def runtime_probe(root: Path) -> dict[str, Any]:
    code = r"""
import inspect
import json

result = {"objects": [], "errors": []}

def record(owner, attribute, value, details=None):
    result["objects"].append({
        "owner": owner,
        "attribute": attribute,
        "type_name": None if value is None else type(value).__name__,
        "module": None if value is None else type(value).__module__,
        "details": details or {},
    })

try:
    from core.src.routes.api import conversation_service
    record("application", "conversation_service", conversation_service)

    for name in ("compiler", "repository", "orchestrator", "answer_handler"):
        record("conversation_service", name, getattr(conversation_service, name, None))

    orchestrator = getattr(conversation_service, "orchestrator", None)
    if orchestrator is not None:
        for name in (
            "director",
            "grounding_service",
            "awareness_service",
            "observability_service",
            "synthesis_handler",
        ):
            value = getattr(orchestrator, name, None)
            details = {}
            if name == "grounding_service" and value is not None:
                details["database_path"] = str(getattr(value, "database_path", ""))
                handler = getattr(value, "search_handler", None)
                if handler is not None:
                    details["search_handler"] = getattr(handler, "__qualname__", repr(handler))
                    details["search_handler_module"] = getattr(handler, "__module__", None)
            record("orchestrator", name, value, details)

    result["conversation_ask_signature"] = str(
        inspect.signature(conversation_service.ask)
    )
except Exception as exc:
    result["errors"].append(f"{type(exc).__name__}: {exc}")

for dotted in (
    "core.knowledge_catalog.search.search_catalog",
    "core.knowledge_catalog.materialization.search.search_runtime_knowledge",
):
    module_name, function_name = dotted.rsplit(".", 1)
    try:
        module = __import__(module_name, fromlist=[function_name])
        value = getattr(module, function_name)
        result.setdefault("search_functions", []).append({
            "module": value.__module__,
            "qualname": value.__qualname__,
            "signature": str(inspect.signature(value)),
        })
    except Exception as exc:
        result["errors"].append(
            f"{dotted} import failed: {type(exc).__name__}: {exc}"
        )

print(json.dumps(result))
"""
    completed = subprocess.run(
        [os.environ.get("PYTHON_BIN", "python"), "-c", code],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=45,
    )
    lines = [
        line for line in completed.stdout.splitlines()
        if line.strip().startswith("{")
    ]
    if not lines:
        return {
            "objects": [],
            "search_functions": [],
            "errors": [
                completed.stderr.strip()
                or completed.stdout.strip()
                or "runtime probe produced no JSON"
            ],
        }

    try:
        return json.loads(lines[-1])
    except Exception:
        return {
            "objects": [],
            "search_functions": [],
            "errors": ["runtime probe returned invalid JSON"],
        }


def table_ownership(
    functions: list[FunctionRecord],
    database: dict[str, Any],
) -> dict[str, dict[str, list[str]]]:
    ownership: dict[str, dict[str, list[str]]] = {
        item["name"]: {"readers": [], "writers": []}
        for item in database.get("tables", [])
    }

    for function in functions:
        source = f"{function.qualified_name} ({function.path}:{function.line})"

        for table in function.sql_reads:
            ownership.setdefault(table, {"readers": [], "writers": []})
            ownership[table]["readers"].append(source)

        for table in function.sql_writes:
            ownership.setdefault(table, {"readers": [], "writers": []})
            ownership[table]["writers"].append(source)

    for value in ownership.values():
        value["readers"] = sorted(set(value["readers"]))
        value["writers"] = sorted(set(value["writers"]))

    return ownership


def classify_functions(
    functions: list[FunctionRecord],
    runtime: dict[str, Any],
) -> list[dict[str, Any]]:
    active_modules: set[str] = set()

    for item in runtime.get("objects", []):
        if item.get("module"):
            active_modules.add(str(item["module"]))
        details = item.get("details") or {}
        if details.get("search_handler_module"):
            active_modules.add(str(details["search_handler_module"]))

    for item in runtime.get("search_functions", []):
        if item.get("module"):
            active_modules.add(str(item["module"]))

    result: list[dict[str, Any]] = []
    for function in functions:
        module = function.path[:-3].replace("/", ".")

        if function.path.startswith("dev/"):
            status = "AUXILIARY"
        elif module in active_modules:
            status = "CANONICAL"
        else:
            status = "DORMANT"

        result.append(
            {
                **asdict(function),
                "module": module,
                "runtime_status": status,
            }
        )

    return result


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Genesis IX-A4.1B Pack 1 — Retrieval Runtime Inventory",
        "",
        f"**Generated:** {report['generated_at']}",
        f"**Repository:** `{report['repository_root']}`",
        f"**Database:** `{report['database']['path']}`",
        f"**Fingerprint:** `{report['fingerprint']}`",
        "",
        "## Summary",
        "",
        f"- Functions: **{len(report['functions'])}**",
        f"- Classes: **{len(report['classes'])}**",
        f"- Imports: **{len(report['imports'])}**",
        f"- Runtime objects: **{len(report['runtime'].get('objects', []))}**",
        f"- Database tables: **{len(report['database'].get('tables', []))}**",
        "",
        "## Live Runtime",
        "",
        "```json",
        json.dumps(report["runtime"], indent=2, sort_keys=True),
        "```",
        "",
        "## Canonical Retrieval Functions",
        "",
    ]

    canonical = [
        item
        for item in report["classified_functions"]
        if item["runtime_status"] == "CANONICAL"
    ]
    if canonical:
        for item in canonical:
            lines.append(
                f"- `{item['qualified_name']}` "
                f"(`{item['path']}:{item['line']}`)"
            )
    else:
        lines.append("- No canonical function was proven by live module identity.")

    lines.extend(
        [
            "",
            "## Database Ownership",
            "",
            "| Table | Readers | Writers |",
            "|---|---:|---:|",
        ]
    )
    for table, owners in sorted(report["table_ownership"].items()):
        lines.append(
            f"| `{table}` | {len(owners['readers'])} | {len(owners['writers'])} |"
        )

    lines.extend(
        [
            "",
            "## Pack Boundary",
            "",
            "Pack 1 produces the machine-readable retrieval census. Pack 2 will "
            "derive the runtime graph, duplicate report, component matrix, "
            "and canonicalization decisions from this inventory.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Genesis IX-A4.1B Pack 1 Retrieval Audit Engine"
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/audits/genesis_ix_a4_1b_pack1"),
    )
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output_dir
    if not output.is_absolute():
        output = root / output
    output.mkdir(parents=True, exist_ok=True)

    functions, classes, imports = function_inventory(root)
    database = database_inventory(args.database)
    runtime = runtime_probe(root)
    ownership = table_ownership(functions, database)
    classified = classify_functions(functions, runtime)

    report: dict[str, Any] = {
        "schema_version": "genesis_ix_a4_1b_pack1_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository_root": str(root),
        "database": database,
        "runtime": runtime,
        "functions": [asdict(item) for item in functions],
        "classes": [asdict(item) for item in classes],
        "imports": [asdict(item) for item in imports],
        "classified_functions": classified,
        "table_ownership": ownership,
    }

    payload = json.dumps(report, sort_keys=True)
    report["fingerprint"] = hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()

    (output / "retrieval_runtime_inventory.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "retrieval_runtime_inventory.md").write_text(
        render_markdown(report) + "\n",
        encoding="utf-8",
    )

    print("=" * 76)
    print("GENESIS IX-A4.1B PACK 1 — RETRIEVAL AUDIT ENGINE")
    print("=" * 76)
    print("Functions   :", len(functions))
    print("Classes     :", len(classes))
    print("Imports     :", len(imports))
    print("Tables      :", len(database.get("tables", [])))
    print("Output      :", output)
    print("Fingerprint :", report["fingerprint"])
    print("=" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
