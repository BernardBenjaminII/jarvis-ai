
#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.executive.integration_audit import IntegrationAuditor, write_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "artifacts/audit/genesis_vii_b0_integration_audit.json"),
    )
    args = parser.parse_args()

    report = IntegrationAuditor(args.project_root).run()
    output = write_report(report, args.output)

    print("=" * 72)
    print("JARVIS — GENESIS VII-B0 INTEGRATION AUDIT")
    print("=" * 72)
    print(f"Overall status : {report.overall_status.value.upper()}")
    print(f"Fingerprint    : {report.fingerprint}")
    print(f"Report         : {output}")
    print("-" * 72)
    for finding in report.findings:
        print(
            f"[{finding.status.value.upper():7}] "
            f"{finding.domain}/{finding.observable} — {finding.summary}"
        )
    print("=" * 72)
    return 1 if report.overall_status.value == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
