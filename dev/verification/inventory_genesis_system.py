#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "docs" / "audits" / "genesis_system_inventory.md"
JSON_PATH = PROJECT_ROOT / "docs" / "audits" / "genesis_system_inventory.json"

EXCLUDED_DIRS = {
    ".git", ".migration_backups", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "__pycache__", ".venv", "venv", "node_modules",
    "dist", "build",
}
ARCHITECTURE_ROOTS = tuple(PROJECT_ROOT / name for name in ("core", "api", "app", "services", "ui"))
TEST_ROOTS = (PROJECT_ROOT / "tests",)
SCRIPT_ROOTS = (PROJECT_ROOT / "dev",)
DOC_ROOTS = (PROJECT_ROOT / "docs",)


@dataclass(frozen=True)
class PythonModule:
    path: str
    module: str
    line_count: int
    classes: tuple[str, ...]
    functions: tuple[str, ...]
    imports: tuple[str, ...]
    public_exports: tuple[str, ...]
    parse_error: str | None = None


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=PROJECT_ROOT, check=False,
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def iter_files(roots: Sequence[Path], suffixes: set[str] | None = None) -> Iterable[Path]:
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if any(part in EXCLUDED_DIRS for part in path.parts):
                continue
            if suffixes is not None and path.suffix not in suffixes:
                continue
            yield path


def relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def module_name(path: Path) -> str:
    parts = list(path.relative_to(PROJECT_ROOT).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def literal_string_sequence(node: ast.AST) -> tuple[str, ...]:
    if not isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return ()
    values: list[str] = []
    for item in node.elts:
        if isinstance(item, ast.Constant) and isinstance(item.value, str):
            values.append(item.value)
    return tuple(values)


def inspect_python(path: Path) -> PythonModule:
    source = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return PythonModule(
            relative(path), module_name(path), len(source.splitlines()), (), (), (), (),
            f"{exc.msg} at line {exc.lineno}",
        )

    classes: list[str] = []
    functions: list[str] = []
    imports: list[str] = []
    exports: tuple[str, ...] = ()

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append("." * node.level + (node.module or ""))
        elif isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
                exports = literal_string_sequence(node.value)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "__all__":
                exports = literal_string_sequence(node.value)

    return PythonModule(
        relative(path), module_name(path), len(source.splitlines()),
        tuple(classes), tuple(functions), tuple(sorted(set(imports))), exports,
    )


def package_from_module(module: str) -> str:
    parts = module.split(".")
    if len(parts) >= 2 and parts[0] == "core":
        return ".".join(parts[:2])
    return parts[0] if parts else module


def resolve_internal_import(source_module: str, imported: str) -> str | None:
    if imported.startswith("."):
        level = len(imported) - len(imported.lstrip("."))
        suffix = imported.lstrip(".")
        source_parts = source_module.split(".")[:-1]
        base = source_parts[: max(0, len(source_parts) - level + 1)]
        resolved = ".".join([*base, *([suffix] if suffix else [])])
    else:
        resolved = imported
    if resolved.startswith(("core.", "api.", "app.", "services.", "ui.")):
        return resolved
    return None


def file_digest(paths: Sequence[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(relative(path).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    if not rows:
        return "_None found._"
    output = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    output.extend(
        "| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |"
        for row in rows
    )
    return "\n".join(output)


def main() -> int:
    python_paths = list(iter_files(ARCHITECTURE_ROOTS, {".py"}))
    modules = [inspect_python(path) for path in python_paths]
    test_paths = list(iter_files(TEST_ROOTS, {".py"}))
    dev_paths = list(iter_files(SCRIPT_ROOTS, {".py", ".sh"}))
    doc_paths = list(iter_files(DOC_ROOTS, {".md", ".txt", ".rst", ".yaml", ".yml"}))

    package_modules: dict[str, list[PythonModule]] = defaultdict(list)
    for module in modules:
        package_modules[package_from_module(module.module)].append(module)

    dependency_edges: Counter[tuple[str, str]] = Counter()
    for module in modules:
        source_package = package_from_module(module.module)
        for imported in module.imports:
            resolved = resolve_internal_import(module.module, imported)
            if resolved is None:
                continue
            target_package = package_from_module(resolved)
            if source_package != target_package:
                dependency_edges[(source_package, target_package)] += 1

    duplicates: dict[str, list[str]] = defaultdict(list)
    for module in modules:
        for symbol in (*module.classes, *module.functions):
            if not symbol.startswith("_"):
                duplicates[symbol].append(module.path)
    duplicates = {k: v for k, v in sorted(duplicates.items()) if len(v) > 1}

    parse_errors = [module for module in modules if module.parse_error]
    evidence_modules = [m for m in modules if m.module == "core.evidence" or m.module.startswith("core.evidence.")]
    observation_modules = [m for m in modules if "observation" in m.module]
    reasoning_modules = [m for m in modules if "reasoning" in m.module]
    executive_modules = [m for m in modules if "executive" in m.module]

    git_status = run_git("status", "--short")
    git_branch = run_git("branch", "--show-current")
    git_head = run_git("rev-parse", "HEAD")
    recent_commits = run_git("log", "--oneline", "--decorate", "-12").splitlines()

    inventory = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository": {
            "branch": git_branch,
            "head": git_head,
            "working_tree_clean": not bool(git_status),
            "status_short": git_status.splitlines(),
        },
        "counts": {
            "production_python_modules": len(modules),
            "production_python_lines": sum(m.line_count for m in modules),
            "test_files": len(test_paths),
            "development_scripts": len(dev_paths),
            "documentation_files": len(doc_paths),
        },
        "packages": {
            package: {
                "modules": len(items),
                "lines": sum(m.line_count for m in items),
                "classes": sorted(s for m in items for s in m.classes if not s.startswith("_")),
                "public_exports": sorted(set(s for m in items for s in m.public_exports)),
            }
            for package, items in sorted(package_modules.items())
        },
        "subsystems": {
            "evidence": [m.path for m in evidence_modules],
            "observation": [m.path for m in observation_modules],
            "reasoning": [m.path for m in reasoning_modules],
            "executive": [m.path for m in executive_modules],
        },
        "dependency_edges": [
            {"source": s, "target": t, "import_count": c}
            for (s, t), c in sorted(dependency_edges.items())
        ],
        "duplicate_public_symbols": duplicates,
        "parse_errors": [{"path": m.path, "error": m.parse_error} for m in parse_errors],
        "architecture_fingerprint": file_digest([*python_paths, *test_paths, *dev_paths]),
        "recent_commits": recent_commits,
    }

    JSON_PATH.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    package_rows = [
        (name, data["modules"], data["lines"], len(data["classes"]), len(data["public_exports"]))
        for name, data in inventory["packages"].items()
    ]
    dependency_rows = [(e["source"], e["target"], e["import_count"]) for e in inventory["dependency_edges"]]
    duplicate_rows = [(name, "<br>".join(paths)) for name, paths in duplicates.items()]
    evidence_rows = [
        (m.path, ", ".join(m.classes) or "—", ", ".join(m.functions) or "—", ", ".join(m.public_exports) or "—")
        for m in evidence_modules
    ]

    observed = {Path(m.path).name for m in evidence_modules}
    proposed = ("policy.py", "rules.py", "evaluator.py", "admissibility.py")
    missing = [name for name in proposed if name not in observed]

    report = f"""# JARVIS Genesis System Inventory

**Generated:** {inventory['generated_at']}  
**Branch:** `{git_branch or 'unknown'}`  
**HEAD:** `{git_head or 'unknown'}`  
**Architecture fingerprint:** `{inventory['architecture_fingerprint']}`  
**Working tree:** {'clean' if not git_status else 'contains changes'}

## 1. Scope

This inventory is derived from the repository itself. It excludes Git internals,
migration backups, virtual environments, caches, build outputs, and external
runtime or knowledge volumes.

## 2. Repository Summary

| Measure | Count |
| --- | ---: |
| Production Python modules | {len(modules)} |
| Production Python lines | {sum(m.line_count for m in modules)} |
| Test files | {len(test_paths)} |
| Development scripts | {len(dev_paths)} |
| Documentation files | {len(doc_paths)} |

## 3. Production Package Inventory

{markdown_table(('Package', 'Modules', 'Lines', 'Public classes', '__all__ exports'), package_rows)}

## 4. Cognitive Subsystem Presence

| Subsystem | Observed modules |
| --- | ---: |
| Evidence | {len(evidence_modules)} |
| Observation | {len(observation_modules)} |
| Reasoning | {len(reasoning_modules)} |
| Executive | {len(executive_modules)} |

## 5. Evidence Engine Inventory

{markdown_table(('File', 'Classes', 'Functions', 'Declared exports'), evidence_rows)}

### Files absent from the proposed next pack

{chr(10).join(f'- `core/evidence/{name}`' for name in missing) or '- None'}

## 6. Internal Dependency Edges

{markdown_table(('Source package', 'Target package', 'Import statements'), dependency_rows)}

## 7. Duplicate Public Symbols

{markdown_table(('Symbol', 'Locations'), duplicate_rows)}

Duplicate names are review targets, not automatic defects. They may represent
bounded-context reuse, aliases, or competing canonical ownership.

## 8. Syntax Health

{'No syntax errors were detected in inventoried production modules.' if not parse_errors else chr(10).join(f'- `{m.path}` — {m.parse_error}' for m in parse_errors)}

## 9. Recent Repository History

{chr(10).join(f'- `{line}`' for line in recent_commits) or '- Git history unavailable.'}

## 10. Derived Next-Pack Boundary

The observed Evidence Engine currently provides domain vocabulary, errors, and
immutable contracts. The next pack should add deterministic admissibility policy
evaluation while deliberately excluding construction, persistence, relationship
analysis, aggregation, runtime orchestration, and reasoning integration.

### Recommended release

**Genesis IV-R3B Pack 1 — Admissibility Policy Foundation**

Proposed production files:

- `core/evidence/policy.py`
- `core/evidence/rules.py`
- `core/evidence/evaluator.py`
- `core/evidence/admissibility.py`

Proposed release assets:

- `docs/architecture/evidence_engine.md`
- `docs/decisions/ADR-00XX-certification-vs-compatibility.md`
- `tests/test_genesis_4r3b_pack1_admissibility_policy.py`
- `dev/verification/verify_genesis_4r3b_pack1.py`
- `dev/verify_genesis_4r3b_pack1.sh`

### Explicit exclusions

- Evidence record construction
- Registries or persistence
- Relationship graphs
- Aggregate sufficiency scoring
- Runtime service orchestration
- Direct reasoning-engine integration

## 11. Review Gate

Before implementation, inspect this report and its JSON companion for:

1. Existing observation contracts the evaluator must consume.
2. Existing modules that overlap the proposed policy boundary.
3. Dependency edges that could create upward or circular coupling.
4. Public enum values that constrain policy outcomes.
5. Stable exports that compatibility verification must preserve.
"""

    REPORT_PATH.write_text(report, encoding="utf-8")

    print()
    print("=" * 72)
    print("JARVIS GENESIS SYSTEM INVENTORY")
    print("=" * 72)
    print(f"[PASS] Report: {REPORT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"[PASS] Data  : {JSON_PATH.relative_to(PROJECT_ROOT)}")
    print(f"[PASS] Production modules: {len(modules)}")
    print(f"[PASS] Evidence modules  : {len(evidence_modules)}")
    print(f"[PASS] Dependency edges  : {len(dependency_edges)}")
    print(f"[PASS] Syntax errors     : {len(parse_errors)}")
    print(f"[PASS] Fingerprint       : {inventory['architecture_fingerprint']}")
    print("-" * 72)
    print("Status: INVENTORY COMPLETE")
    print("=" * 72)
    return 1 if parse_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
