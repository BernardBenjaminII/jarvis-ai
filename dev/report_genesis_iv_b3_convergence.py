#!/usr/bin/env python3
"""Generate Genesis IV-B3 Observation convergence audit artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.observation.audit import (  # noqa: E402
    audit_observation_definitions,
    format_observation_convergence_report,
    write_observation_convergence_reports,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate deterministic Genesis IV-B3 Observation "
            "convergence reports."
        )
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=ROOT,
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=ROOT / "docs" / "audits",
    )
    parser.add_argument(
        "--require-converged",
        action="store_true",
        help="Return a non-zero exit code when the repository is not converged.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = audit_observation_definitions(
        args.repository_root
    )
    json_path, markdown_path = (
        write_observation_convergence_reports(
            report,
            args.output_directory,
        )
    )

    print(format_observation_convergence_report(report))
    print(f"[PASS] JSON report     : {json_path}")
    print(f"[PASS] Markdown report : {markdown_path}")

    if args.require_converged and not report.converged:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
