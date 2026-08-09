#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path

LAYERS = {"models": 0, "relationships": 1, "serialization": 2, "registry": 3, "executive": 4}
FORBIDDEN = (
    "fastapi", "sqlite3", "sqlalchemy", "psycopg", "lmdb",
    "requests", "httpx", "subprocess", "asyncio",
    "core.src", "core.executive.director",
)
REQUIRED = (
    "docs/constitution/GOA-0000_ORGANIZATIONAL_CONSTITUTION.md",
    *tuple(f"dev/verify_genesis_viii_a0_{i}.sh" for i in range(1, 6)),
    *tuple(
        f"tests/test_genesis_viii_a0_{i}_{name}.py"
        for i, name in (
            (1, "constitutional_object_model"),
            (2, "government_relationships"),
            (3, "canonical_government_serialization"),
            (4, "organizational_registry_interfaces"),
            (5, "executive_integration_contracts"),
        )
    ),
    *tuple(
        f"docs/architecture/genesis_viii_a0_{i}_{name}.md"
        for i, name in (
            (1, "constitutional_object_model"),
            (2, "government_relationships"),
            (3, "canonical_government_serialization"),
            (4, "organizational_registry_interfaces"),
            (5, "executive_integration_contracts"),
        )
    ),
)


@dataclass(frozen=True, slots=True)
class Finding:
    finding_id: str
    status: str
    summary: str
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return asdict(self)


def imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.append(node.module)
    return tuple(sorted(set(result)))


def source_fingerprint(root: Path, files: tuple[Path, ...]) -> str:
    digest = sha256()
    for path in sorted(files):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def architecture_fingerprint(findings: tuple[Finding, ...]) -> str:
    payload = [item.to_dict() for item in sorted(findings, key=lambda x: x.finding_id)]
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def path_layer(path: Path) -> str | None:
    parts = path.parts
    if "government" not in parts:
        return None
    index = parts.index("government")
    if len(parts) <= index + 1:
        return None
    layer = parts[index + 1]
    return layer if layer in LAYERS else None


def module_layer(module: str) -> str | None:
    prefix = "core.government."
    if not module.startswith(prefix):
        return None
    layer = module[len(prefix):].split(".", 1)[0]
    return layer if layer in LAYERS else None


def certify(root: Path) -> dict:
    files = tuple(
        sorted(
            path for path in (root / "core/government").rglob("*.py")
            if "__pycache__" not in path.parts
        )
    )

    missing = tuple(path for path in REQUIRED if not (root / path).is_file())
    required = Finding(
        "required-artifacts",
        "pass" if not missing else "fail",
        "All prerequisite verifiers, tests, documents, and GOA-0000 are present."
        if not missing else "Required Government Framework artifacts are missing.",
        missing or (f"required_artifacts={len(REQUIRED)}",),
    )

    forbidden: list[str] = []
    direction: list[str] = []
    edges: set[str] = set()

    for path in files:
        source_layer = path_layer(path)
        for module in imports(path):
            if module.startswith(FORBIDDEN):
                forbidden.append(f"{path.relative_to(root)} -> {module}")
            target_layer = module_layer(module)
            if source_layer and target_layer and source_layer != target_layer:
                edges.add(f"{source_layer}->{target_layer}")
                if LAYERS[target_layer] > LAYERS[source_layer]:
                    direction.append(
                        f"{path.relative_to(root)}: {source_layer}->{target_layer}"
                    )

    forbidden_finding = Finding(
        "forbidden-imports",
        "pass" if not forbidden else "fail",
        "No runtime, persistence, web, process, or legacy Executive imports."
        if not forbidden else "Forbidden imports were detected.",
        tuple(sorted(forbidden)) or ("violations=0",),
    )

    direction_finding = Finding(
        "dependency-direction",
        "pass" if not direction else "fail",
        "Dependencies flow only toward lower constitutional layers."
        if not direction else "Dependency direction violations were detected.",
        tuple(sorted(direction)) or tuple(sorted(edges)),
    )

    public_source = (root / "core/government/__init__.py").read_text(encoding="utf-8")
    expected_exports = tuple(
        f"from .{name} import *"
        for name in ("models", "relationships", "serialization", "registry", "executive")
    )
    absent = tuple(item for item in expected_exports if item not in public_source)
    public_api = Finding(
        "public-api",
        "pass" if not absent else "fail",
        "The Government public API exports all certified layers."
        if not absent else "Government public API exports are incomplete.",
        absent or expected_exports,
    )

    interface_files = (
        root / "core/government/registry/interfaces.py",
        root / "core/government/registry/repository.py",
        root / "core/government/registry/provider.py",
        root / "core/government/registry/transaction.py",
        root / "core/government/executive/interfaces.py",
    )
    concrete: list[str] = []
    for path in interface_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                bases = {base.id for base in node.bases if isinstance(base, ast.Name)}
                if "ABC" not in bases:
                    concrete.append(f"{path.relative_to(root)}:{node.name}")

    boundaries = Finding(
        "abstract-boundaries",
        "pass" if not concrete else "fail",
        "Registry and Executive integration boundaries remain abstract."
        if not concrete else "Concrete interface classes were detected.",
        tuple(sorted(concrete)) or ("concrete_interface_classes=0",),
    )

    findings = (required, forbidden_finding, direction_finding, public_api, boundaries)
    status = "pass" if all(item.status == "pass" for item in findings) else "fail"

    return {
        "schema_version": "1.0.0",
        "framework": "JARVIS Government Framework",
        "framework_version": "Genesis VIII-A0",
        "status": status,
        "source_fingerprint": source_fingerprint(root, files),
        "architecture_fingerprint": architecture_fingerprint(findings),
        "findings": [item.to_dict() for item in findings],
    }


def write_artifacts(root: Path, certification: dict) -> None:
    output = root / "artifacts/audit"
    output.mkdir(parents=True, exist_ok=True)

    (output / "government_framework_certification.json").write_text(
        json.dumps(certification, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Government Framework Certification",
        "",
        f"**Framework:** {certification['framework']}  ",
        f"**Version:** {certification['framework_version']}  ",
        f"**Certification:** `{certification['status'].upper()}`  ",
        f"**Source fingerprint:** `{certification['source_fingerprint']}`  ",
        f"**Architecture fingerprint:** `{certification['architecture_fingerprint']}`",
        "",
        "## Findings",
        "",
    ]
    for finding in certification["findings"]:
        lines.extend(
            [
                f"### {finding['finding_id']}",
                "",
                f"**Status:** `{finding['status'].upper()}`",
                "",
                finding["summary"],
                "",
                *[f"- `{item}`" for item in finding["evidence"]],
                "",
            ]
        )

    (output / "government_framework_certification.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    (output / "government_framework.sha256").write_text(
        f"{certification['source_fingerprint']}  core/government\n",
        encoding="utf-8",
    )


def main() -> int:
    root = Path(".").resolve()
    certification = certify(root)
    write_artifacts(root, certification)

    print("=" * 72)
    print("JARVIS — GENESIS VIII-A0-6")
    print("GOVERNMENT FRAMEWORK CERTIFICATION")
    print("=" * 72)
    print(f"Certification           : {certification['status'].upper()}")
    print(f"Source fingerprint      : {certification['source_fingerprint']}")
    print(f"Architecture fingerprint: {certification['architecture_fingerprint']}")
    print("-" * 72)
    for finding in certification["findings"]:
        print(
            f"[{finding['status'].upper():4}] "
            f"{finding['finding_id']} — {finding['summary']}"
        )
    print("=" * 72)
    return 0 if certification["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
