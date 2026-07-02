from __future__ import annotations

import ast
import csv
from dataclasses import dataclass, field
from pathlib import Path


ROOTS = [
    Path("core/knowledge_catalog"),
    Path("core/knowledge_graph"),
    Path("core/knowledge_mapper"),
    Path("core/semantic_digest"),
    Path("knowledge_engine"),
    Path("dev/librarian"),
]

OUT_DIR = Path("audit/knowledge_capabilities")
REPORT_MD = OUT_DIR / "CAPABILITY_MATRIX.md"
REPORT_CSV = OUT_DIR / "capability_matrix.csv"


CAPABILITY_KEYWORDS = {
    "acquisition": ["download", "acquire", "hunter", "miner", "provider", "source"],
    "inspection": ["inspect", "inspector", "mime", "magic", "detect"],
    "extraction": ["extract", "reader", "pdf", "zim", "html", "epub", "docx", "text"],
    "normalization": ["normalize", "archive", "manifest", "metadata"],
    "catalog": ["catalog", "register", "repository", "document", "asset"],
    "classification": ["classif", "subject", "keyword", "concept", "mapper", "semantic"],
    "collections": ["collection"],
    "graph": ["graph", "coverage", "gap", "ontology", "prerequisite"],
    "search": ["search", "retrieve", "query"],
    "storage": ["store", "storage", "database", "sqlite", "connect"],
    "chunking": ["chunk"],
    "embedding": ["embed", "vector"],
    "cko": ["cko", "canonical"],
}


@dataclass
class ModuleInfo:
    path: Path
    module: str
    package: str
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    cli: bool = False
    database: bool = False
    capabilities: set[str] = field(default_factory=set)


def module_name(path: Path) -> str:
    return ".".join(path.with_suffix("").parts)


def package_name(path: Path) -> str:
    parts = path.parts
    if len(parts) >= 2:
        if parts[0] == "core":
            return "/".join(parts[:2])
        if parts[0] == "knowledge_engine":
            return "knowledge_engine"
        if parts[0] == "dev" and len(parts) >= 2:
            return "/".join(parts[:2])
    return parts[0]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def classify_capabilities(path: Path, text: str, names: list[str]) -> set[str]:
    haystack = " ".join(
        [
            str(path).lower(),
            text.lower(),
            " ".join(names).lower(),
        ]
    )

    found = set()

    for capability, keywords in CAPABILITY_KEYWORDS.items():
        if any(k in haystack for k in keywords):
            found.add(capability)

    return found


def inspect_file(path: Path) -> ModuleInfo:
    text = read_text(path)
    info = ModuleInfo(
        path=path,
        module=module_name(path),
        package=package_name(path),
    )

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return info

    names = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                info.classes.append(node.name)
                names.append(node.name)

        elif isinstance(node, ast.FunctionDef):
            if not node.name.startswith("_"):
                info.functions.append(node.name)
                names.append(node.name)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                info.imports.append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                info.imports.append(node.module)

    info.cli = (
        "argparse" in text
        or "if __name__ == \"__main__\"" in text
        or "if __name__ == '__main__'" in text
    )

    info.database = "sqlite3" in text or "connect(" in text or "CREATE TABLE" in text

    info.capabilities = classify_capabilities(path, text, names)

    return info


def discover_modules() -> list[ModuleInfo]:
    modules = []

    for root in ROOTS:
        if not root.exists():
            continue

        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue

            modules.append(inspect_file(path))

    return modules


def write_csv(modules: list[ModuleInfo]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with REPORT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "package",
                "module",
                "path",
                "capabilities",
                "classes",
                "functions",
                "cli",
                "database",
                "imports",
            ],
        )
        writer.writeheader()

        for m in modules:
            writer.writerow(
                {
                    "package": m.package,
                    "module": m.module,
                    "path": str(m.path),
                    "capabilities": ", ".join(sorted(m.capabilities)),
                    "classes": ", ".join(m.classes),
                    "functions": ", ".join(m.functions),
                    "cli": "yes" if m.cli else "",
                    "database": "yes" if m.database else "",
                    "imports": ", ".join(sorted(set(m.imports))),
                }
            )


def summarize_by_package(modules: list[ModuleInfo]) -> dict[str, dict]:
    summary: dict[str, dict] = {}

    for m in modules:
        row = summary.setdefault(
            m.package,
            {
                "modules": 0,
                "classes": 0,
                "functions": 0,
                "cli": 0,
                "database": 0,
                "capabilities": set(),
            },
        )

        row["modules"] += 1
        row["classes"] += len(m.classes)
        row["functions"] += len(m.functions)
        row["cli"] += 1 if m.cli else 0
        row["database"] += 1 if m.database else 0
        row["capabilities"].update(m.capabilities)

    return summary


def capability_owners(modules: list[ModuleInfo]) -> dict[str, set[str]]:
    owners: dict[str, set[str]] = {}

    for m in modules:
        for capability in m.capabilities:
            owners.setdefault(capability, set()).add(m.package)

    return owners


def write_markdown(modules: list[ModuleInfo]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    package_summary = summarize_by_package(modules)
    owners = capability_owners(modules)

    lines = []
    lines.append("# JARVIS Knowledge Capability Matrix")
    lines.append("")
    lines.append("Generated from repository source code.")
    lines.append("")
    lines.append("## Package Summary")
    lines.append("")
    lines.append("| Package | Modules | Classes | Functions | CLI | DB | Capabilities |")
    lines.append("|---|---:|---:|---:|---:|---:|---|")

    for package, row in sorted(package_summary.items()):
        lines.append(
            "| "
            + " | ".join(
                [
                    package,
                    str(row["modules"]),
                    str(row["classes"]),
                    str(row["functions"]),
                    str(row["cli"]),
                    str(row["database"]),
                    ", ".join(sorted(row["capabilities"])),
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Capability Ownership")
    lines.append("")
    lines.append("| Capability | Owners | Duplication Risk |")
    lines.append("|---|---|---|")

    for capability, pkgs in sorted(owners.items()):
        risk = "HIGH" if len(pkgs) > 1 else "LOW"
        lines.append(
            f"| {capability} | {', '.join(sorted(pkgs))} | {risk} |"
        )

    lines.append("")
    lines.append("## Module Details")
    lines.append("")

    for m in sorted(modules, key=lambda x: x.module):
        lines.append(f"### `{m.module}`")
        lines.append("")
        lines.append(f"- Path: `{m.path}`")
        lines.append(f"- Package: `{m.package}`")
        lines.append(f"- Capabilities: {', '.join(sorted(m.capabilities)) or 'none detected'}")
        lines.append(f"- CLI: {'yes' if m.cli else 'no'}")
        lines.append(f"- Database: {'yes' if m.database else 'no'}")

        if m.classes:
            lines.append(f"- Classes: {', '.join(m.classes)}")
        if m.functions:
            lines.append(f"- Functions: {', '.join(m.functions)}")

        lines.append("")

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    modules = discover_modules()
    write_csv(modules)
    write_markdown(modules)

    print("[OK] Knowledge capability audit complete")
    print(f"Modules analyzed: {len(modules)}")
    print(f"Markdown report : {REPORT_MD}")
    print(f"CSV report      : {REPORT_CSV}")


if __name__ == "__main__":
    main()
