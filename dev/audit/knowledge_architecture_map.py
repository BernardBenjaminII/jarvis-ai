from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


ROOTS = [
    Path("knowledge_engine"),
    Path("core/knowledge_catalog"),
    Path("core/knowledge_graph"),
    Path("core/knowledge_mapper"),
    Path("core/semantic_digest"),
    Path("dev/librarian"),
]

OUT = Path("audit/knowledge_architecture/KNOWLEDGE_ARCHITECTURE_MAP.md")


CANONICAL_CAPABILITIES = {
    "discovery": ["discover", "scanner", "provider", "source"],
    "inspection": ["inspect", "inspector", "detect", "magic", "mime"],
    "reading": ["reader", "read_", "pdf", "zim", "epub", "html", "markdown", "docx", "text"],
    "extraction": ["extract", "extractor", "structure", "metadata"],
    "normalization": ["normalize", "archive", "manifest"],
    "chunking": ["chunk"],
    "embedding": ["embed", "vector"],
    "catalog": ["catalog", "document", "asset", "register", "repository"],
    "classification": ["classif", "subject", "keyword", "concept", "mapper", "semantic"],
    "storage": ["store", "storage", "database", "sqlite"],
    "search": ["search", "retrieve", "query"],
    "graph": ["graph", "coverage", "gap", "ontology", "prerequisite"],
    "acquisition": ["download", "acquire", "hunter", "miner"],
    "cko": ["cko", "canonical"],
}


@dataclass
class ModuleRecord:
    path: Path
    module: str
    package: str
    imports: set[str] = field(default_factory=set)
    imported_by: set[str] = field(default_factory=set)
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    capabilities: set[str] = field(default_factory=set)


def module_name(path: Path) -> str:
    return ".".join(path.with_suffix("").parts)


def package_name(path: Path) -> str:
    parts = path.parts

    if parts[0] == "knowledge_engine":
        return "knowledge_engine"

    if parts[0] == "core" and len(parts) >= 2:
        return "/".join(parts[:2])

    if parts[0] == "dev" and len(parts) >= 2:
        return "/".join(parts[:2])

    return parts[0]


def detect_capabilities(path: Path, text: str, names: list[str]) -> set[str]:
    haystack = " ".join([str(path), text, " ".join(names)]).lower()
    found = set()

    for cap, words in CANONICAL_CAPABILITIES.items():
        if any(word in haystack for word in words):
            found.add(cap)

    return found


