"""Verify Genesis VII-A0 Pack 4A-3."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = (
    "core/executive/events/bootstrap.py",
    "core/executive/events/__init__.py",
    "core/src/routes/executive_event_runtime.py",
    "core/src/main.py",
    "tests/test_genesis_vii_a0_pack4a3_runtime_bootstrap.py",
    "docs/genesis/genesis_vii_a0/GENESIS_VII_A0_PACK_4A_3.md",
)


def check_main_contract() -> int:
    text = (ROOT / "core/src/main.py").read_text(encoding="utf-8")
    required = (
        "lifespan=lifespan",
        "executive_application_lifespan",
        "executive_event_runtime_router",
        "app.include_router(executive_operations_router)",
        "app.include_router(executive_event_runtime_router)",
    )
    missing = [item for item in required if item not in text]
    if missing:
        print(
            "[FAIL] FastAPI bootstrap contract: "
            + ", ".join(missing)
        )
        return 1

    print("[PASS] FastAPI bootstrap contract")
    return 0


def main() -> int:
    failures = 0

    for relative in REQUIRED:
        path = ROOT / relative
        if path.is_file() and path.stat().st_size > 0:
            print(f"[PASS] {relative}")
        else:
            print(f"[FAIL] {relative}")
            failures += 1

    failures += check_main_contract()

    compile_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "py_compile",
            *(str(ROOT / item) for item in REQUIRED
              if item.endswith(".py")),
        ],
        check=False,
    )
    if compile_result.returncode == 0:
        print("[PASS] Python compilation")
    else:
        print("[FAIL] Python compilation")
        failures += 1

    test_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "tests.test_genesis_vii_a0_pack4a1_event_bus",
            "tests.test_genesis_vii_a0_pack4a2_publishers",
            "tests.test_genesis_vii_a0_pack4a3_runtime_bootstrap",
            "-v",
        ],
        cwd=ROOT,
        check=False,
    )
    if test_result.returncode == 0:
        print("[PASS] Pack 4A regression")
    else:
        print("[FAIL] Pack 4A regression")
        failures += 1

    import_result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from core.src.main import app; "
                "assert app.title == 'JARVIS'; "
                "print('[PASS] FastAPI application import')"
            ),
        ],
        cwd=ROOT,
        check=False,
    )
    if import_result.returncode != 0:
        print("[FAIL] FastAPI application import")
        failures += 1

    print()
    print(f"Checks failed : {failures}")
    print(
        "Overall status: "
        + ("EXCELLENT" if failures == 0 else "REQUIRES CORRECTION")
    )
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
