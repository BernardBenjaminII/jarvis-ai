#!/usr/bin/env python3
"""Structural verifier for Genesis VI-B0."""

from __future__ import annotations

import ast
import hashlib
import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "core/integration/contracts.py"
INIT = ROOT / "core/integration/__init__.py"

REQUIRED_CONTRACTS = {
    "ProjectionEnvelope",
    "ProjectionHealth",
    "ProjectionStatus",
    "ExecutiveProjection",
    "CapabilityProjection",
    "IntegrationHealthProjection",
    "CommanderBriefProjection",
    "MissionControlProjection",
}

REQUIRED_PUBLIC = {
    "ProjectionEnvelope",
    "ProjectionHealth",
    "ProjectionStatus",
    "ExecutiveProjection",
}


def passed(message: str) -> None:
    print(f"[PASS] {message}")


def failed(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def direct_symbols(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }


def main() -> int:
    if not CONTRACTS.is_file() or not INIT.is_file():
        failed("Canonical Integration files are missing")

    symbols = direct_symbols(CONTRACTS)
    missing = sorted(REQUIRED_CONTRACTS - symbols)
    if missing:
        failed(f"Missing canonical contracts: {', '.join(missing)}")
    passed("Canonical provider and executive contract families")

    module = importlib.import_module("core.integration")
    missing_public = sorted(
        name for name in REQUIRED_PUBLIC if not hasattr(module, name)
    )
    if missing_public:
        failed(f"Missing public Integration symbols: {', '.join(missing_public)}")
    passed("Stable public Integration API")

    provider_module = importlib.import_module(
        "core.integration.providers.capabilities"
    )
    if not hasattr(provider_module, "CapabilityProjectionProvider"):
        failed("CapabilityProjectionProvider is unavailable")
    passed("Capability provider import boundary")

    importlib.import_module("core.integration.bootstrap")
    passed("Integration bootstrap import boundary")

    importlib.import_module("core.src.routes.operations")
    passed("Operations route import boundary")

    importlib.import_module("core.src.main")
    passed("FastAPI application import boundary")

    payload = CONTRACTS.read_bytes() + b"\0" + INIT.read_bytes()
    fingerprint = hashlib.sha256(payload).hexdigest()
    passed(f"Deterministic architecture fingerprint: {fingerprint}")

    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
