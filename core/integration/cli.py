from __future__ import annotations

import argparse
import json
from pathlib import Path

from .serialization import to_canonical_data
from .service import ExecutiveIntegrationService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m core.integration.cli",
        description="Genesis IV-B1 RC1 integration and visibility tooling.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser(
        "audit",
        help="Audit repository integration and visibility.",
    )
    audit.add_argument("--repository-root", default=".")
    audit.add_argument(
        "--output",
        default="docs/audits/genesis_iv_b1_integration_audit.json",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    repository_root = Path(args.repository_root).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = repository_root / output

    projection = ExecutiveIntegrationService(
        repository_root
    ).integration_health()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            to_canonical_data(projection),
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    print(f"[PASS] Integration audit written: {output}")
    print(f"[INFO] Overall health: {projection.overall_health.value}")
    print(f"[INFO] Findings: {len(projection.findings)}")


if __name__ == "__main__":
    main()
