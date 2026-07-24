#!/usr/bin/env python3
"""Audit duplicate cognitive symbols and legacy evidence dependencies."""

from __future__ import annotations

import ast
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core"
REPORT = ROOT / "docs" / "audits" / "cognitive_ownership_migration_map.md"
DATA = ROOT / "docs" / "audits" / "cognitive_ownership_migration_map.json"

EXCLUDED = {"__pycache__", ".migration_backups", ".git"}


def files() -> Iterable[Path]:
    for path in sorted(CORE.rglob("*.py")):
        if any(part in EXCLUDED for part in path.parts):
            continue
        yield path


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def module_name(path: Path) -> str:
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def imported_modules(tree: ast.AST) -> list[str]:
    values: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            values.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            values.append(("." * node.level) + (node.module or ""))
    return values


def symbols(tree: ast.Module) -> list[str]:
    result: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                result.append(node.name)
    return result


def main() -> int:
    parsed: dict[Path, ast.Module] = {}
    parse_errors: list[dict[str, str]] = []

    for path in files():
        try:
            parsed[path] = ast.parse(
                path.read_text(encoding="utf-8", errors="replace"),
                filename=str(path),
            )
        except SyntaxError as exc:
            parse_errors.append({"path": rel(path), "error": str(exc)})

    symbol_locations: dict[str, list[str]] = defaultdict(list)
    for path, tree in parsed.items():
        for symbol in symbols(tree):
            symbol_locations[symbol].append(rel(path))

    evidence_duplicate_names = {
        name: locations
        for name, locations in sorted(symbol_locations.items())
        if len(locations) > 1
        and any(location.startswith("core/evidence/") for location in locations)
    }

    legacy_imports: list[dict[str, object]] = []
    canonical_imports: list[dict[str, object]] = []

    for path, tree in parsed.items():
        imports = sorted(set(imported_modules(tree)))
        legacy = [
            value for value in imports
            if "reasoning.evidence" in value
        ]
        canonical = [
            value for value in imports
            if value == "core.evidence" or value.startswith("core.evidence.")
        ]
        if legacy:
            legacy_imports.append({
                "consumer": rel(path),
                "module": module_name(path),
                "imports": legacy,
            })
        if canonical:
            canonical_imports.append({
                "consumer": rel(path),
                "module": module_name(path),
                "imports": canonical,
            })

    legacy_package_files = [
        rel(path)
        for path in parsed
        if rel(path).startswith("core/reasoning/evidence/")
    ]

    data = {
        "canonical_owner": "core.evidence",
        "legacy_package": "core.reasoning.evidence",
        "legacy_package_files": legacy_package_files,
        "legacy_consumers": legacy_imports,
        "canonical_consumers": canonical_imports,
        "duplicate_symbols_touching_core_evidence": evidence_duplicate_names,
        "parse_errors": parse_errors,
        "migration_eligible_for_removal": (
            not legacy_package_files
            or (not legacy_imports and not evidence_duplicate_names)
        ),
    }

    DATA.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    duplicate_lines = []
    for name, locations in evidence_duplicate_names.items():
        duplicate_lines.append(
            f"| `{name}` | " + "<br>".join(f"`{location}`" for location in locations) + " |"
        )

    legacy_lines = []
    for item in legacy_imports:
        legacy_lines.append(
            f"| `{item['consumer']}` | " +
            "<br>".join(f"`{value}`" for value in item["imports"]) + " |"
        )

    canonical_lines = []
    for item in canonical_imports:
        canonical_lines.append(
            f"| `{item['consumer']}` | " +
            "<br>".join(f"`{value}`" for value in item["imports"]) + " |"
        )

    report = f"""# Cognitive Ownership Migration Map

**Canonical evidence owner:** `core.evidence`  
**Legacy evidence package:** `core.reasoning.evidence`  
**Removal eligible:** {"YES" if data["migration_eligible_for_removal"] else "NO"}

## 1. Legacy Package Files

{chr(10).join(f"- `{path}`" for path in legacy_package_files) or "- None"}

## 2. Active Legacy Imports

| Consumer | Legacy imports |
| --- | --- |
{chr(10).join(legacy_lines) or "| None | None |"}

## 3. Active Canonical Imports

| Consumer | Canonical imports |
| --- | --- |
{chr(10).join(canonical_lines) or "| None | None |"}

## 4. Duplicate Symbols Touching `core.evidence`

| Symbol | Locations |
| --- | --- |
{chr(10).join(duplicate_lines) or "| None | None |"}

## 5. Migration Decision

The legacy package is not removable while any of the following remain:

- production imports of `core.reasoning.evidence`;
- semantically unresolved duplicate contracts;
- persisted payloads tied to the legacy schema;
- compatibility obligations without adapters.

This audit authorizes analysis only. It does not authorize deletion.
"""

    REPORT.write_text(report, encoding="utf-8")

    print("=" * 72)
    print("GENESIS IV-R3A PACK 3 — COGNITIVE OWNERSHIP AUDIT")
    print("=" * 72)
    print(f"[PASS] Legacy package files : {len(legacy_package_files)}")
    print(f"[PASS] Legacy consumers     : {len(legacy_imports)}")
    print(f"[PASS] Canonical consumers  : {len(canonical_imports)}")
    print(f"[PASS] Duplicate symbols    : {len(evidence_duplicate_names)}")
    print(f"[PASS] Parse errors         : {len(parse_errors)}")
    print(f"[PASS] Report               : {REPORT.relative_to(ROOT)}")
    print(f"[PASS] Data                 : {DATA.relative_to(ROOT)}")
    print("-" * 72)
    print("Status: MIGRATION MAP GENERATED")
    print("=" * 72)

    return 1 if parse_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
