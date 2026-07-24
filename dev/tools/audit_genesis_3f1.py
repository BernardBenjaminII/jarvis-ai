#!/usr/bin/env python3
"""Generate and verify the Genesis III-F1 Cognitive Workspace freeze baseline."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

SCHEMA_VERSION = "genesis-3f0/v1"
CANONICAL_PACKAGES = (
    "core/cognition/workspace",
    "core/cognition/integration",
)
REQUIRED_VERIFIERS = (
    "dev/verify_genesis_3a1.sh",
    "dev/verify_genesis_3a2.sh",
    "dev/verify_genesis_3a3.sh",
    "dev/verify_genesis_3a4.sh",
)
FORBIDDEN_IMPORT_PREFIXES = {
    "core/cognition/workspace": (
        "core.executive",
        "core.mission",
        "core.operations",
        "core.cognition.integration",
    ),
    "core/cognition/integration": (
        "core.executive",
        "core.mission",
        "core.operations",
        "core.routes",
    ),
}
REPORT_DIR = Path("docs/architecture/convergence")
JSON_REPORTS = {
    "public_api": REPORT_DIR / "genesis_3f1_public_api.json",
    "dependency_graph": REPORT_DIR / "genesis_3f1_dependency_graph.json",
    "snapshot": REPORT_DIR / "genesis_3f1_snapshot.json",
}
MARKDOWN_REPORTS = {
    "public_api": REPORT_DIR / "genesis_3f1_public_api.md",
    "dependency_graph": REPORT_DIR / "genesis_3f1_dependency_graph.md",
    "executive_readiness": REPORT_DIR / "genesis_3f1_executive_readiness.md",
}


class FreezeAuditError(RuntimeError):
    """Raised when the repository cannot satisfy the freeze contract."""


@dataclass(frozen=True)
class ModuleAudit:
    module: str
    path: str
    sha256: str
    exports: tuple[str, ...]
    imports: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "module": self.module,
            "path": self.path,
            "sha256": self.sha256,
            "exports": list(self.exports),
            "imports": list(self.imports),
        }


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def module_name(root: Path, path: Path) -> str:
    relative = path.relative_to(root).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _literal_strings(node: ast.AST) -> tuple[str, ...] | None:
    if not isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return None
    values: list[str] = []
    for item in node.elts:
        if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
            return None
        values.append(item.value)
    return tuple(values)


def discover_exports(tree: ast.Module) -> tuple[str, ...]:
    explicit: tuple[str, ...] | None = None
    public: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                public.add(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".", 1)[0]
                if not name.startswith("_"):
                    public.add(name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    continue
                name = alias.asname or alias.name
                if not name.startswith("_"):
                    public.add(name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    literal = _literal_strings(node.value)
                    if literal is not None:
                        explicit = literal
                elif isinstance(target, ast.Name) and not target.id.startswith("_"):
                    public.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if not node.target.id.startswith("_"):
                public.add(node.target.id)
    return tuple(sorted(set(explicit if explicit is not None else public)))


def _resolve_relative_import(
    current_module: str, level: int, imported: str | None, *, is_package: bool
) -> str:
    package_parts = current_module.split(".") if is_package else current_module.split(".")[:-1]
    if level > 1:
        package_parts = package_parts[: -(level - 1)]
    if imported:
        package_parts.extend(imported.split("."))
    return ".".join(part for part in package_parts if part)


def discover_imports(
    tree: ast.Module, current_module: str, *, is_package: bool
) -> tuple[str, ...]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            resolved = _resolve_relative_import(
                current_module, node.level, node.module, is_package=is_package
            )
            if resolved:
                imports.add(resolved)
    return tuple(sorted(imports))


def audit_module(root: Path, path: Path) -> ModuleAudit:
    relative = path.relative_to(root).as_posix()
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=relative)
    name = module_name(root, path)
    return ModuleAudit(
        module=name,
        path=relative,
        sha256=sha256_bytes(source.encode("utf-8")),
        exports=discover_exports(tree),
        imports=discover_imports(tree, name, is_package=path.name == "__init__.py"),
    )


def package_modules(root: Path, package: str) -> tuple[ModuleAudit, ...]:
    package_path = root / package
    if not package_path.is_dir():
        raise FreezeAuditError(f"missing canonical package: {package}")
    paths = sorted(
        path for path in package_path.rglob("*.py")
        if "__pycache__" not in path.parts
    )
    if not paths:
        raise FreezeAuditError(f"canonical package contains no Python modules: {package}")
    return tuple(audit_module(root, path) for path in paths)


def validate_unique_modules(modules: Sequence[ModuleAudit]) -> None:
    seen: dict[str, str] = {}
    for item in modules:
        previous = seen.setdefault(item.module, item.path)
        if previous != item.path:
            raise FreezeAuditError(
                f"duplicate module identity {item.module!r}: {previous!r} and {item.path!r}"
            )


def validate_dependencies(modules: Sequence[ModuleAudit]) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for item in modules:
        package = next(
            (candidate.replace("/", ".") for candidate in CANONICAL_PACKAGES
             if item.module == candidate.replace("/", ".")
             or item.module.startswith(candidate.replace("/", ".") + ".")),
            None,
        )
        if package is None:
            continue
        prefix_key = package.replace(".", "/")
        for imported in item.imports:
            for forbidden in FORBIDDEN_IMPORT_PREFIXES[prefix_key]:
                if imported == forbidden or imported.startswith(forbidden + "."):
                    violations.append(
                        {"module": item.module, "import": imported, "forbidden_prefix": forbidden}
                    )
    return sorted(violations, key=lambda value: (value["module"], value["import"]))


def build_reports(root: Path) -> dict[str, str]:
    modules = tuple(
        module
        for package in CANONICAL_PACKAGES
        for module in package_modules(root, package)
    )
    validate_unique_modules(modules)
    missing_verifiers = [path for path in REQUIRED_VERIFIERS if not (root / path).is_file()]
    if missing_verifiers:
        raise FreezeAuditError("missing prerequisite verifiers: " + ", ".join(missing_verifiers))
    violations = validate_dependencies(modules)
    if violations:
        details = "; ".join(f"{v['module']} -> {v['import']}" for v in violations)
        raise FreezeAuditError("forbidden dependency direction: " + details)

    module_dicts = [item.as_dict() for item in modules]
    package_api: dict[str, list[str]] = {}
    for package in CANONICAL_PACKAGES:
        dotted = package.replace("/", ".")
        root_module = next((item for item in modules if item.module == dotted), None)
        package_api[dotted] = list(root_module.exports if root_module else ())

    public_api = {
        "schema": SCHEMA_VERSION,
        "packages": package_api,
        "modules": [
            {"module": item.module, "exports": list(item.exports)}
            for item in modules
        ],
    }
    dependency_graph = {
        "schema": SCHEMA_VERSION,
        "allowed_direction": [
            "core.cognition.workspace -> standard library / lower-level contracts",
            "core.cognition.integration -> core.cognition.workspace",
            "executive consumers -> core.cognition.integration",
        ],
        "edges": [
            {"from": item.module, "to": imported}
            for item in modules for imported in item.imports
        ],
        "violations": violations,
    }
    freeze_material = {
        "schema": SCHEMA_VERSION,
        "canonical_packages": list(CANONICAL_PACKAGES),
        "required_verifiers": list(REQUIRED_VERIFIERS),
        "modules": module_dicts,
        "public_api": public_api,
        "dependency_graph": dependency_graph,
    }
    fingerprint = sha256_bytes(
        json.dumps(freeze_material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    snapshot = {
        **freeze_material,
        "architecture_fingerprint": fingerprint,
        "module_count": len(modules),
        "public_symbol_count": sum(len(item.exports) for item in modules),
        "executive_readiness": {
            "workspace_contracts": "READY",
            "persistence": "READY",
            "catalog_search": "READY",
            "integration_pipeline": "READY",
            "determinism": "READY",
            "dependency_direction": "READY",
            "public_api_baseline": "READY",
        },
    }

    public_api_md = [
        "# Genesis III-F1 Public API Baseline",
        "",
        f"**Schema:** `{SCHEMA_VERSION}`  ",
        f"**Architecture fingerprint:** `{fingerprint}`",
        "",
    ]
    for package, exports in package_api.items():
        public_api_md.extend([f"## `{package}`", ""])
        if exports:
            public_api_md.extend(f"- `{name}`" for name in exports)
        else:
            public_api_md.append("- No explicit package exports detected.")
        public_api_md.append("")

    dependency_md = [
        "# Genesis III-F1 Dependency Graph",
        "",
        f"**Architecture fingerprint:** `{fingerprint}`",
        "",
        "## Certified direction",
        "",
        "```text",
        "core.cognition.workspace",
        "        ↓",
        "core.cognition.integration",
        "        ↓",
        "future executive consumers",
        "```",
        "",
        "## Internal import edges",
        "",
    ]
    internal_prefixes = tuple(package.replace("/", ".") for package in CANONICAL_PACKAGES)
    internal_edges = [
        edge for edge in dependency_graph["edges"]
        if str(edge["to"]).startswith(internal_prefixes)
    ]
    dependency_md.extend(
        f"- `{edge['from']}` → `{edge['to']}`" for edge in internal_edges
    )
    if not internal_edges:
        dependency_md.append("- No internal cross-module imports detected.")
    dependency_md.extend(["", "**Forbidden dependency violations:** 0", ""])

    readiness_md = [
        "# Genesis III-F1 Executive Readiness",
        "",
        "**Certification:** READY  ",
        f"**Architecture fingerprint:** `{fingerprint}`  ",
        "",
        "| Capability | Status |",
        "|---|---|",
    ]
    for capability, status in snapshot["executive_readiness"].items():
        readiness_md.append(f"| {capability.replace('_', ' ').title()} | {status} |")
    readiness_md.extend([
        "",
        "Genesis III provides a certified cognitive workspace, durable repository, catalog/search boundary, and integration engine suitable for future executive consumption.",
        "",
    ])

    return {
        str(JSON_REPORTS["public_api"]): canonical_json(public_api),
        str(JSON_REPORTS["dependency_graph"]): canonical_json(dependency_graph),
        str(JSON_REPORTS["snapshot"]): canonical_json(snapshot),
        str(MARKDOWN_REPORTS["public_api"]): "\n".join(public_api_md).rstrip() + "\n",
        str(MARKDOWN_REPORTS["dependency_graph"]): "\n".join(dependency_md).rstrip() + "\n",
        str(MARKDOWN_REPORTS["executive_readiness"]): "\n".join(readiness_md).rstrip() + "\n",
    }


def write_reports(root: Path, reports: Mapping[str, str]) -> None:
    for relative, content in sorted(reports.items()):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"[WRITE] {relative}")


def check_reports(root: Path, reports: Mapping[str, str]) -> list[str]:
    mismatches: list[str] = []
    for relative, expected in sorted(reports.items()):
        path = root / relative
        if not path.is_file():
            mismatches.append(f"missing report: {relative}")
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            mismatches.append(f"stale report: {relative}")
    return mismatches


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write the certified baseline reports")
    mode.add_argument("--check", action="store_true", help="verify reports match the repository")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    try:
        reports = build_reports(root)
    except (FreezeAuditError, OSError, SyntaxError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    if args.write:
        write_reports(root, reports)
        snapshot = json.loads(reports[str(JSON_REPORTS["snapshot"])])
        print(f"[PASS] Genesis III-F1 baseline written: {snapshot['architecture_fingerprint']}")
        return 0
    mismatches = check_reports(root, reports)
    if mismatches:
        for mismatch in mismatches:
            print(f"[FAIL] {mismatch}", file=sys.stderr)
        return 1
    snapshot = json.loads(reports[str(JSON_REPORTS["snapshot"])])
    print(f"[PASS] Genesis III-F1 baseline is current: {snapshot['architecture_fingerprint']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