def parse_module(path: Path) -> ModuleRecord:
    text = path.read_text(encoding="utf-8", errors="ignore")
    rec = ModuleRecord(
        path=path,
        module=module_name(path),
        package=package_name(path),
    )

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return rec

    names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                rec.classes.append(node.name)
                names.append(node.name)

        elif isinstance(node, ast.FunctionDef):
            if not node.name.startswith("_"):
                rec.functions.append(node.name)
                names.append(node.name)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                rec.imports.add(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                rec.imports.add(node.module)

    rec.capabilities = detect_capabilities(path, text, names)
    return rec


def discover() -> dict[str, ModuleRecord]:
    records: dict[str, ModuleRecord] = {}

    for root in ROOTS:
        if not root.exists():
            continue

        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue

            rec = parse_module(path)
            records[rec.module] = rec

    # Build reverse dependency map.
    for rec in records.values():
        for imported in rec.imports:
            for candidate in records:
                if candidate == imported or candidate.startswith(imported + "."):
                    records[candidate].imported_by.add(rec.module)

    return records


def summarize_packages(records: dict[str, ModuleRecord]) -> dict[str, dict]:
    summary = defaultdict(lambda: {
        "modules": 0,
        "classes": 0,
        "functions": 0,
        "capabilities": set(),
        "imports_out": 0,
        "imports_in": 0,
    })

    for rec in records.values():
        row = summary[rec.package]
        row["modules"] += 1
        row["classes"] += len(rec.classes)
        row["functions"] += len(rec.functions)
        row["capabilities"].update(rec.capabilities)
        row["imports_out"] += len(rec.imports)
        row["imports_in"] += len(rec.imported_by)

    return summary


def capability_owners(records: dict[str, ModuleRecord]) -> dict[str, set[str]]:
    owners = defaultdict(set)

    for rec in records.values():
        for cap in rec.capabilities:
            owners[cap].add(rec.package)

    return owners


def likely_canonical_owner(capability: str, owners: set[str]) -> str:
    preferred = {
        "discovery": "dev/librarian",
        "acquisition": "dev/librarian",
        "inspection": "knowledge_engine",
        "reading": "knowledge_engine",
        "extraction": "knowledge_engine",
        "normalization": "dev/librarian",
        "chunking": "knowledge_engine",
        "embedding": "knowledge_engine",
        "catalog": "core/knowledge_catalog",
        "classification": "core/knowledge_catalog",
        "storage": "core/knowledge_catalog",
        "search": "core/knowledge_catalog",
        "graph": "core/knowledge_graph",
        "cko": "dev/librarian",
    }

    choice = preferred.get(capability)

    if choice in owners:
        return choice

    if "knowledge_engine" in owners:
        return "knowledge_engine"

    return sorted(owners)[0] if owners else "UNKNOWN"


def write_report(records: dict[str, ModuleRecord]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    package_summary = summarize_packages(records)
    owners = capability_owners(records)

    lines: list[str] = []
    lines.append("# JARVIS Knowledge Architecture Map")
    lines.append("")
    lines.append("Generated from source code. This report is for architecture decisions, not runtime behavior.")
    lines.append("")
    lines.append("## Package Summary")
    lines.append("")
    lines.append("| Package | Modules | Classes | Functions | Imports In | Imports Out | Capabilities |")
    lines.append("|---|---:|---:|---:|---:|---:|---|")

    for pkg, row in sorted(package_summary.items()):
        lines.append(
            f"| {pkg} | {row['modules']} | {row['classes']} | {row['functions']} | "
            f"{row['imports_in']} | {row['imports_out']} | {', '.join(sorted(row['capabilities']))} |"
        )

    lines.append("")
    lines.append("## Capability Ownership Decision Draft")
    lines.append("")
    lines.append("| Capability | Detected Owners | Proposed Canonical Owner | Action |")
    lines.append("|---|---|---|---|")

    for cap, pkgs in sorted(owners.items()):
        canonical = likely_canonical_owner(cap, pkgs)
        action = "KEEP canonical; adapt/archive duplicates" if len(pkgs) > 1 else "KEEP"
        lines.append(
            f"| {cap} | {', '.join(sorted(pkgs))} | {canonical} | {action} |"
        )

    lines.append("")
    lines.append("## Most Connected Modules")
    lines.append("")
    lines.append("| Module | Package | Imported By | Imports | Capabilities |")
    lines.append("|---|---|---:|---:|---|")

    connected = sorted(
        records.values(),
        key=lambda r: len(r.imported_by) + len(r.imports),
        reverse=True,
    )[:40]

    for rec in connected:
        lines.append(
            f"| `{rec.module}` | {rec.package} | {len(rec.imported_by)} | "
            f"{len(rec.imports)} | {', '.join(sorted(rec.capabilities))} |"
        )

    lines.append("")
    lines.append("## Duplicate-Risk Modules")
    lines.append("")
    lines.append("Modules below participate in capabilities with multiple detected owners.")
    lines.append("")

    duplicate_caps = {cap for cap, pkgs in owners.items() if len(pkgs) > 1}

    for rec in sorted(records.values(), key=lambda r: (r.package, r.module)):
        overlap = rec.capabilities.intersection(duplicate_caps)
        if not overlap:
            continue

        lines.append(f"### `{rec.module}`")
        lines.append(f"- Package: `{rec.package}`")
        lines.append(f"- Path: `{rec.path}`")
        lines.append(f"- Duplicate-risk capabilities: {', '.join(sorted(overlap))}")
        if rec.classes:
            lines.append(f"- Classes: {', '.join(rec.classes)}")
        if rec.functions:
            lines.append(f"- Functions: {', '.join(rec.functions)}")
        lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    records = discover()
    write_report(records)

    print("[OK] Knowledge architecture map generated")
    print(f"Modules analyzed: {len(records)}")
    print(f"Report: {OUT}")


if __name__ == "__main__":
    main()
