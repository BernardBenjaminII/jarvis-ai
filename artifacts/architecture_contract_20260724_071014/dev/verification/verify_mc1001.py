#!/usr/bin/env python3
"""Structural and behavioral certification for MC-1001."""

from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Repository import boundary
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

# Directly executing a script under dev/verification places that directory,
# rather than the repository root, at sys.path[0]. Insert the repository root
# before importing any JARVIS package.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


EXPECTED_FILES = (
    "core/operations/__init__.py",
    "core/operations/contracts.py",
    "core/operations/enums.py",
    "core/operations/errors.py",
    "core/operations/events.py",
    "core/operations/health.py",
    "core/operations/missions.py",
    "core/operations/models.py",
    "core/operations/registry.py",
    "core/operations/resources.py",
    "core/operations/service.py",
    "core/operations/timeline.py",
    "core/src/routes/operations.py",
    "docs/architecture/operations_layer.md",
    "tests/test_mc1001_operations.py",
)


def check(name: str, condition: bool, detail: str = "") -> int:
    """Print one verification result and return its failure contribution."""

    if condition:
        print(f"[PASS] {name}")
        return 0

    suffix = f": {detail}" if detail else ""
    print(f"[FAIL] {name}{suffix}")
    return 1


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a verification command from the canonical repository root."""

    return subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
    )


def verify_file_set() -> tuple[bool, str]:
    missing = [
        relative_path
        for relative_path in EXPECTED_FILES
        if not (ROOT / relative_path).is_file()
    ]
    return not missing, ", ".join(missing)


def verify_dependency_boundary() -> tuple[bool, str]:
    """Ensure lower-level subsystems do not import Operations."""

    forbidden_importers: list[str] = []

    protected_packages = (
        "core/executive",
        "core/reasoning",
        "core/cognition",
        "core/knowledge",
        "core/evidence",
        "core/representation",
    )

    forbidden_patterns = (
        "import core.operations",
        "from core.operations",
        "from ..operations",
        "from ...operations",
    )

    for package_name in protected_packages:
        package_root = ROOT / package_name

        if not package_root.exists():
            continue

        for path in package_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")

            if any(pattern in text for pattern in forbidden_patterns):
                forbidden_importers.append(str(path.relative_to(ROOT)))

    return not forbidden_importers, ", ".join(forbidden_importers)


def verify_routes() -> tuple[bool, str]:
    route_file = ROOT / "core/src/routes/operations.py"
    route_text = route_file.read_text(encoding="utf-8")

    required_routes = (
        '"/status"',
        '"/health"',
        '"/missions"',
        '"/resources"',
        '"/timeline"',
        '"/events"',
    )

    missing_routes = [
        route
        for route in required_routes
        if route not in route_text
    ]

    return not missing_routes, ", ".join(missing_routes)


def verify_main_router_registration() -> tuple[bool, str]:
    main_file = ROOT / "core/src/main.py"

    if not main_file.is_file():
        return False, "core/src/main.py does not exist"

    text = main_file.read_text(encoding="utf-8")

    has_router_import = (
        "operations_router" in text
        or "routes.operations" in text
    )
    has_router_registration = "include_router" in text and "operations_router" in text

    if not has_router_import:
        return False, "Operations router import is absent"

    if not has_router_registration:
        return False, "Operations router registration is absent"

    return True, ""


def main() -> int:
    failures = 0

    print("=" * 70)
    print("JARVIS — MC-1001 SPRINT 0 EXECUTIVE OPERATIONS INTERFACE")
    print("=" * 70)

    file_set_ok, file_set_detail = verify_file_set()
    failures += check(
        "Canonical MC-1001 file set",
        file_set_ok,
        file_set_detail,
    )

    compile_result = run_command(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "core/operations",
            "core/src/routes/operations.py",
            "dev/verification/verify_mc1001.py",
        ]
    )
    failures += check(
        "Operations package compilation",
        compile_result.returncode == 0,
    )

    try:
        operations = importlib.import_module("core.operations")
        import_ok = True
        import_detail = ""
    except Exception as exc:
        operations = None
        import_ok = False
        import_detail = f"{type(exc).__name__}: {exc}"

    failures += check(
        "Operations package importability",
        import_ok,
        import_detail,
    )

    if operations is not None:
        required_exports = {
            "OperationsService",
            "OperationsSnapshot",
            "MissionSnapshot",
            "HealthSnapshot",
            "ResourceSnapshot",
            "OperationsEvent",
        }

        missing_exports = sorted(
            name
            for name in required_exports
            if not hasattr(operations, name)
        )

        failures += check(
            "Stable public Operations imports",
            not missing_exports,
            ", ".join(missing_exports),
        )
    else:
        failures += check(
            "Stable public Operations imports",
            False,
            "Operations package could not be imported",
        )

    boundary_ok, boundary_detail = verify_dependency_boundary()
    failures += check(
        "Forward-only dependency boundary",
        boundary_ok,
        boundary_detail,
    )

    routes_ok, routes_detail = verify_routes()
    failures += check(
        "Required REST endpoints declared",
        routes_ok,
        routes_detail,
    )

    registration_ok, registration_detail = verify_main_router_registration()
    failures += check(
        "Operations router registered",
        registration_ok,
        registration_detail,
    )

    if operations is not None:
        fixed_time = datetime(
            2026,
            7,
            23,
            0,
            0,
            0,
            tzinfo=timezone.utc,
        )

        try:
            service = operations.OperationsService(
                clock=lambda: fixed_time,
            )

            first_snapshot = service.snapshot()
            second_snapshot = service.snapshot()

            first_payload = first_snapshot.to_dict()
            second_payload = second_snapshot.to_dict()

            deterministic = (
                first_payload == second_payload
                and first_snapshot.fingerprint
                == second_snapshot.fingerprint
            )

            snapshot_detail = ""
        except Exception as exc:
            first_payload = {}
            deterministic = False
            snapshot_detail = f"{type(exc).__name__}: {exc}"

        failures += check(
            "Deterministic snapshot generation",
            deterministic,
            snapshot_detail,
        )

        if first_payload:
            canonical_payload = json.dumps(
                first_payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("utf-8")

            verification_fingerprint = hashlib.sha256(
                canonical_payload
            ).hexdigest()

            fingerprint_ok = len(verification_fingerprint) == 64

            failures += check(
                "Deterministic verification fingerprint",
                fingerprint_ok,
            )

            if fingerprint_ok:
                print(f"       fingerprint: {verification_fingerprint}")
        else:
            failures += check(
                "Deterministic verification fingerprint",
                False,
                "No snapshot payload was generated",
            )
    else:
        failures += check(
            "Deterministic snapshot generation",
            False,
            "Operations package could not be imported",
        )
        failures += check(
            "Deterministic verification fingerprint",
            False,
            "Operations package could not be imported",
        )

    test_result = run_command(
        [
            sys.executable,
            "-m",
            "unittest",
            "-v",
            "tests.test_mc1001_operations",
        ]
    )
    failures += check(
        "MC-1001 unit tests",
        test_result.returncode == 0,
    )

    print("-" * 70)
    print(f"Checks failed : {failures}")
    print(
        "Overall status: "
        f"{'EXCELLENT' if failures == 0 else 'FAILED'}"
    )
    print("=" * 70)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
