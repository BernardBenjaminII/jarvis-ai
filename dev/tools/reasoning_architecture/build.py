from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .loader import BaselineBuildError, describe_report, load_json, validate_reports
from .renderers import render_json, render_markdown
from .synthesis import synthesize

PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_ROOT = PROJECT_ROOT / "docs/architecture/convergence"
A1_REPORT = REPORT_ROOT / "genesis_1a1_reasoning_contract_audit.json"
A2_REPORT = REPORT_ROOT / "genesis_1a2_reasoning_service_audit.json"
A3_REPORT = REPORT_ROOT / "genesis_1a3_knowledge_integration_audit.json"
JSON_OUTPUT = REPORT_ROOT / "genesis_1a4_reasoning_architecture_baseline.json"
MARKDOWN_OUTPUT = REPORT_ROOT / "genesis_1a4_reasoning_architecture_baseline.md"


def build() -> tuple[dict, str, str]:
    a1, a2, a3 = load_json(A1_REPORT), load_json(A2_REPORT), load_json(A3_REPORT)
    validate_reports(a1, a2, a3)
    sources = [
        describe_report(PROJECT_ROOT, "Genesis I-A1", A1_REPORT, a1),
        describe_report(PROJECT_ROOT, "Genesis I-A2", A2_REPORT, a2),
        describe_report(PROJECT_ROOT, "Genesis I-A3", A3_REPORT, a3),
    ]
    baseline = synthesize(sources)
    return baseline, render_json(baseline), render_markdown(baseline)


def check(path: Path, expected: str) -> bool:
    if not path.is_file():
        print(f"[FAIL] Missing output: {path.relative_to(PROJECT_ROOT)}")
        return False
    if path.read_text(encoding="utf-8") != expected:
        print(f"[FAIL] Stale output: {path.relative_to(PROJECT_ROOT)}")
        return False
    print(f"[PASS] Current output: {path.relative_to(PROJECT_ROOT)}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the canonical JARVIS reasoning architecture baseline.")
    parser.add_argument("--check", action="store_true", help="Fail when generated outputs are missing or stale.")
    args = parser.parse_args()
    try:
        baseline, json_content, markdown_content = build()
    except (BaselineBuildError, OSError, ValueError) as exc:
        print(f"[FAIL] {exc}")
        return 1
    if args.check:
        return 0 if check(JSON_OUTPUT, json_content) and check(MARKDOWN_OUTPUT, markdown_content) else 1
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(json_content, encoding="utf-8")
    MARKDOWN_OUTPUT.write_text(markdown_content, encoding="utf-8")
    print(f"[WRITE] {JSON_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"[WRITE] {MARKDOWN_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"[PASS] Baseline fingerprint: {baseline['baseline_fingerprint']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
