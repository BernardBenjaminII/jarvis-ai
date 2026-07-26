#!/usr/bin/env python3
"""Certify typed and historical Projection Plane APIs."""

from __future__ import annotations

import ast
import hashlib
import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVICE = ROOT / "core/integration/service.py"
TEST = ROOT / "tests/test_genesis_vi_b0a_projection_compatibility.py"


def passed(message: str) -> None:
    print(f"[PASS] {message}")


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def service_methods() -> set[str]:
    tree = ast.parse(
        SERVICE.read_text(encoding="utf-8"),
        filename=str(SERVICE),
    )
    for node in tree.body:
        if (
            isinstance(node, ast.ClassDef)
            and node.name == "ExecutiveProjectionService"
        ):
            return {
                child.name
                for child in node.body
                if isinstance(
                    child,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                )
            }
    return set()


def main() -> int:
    methods = service_methods()
    required = {
        "projection",
        "projection_envelopes",
        "executive_projection",
        "all_projections",
    }
    missing = sorted(required - methods)
    if missing:
        fail(
            "ExecutiveProjectionService missing methods: "
            + ", ".join(missing)
        )
    passed("Typed and compatibility service methods")

    contracts = importlib.import_module("core.integration.contracts")
    registry_module = importlib.import_module("core.integration.registry")
    service_module = importlib.import_module("core.integration.service")

    ProjectionEnvelope = contracts.ProjectionEnvelope
    ProjectionHealth = contracts.ProjectionHealth
    ProjectionStatus = contracts.ProjectionStatus
    ExecutiveProjection = contracts.ExecutiveProjection
    ProjectionRegistry = registry_module.ProjectionRegistry
    ExecutiveProjectionService = (
        service_module.ExecutiveProjectionService
    )

    class FixtureProvider:
        projection_id = "fixture"
        schema_version = "1.0"

        def project(self):
            return ProjectionEnvelope(
                projection_id=self.projection_id,
                schema_version=self.schema_version,
                generated_at=datetime.now(timezone.utc),
                source_timestamp=None,
                provider="verification.FixtureProvider",
                health=ProjectionHealth(
                    status=ProjectionStatus.AVAILABLE,
                    summary="Fixture available.",
                ),
                data={"value": 1},
            )

    service = ExecutiveProjectionService(
        ProjectionRegistry((FixtureProvider(),))
    )

    typed = service.projection_envelopes()
    if not isinstance(typed, tuple):
        fail("projection_envelopes() must return tuple")
    if len(typed) != 1 or not isinstance(typed[0], ProjectionEnvelope):
        fail("projection_envelopes() returned invalid values")
    passed("Canonical typed envelope API")

    aggregate = service.executive_projection()
    if not isinstance(aggregate, ExecutiveProjection):
        fail("executive_projection() must return ExecutiveProjection")
    passed("Canonical typed aggregate API")

    compatibility = service.all_projections()
    if not isinstance(compatibility, dict):
        fail("all_projections() must return dictionary")
    if compatibility.get("provider_count") != 1:
        fail("Historical provider_count contract")
    if compatibility.get("summary", {}).get("available") != 1:
        fail("Historical status summary contract")
    expected = [item.to_dict() for item in typed]
    actual = compatibility.get("projections", [])

    if len(actual) != len(expected):
        fail("Compatibility projection serialization")

    for expected_item, actual_item in zip(expected, actual):
        expected_item = dict(expected_item)
        actual_item = dict(actual_item)

        # Each public API call executes providers independently, so the
        # generation timestamp is intentionally not compared.
        expected_item.pop("generated_at", None)
        actual_item.pop("generated_at", None)

        if actual_item != expected_item:
            fail("Compatibility projection serialization")
    passed("Historical UI/API compatibility contract")

    for module_name, description in (
        (
            "core.integration.bootstrap",
            "Integration bootstrap import boundary",
        ),
        (
            "core.src.routes.operations",
            "Operations route import boundary",
        ),
        (
            "core.src.main",
            "FastAPI application import boundary",
        ),
    ):
        importlib.import_module(module_name)
        passed(description)

    payload = SERVICE.read_bytes() + b"\0" + TEST.read_bytes()
    fingerprint = hashlib.sha256(payload).hexdigest()
    passed(f"VI-B0A compatibility fingerprint: {fingerprint}")

    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
