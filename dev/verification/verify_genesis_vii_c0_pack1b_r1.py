from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.governance.audit import RepositoryInventoryBuilder, RepositoryInventoryVerifier


def result(ok: bool, label: str, detail: str = "") -> bool:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    return ok


def main() -> int:
    root = PROJECT_ROOT
    output = root / "artifacts" / "audit" / "km0000-r1"
    failed = 0
    print("=" * 72)
    print("GENESIS VII-C0 — PACK 1B-R1 EVIDENCE CLASSIFICATION REVISION")
    print("=" * 72)

    env = dict(os.environ); env["PYTHONPATH"] = str(root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    test = subprocess.run([sys.executable, "-m", "unittest", "tests.test_genesis_vii_c0_pack1b_r1"], cwd=root, env=env, check=False)
    if not result(test.returncode == 0, "Pack 1B-R1 unit tests"):
        failed += 1

    builder = RepositoryInventoryBuilder()
    first = builder.build(root); second = builder.build(root)
    if not result(first == second and first.fingerprint == second.fingerprint, "Deterministic repository inventory", first.fingerprint):
        failed += 1

    report = RepositoryInventoryVerifier().verify(first, root=root)
    for check in report.checks:
        if not result(check.passed, check.description, check.detail): failed += 1

    builder.write_outputs(first, output)
    verifier = RepositoryInventoryVerifier(); manifest = verifier.build_manifest(first, report)
    verifier.write_outputs(report, manifest, output)
    for check in verifier.verify_artifacts(output, first):
        if not result(check.passed, check.description, check.detail): failed += 1

    # Critical regression: writing generated artifacts must not invalidate source hashes.
    post = verifier.verify(first, root=root)
    regression_ok = all(c.passed for c in post.checks if c.check_id in {"SOURCE-PRESENCE", "SOURCE-HASHES"})
    if not result(regression_ok, "Generated audit outputs do not invalidate repository source integrity"):
        failed += 1

    print("-" * 72)
    print(f"Repository files       : {first.statistics.total_files}")
    print(f"Source files           : {first.statistics.source_files}")
    print(f"Generated files        : {first.statistics.generated_files}")
    print(f"External files         : {first.statistics.external_files}")
    print(f"Repository fingerprint : {first.fingerprint}")
    print("-" * 72)
    print(f"Checks failed : {failed}")
    print(f"Overall status: {'EXCELLENT' if failed == 0 else 'FAILED'}")
    print("=" * 72)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
