"""Command-line interface for Engineering OS compatibility analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .api_inventory import inventory_targets
from .compatibility import (
    analyze_compatibility,
    expectations_from_tests,
    load_expectations,
    save_expectations,
)
from .reporting import write_compatibility_report
from .restoration import build_restoration_plan


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jarvis-engineering",
        description="JARVIS Engineering OS read-only compatibility tooling.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap = subparsers.add_parser(
        "bootstrap-manifest",
        help="Derive expected public imports from test source.",
    )
    bootstrap.add_argument("--project-root", default=".")
    bootstrap.add_argument("--tests-root", default="tests")
    bootstrap.add_argument(
        "--output",
        default="dev/verification/manifests/test_public_api_expectations.json",
    )
    bootstrap.add_argument("--package-prefix", default="core.")

    analyze = subparsers.add_parser(
        "analyze",
        help="Compare an expectation manifest with observed package exports.",
    )
    analyze.add_argument("--project-root", default=".")
    analyze.add_argument(
        "--manifest",
        default="dev/verification/manifests/test_public_api_expectations.json",
    )
    analyze.add_argument(
        "--json-output",
        default=".artifacts/engineering/public_api_compatibility.json",
    )
    analyze.add_argument(
        "--report-output",
        default="docs/audits/public_api_compatibility_report.md",
    )
    return parser


def _bootstrap(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    tests = root / args.tests_root
    output = root / args.output
    expectations = expectations_from_tests(
        project_root=root,
        tests_root=tests,
        package_prefix=args.package_prefix,
    )
    save_expectations(expectations, output)
    print(f"Manifest written: {output}")
    print(f"Packages: {len(expectations)}")
    print(f"Symbols: {sum(len(item.expected_symbols) for item in expectations)}")
    return 0


def _analyze(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    manifest_path = root / args.manifest
    expectations = load_expectations(manifest_path)
    packages = tuple(item.package for item in expectations)

    inventories = inventory_targets(root, packages)
    report = analyze_compatibility(expectations, inventories)
    recommendations = build_restoration_plan(report)

    json_output = root / args.json_output
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(
        json.dumps(
            {
                "compatibility_score": report.compatibility_score,
                "fingerprint": report.fingerprint(),
                "findings": [
                    {
                        "package": item.package,
                        "symbol": item.symbol,
                        "finding_type": item.finding_type,
                        "severity": item.severity,
                        "explanation": item.explanation,
                        "implementation_candidates": list(
                            item.implementation_candidates
                        ),
                    }
                    for item in report.findings
                ],
                "recommendations": [
                    {
                        "package": item.package,
                        "symbol": item.symbol,
                        "action": item.action,
                        "target_file": item.target_file,
                        "source_module": item.source_module,
                        "rationale": item.rationale,
                        "confidence": item.confidence,
                    }
                    for item in recommendations
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    report_output = root / args.report_output
    write_compatibility_report(report, recommendations, report_output)

    print(f"Compatibility score: {report.compatibility_score:.2%}")
    print(f"Findings: {len(report.findings)}")
    print(f"JSON evidence: {json_output}")
    print(f"Markdown report: {report_output}")
    return 0 if not report.findings else 2


def main() -> int:
    args = _parser().parse_args()
    if args.command == "bootstrap-manifest":
        return _bootstrap(args)
    if args.command == "analyze":
        return _analyze(args)
    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
