"""Certification verifier for Genesis IV-B4 Audit Correction."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.observation.audit import audit_observation_definitions
from core.observation.export_audit import (
    module_defines_observation,
    scan_observation_exports,
)


REQUIRED_FILES = (
    "core/observation/export_audit.py",
    "tests/test_genesis_iv_b4_audit_correction.py",
    "dev/verification/verify_genesis_iv_b4_audit_correction.py",
    "dev/verify_genesis_4b4_audit_correction.sh",
    "docs/architecture/convergence/genesis_iv_b4_audit_correction.md",
)


def check(condition: bool, label: str) -> None:
    if not condition:
        print(f"[FAIL] {label}")
        raise SystemExit(1)
    print(f"[PASS] {label}")


def main() -> None:
    check(
        all((ROOT / path).is_file() for path in REQUIRED_FILES),
        "Canonical audit-correction file set",
    )

    check(
        module_defines_observation(
            ROOT / "core/cognition/common/contracts.py"
        ),
        "Direct Observation definition detected",
    )
    check(
        not module_defines_observation(
            ROOT / "core/cognition/contracts.py"
        ),
        "Public re-export excluded from definition ownership",
    )

    exports = scan_observation_exports(ROOT)
    check(
        any(
            item.path == "core/cognition/contracts.py"
            for item in exports
        ),
        "Public Observation export inventoried",
    )

    report = audit_observation_definitions(ROOT)
    paths = {item.path for item in report.definitions}
    check(
        "core/cognition/contracts.py" not in paths,
        "Re-export absent from governance definitions",
    )
    check(
        not report.forbidden_duplicates,
        "No false or ungoverned Observation duplicates",
    )


if __name__ == "__main__":
    main()
