#!/usr/bin/env python3
"""Structural and import-boundary verifier for Genesis VI-B0."""

from __future__ import annotations

import ast
import hashlib
import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

FILES = (
    ROOT / "core/integration/contracts.py",
    ROOT / "core/integration/errors.py",
    ROOT / "core/integration/registry.py",
    ROOT / "core/integration/service.py",
    ROOT / "core/integration/__init__.py",
)

EXPECTED = {
    ROOT / "core/integration/contracts.py": {
        "ProjectionStatus",
        "ProjectionHealth",
        "ProjectionEnvelope",
        "ExecutiveProjection",
    },
    ROOT / "core/integration/registry.py": {
        "CapabilityRegistry",
        "ProjectionRegistry",
    },
    ROOT / "core/integration/service.py": {
        "ExecutiveIntegrationService",
        "ExecutiveProjectionService",
    },
}


def definitions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef))
    }


def passed(message: str) -> None:
    print(f"[PASS] {message}")


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    for path in FILES:
        if not path.is_file():
            fail(f"Missing canonical file: {path.relative_to(ROOT)}")
    passed("Canonical Projection Plane file set")

    for path, expected in EXPECTED.items():
        missing = sorted(expected - definitions(path))
        if missing:
            fail(
                f"{path.relative_to(ROOT)} missing: {', '.join(missing)}"
            )
    passed("Canonical contract, registry, and service ownership")

    integration = importlib.import_module("core.integration")
    for name in (
        "ProjectionEnvelope",
        "ProjectionHealth",
        "ProjectionStatus",
        "ProjectionRegistry",
        "ExecutiveProjectionService",
    ):
        if not hasattr(integration, name):
            fail(f"Public Integration symbol missing: {name}")
    passed("Stable public Integration API")

    for module_name, description in (
        (
            "core.integration.providers.operations",
            "Operations projection provider",
        ),
        (
            "core.integration.providers.capabilities",
            "Capability projection provider",
        ),
        (
            "core.integration.providers.knowledge",
            "Knowledge projection provider",
        ),
        (
            "core.integration.bootstrap",
            "Integration bootstrap boundary",
        ),
        (
            "core.src.routes.operations",
            "Operations route boundary",
        ),
        (
            "core.src.main",
            "FastAPI application boundary",
        ),
    ):
        importlib.import_module(module_name)
        passed(description)

    payload = b"\0".join(path.read_bytes() for path in FILES)
    fingerprint = hashlib.sha256(payload).hexdigest()
    passed(f"Deterministic architecture fingerprint: {fingerprint}")

    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
