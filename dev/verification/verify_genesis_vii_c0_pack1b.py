#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

from core.governance.audit import RepositoryInventoryBuilder, RepositoryInventoryVerifier


def _print_result(passed: bool, label: str, detail: str | None = None) -> bool:
    print(f"[{'PASS' if passed else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    return passed


def _run_unit_tests(project_root: Path) -> bool:
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(project_root / "tests"),
        pattern="test_genesis_vii_c0_pack1b.py",
        top_level_dir=str(project_root),
    )
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return result.wasSuccessful()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Genesis VII-C0 Pack 1B.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--output", type=Path, default=Path("artifacts/audit/km0000-r1"), help="Audit artifact directory")
    parser.add_argument("--skip-unit-tests", action="store_true")
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    output = args.output if args.output.is_absolute() else root / args.output

    print("=" * 72)
    print("GENESIS VII-C0 — PACK 1B REPOSITORY DISCOVERY CERTIFICATION")
    print("=" * 72)

    checks_failed = 0
    if not args.skip_unit_tests:
        unit_ok = _run_unit_tests(root)
        if not _print_result(unit_ok, "Pack 1B unit tests"):
            checks_failed += 1

    builder = RepositoryInventoryBuilder()
    first = builder.build(root)
    second = builder.build(root)
    deterministic = first == second and first.fingerprint == second.fingerprint
    if not _print_result(deterministic, "Deterministic repository inventory", first.fingerprint):
        checks_failed += 1

    builder.write_outputs(first, output)
    verifier = RepositoryInventoryVerifier()
    report = verifier.verify(first, root=root)
    manifest = verifier.build_manifest(first, report)
    verifier.write_outputs(report, manifest, output)

    for check in report.checks:
        if not _print_result(check.passed, check.description, check.detail):
            checks_failed += 1

    expected_outputs = (
        "repository_inventory.json",
        "repository_statistics.json",
        "documentation_inventory.json",
        "verification_report.json",
        "manifest.json",
        "certification_report.md",
    )
    outputs_ok = all((output / name).is_file() for name in expected_outputs)
    if not _print_result(outputs_ok, "Canonical certification artifact set", str(output.relative_to(root) if output.is_relative_to(root) else output)):
        checks_failed += 1

    print("-" * 72)
    print(f"Repository files     : {first.statistics.total_files}")
    print(f"Python modules       : {first.statistics.python_modules}")
    print(f"Python symbols       : {first.statistics.python_symbols}")
    print(f"Markdown documents   : {first.statistics.markdown_documents}")
    print(f"Diagnostics          : {first.statistics.diagnostics}")
    print(f"Parse coverage       : {report.health.coverage_percent:.6f}%")
    print(f"Repository fingerprint: {first.fingerprint}")
    print("-" * 72)
    print(f"Checks failed : {checks_failed}")
    print(f"Overall status: {'EXCELLENT' if checks_failed == 0 else 'FAILED'}")
    print("=" * 72)
    return 0 if checks_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
