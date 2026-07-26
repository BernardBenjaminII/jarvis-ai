"""Certification verifier for Genesis IV-B4A.1."""

from __future__ import annotations

from pathlib import Path
import inspect
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.observation.contracts import ObservationContext  # noqa: E402
from core.observation.migration import _make_context  # noqa: E402

REQUIRED_FILES = (
    "core/observation/migration.py",
    "tests/test_genesis_iv_b4a1_context_repair.py",
    "dev/verification/verify_genesis_iv_b4a1.py",
    "dev/verify_genesis_4b4a1.sh",
)


def check(condition: bool, label: str) -> None:
    if not condition:
        print(f"[FAIL] {label}")
        raise SystemExit(1)
    print(f"[PASS] {label}")


def main() -> None:
    check(
        all((ROOT / path).is_file() for path in REQUIRED_FILES),
        "Canonical IV-B4A.1 file set",
    )

    context = _make_context({"legacy_contract": "verification"})
    check(
        isinstance(context, ObservationContext),
        "Canonical ObservationContext constructed",
    )

    signature = inspect.signature(ObservationContext)
    print(f"[PASS] ObservationContext signature: {signature}")


if __name__ == "__main__":
    main()
