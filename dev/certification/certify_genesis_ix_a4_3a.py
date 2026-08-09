from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def root():
    current = Path(__file__).resolve()
    for candidate in (current.parent, *current.parents):
        if all((candidate / name).is_dir() for name in ("core","dev","docs")):
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            return candidate
    raise RuntimeError("Unable to locate JARVIS root.")

ROOT = root()

from core.certification.runtime import CertificationRuntime
from core.retrieval.failure_analysis import CertificationFailureAnalyzer

def render(data):
    lines = [
        "# Genesis IX-A4.3A — Certification Failure Analyzer","",
        f"**Status:** **{data['status']}**",
        f"**Source status:** **{data['source_status']}**",
        f"**Failed checks:** **{data['failed_check_count']}**","",
        "## Summary","",
        f"- Blocking failures: **{data['summary']['blocking_failures']}**",
        f"- Non-blocking failures: **{data['summary']['non_blocking_failures']}**",
        f"- Next action: {data['summary']['recommended_next_action']}","",
    ]
    for item in data["analyses"]:
        lines += [
            f"## `{item['check_code']}` — {item['label']}","",
            f"- Classification: `{item['classification']}`",
            f"- Confidence: {item['confidence']:.2f}",
            f"- Blocking: {item['blocking']}",
            f"- Repair scope: {item['repair_scope']}",
            f"- Reason: {item['reason']}",
            f"- Recommended repair: {item['recommended_repair']}","",
            "### Evidence","",
        ]
        lines += [f"- {value}" for value in item["evidence"]]
        lines.append("")
    return "\n".join(lines) + "\n"

def matrix(data):
    lines = [
        "# Genesis IX-A4.3A — Failure Classification Matrix","",
        "| Check | Classification | Confidence | Blocking | Scope |",
        "|---|---|---:|---|---|",
    ]
    for item in data["analyses"]:
        lines.append(
            f"| `{item['check_code']}` | `{item['classification']}` | "
            f"{item['confidence']:.2f} | {item['blocking']} | {item['repair_scope']} |"
        )
    return "\n".join(lines) + "\n"

def repair(data):
    lines = [
        "# Genesis IX-A4.3A — Minimal Repair Plan","",
        f"**Next action:** {data['summary']['recommended_next_action']}","",
    ]
    for i, item in enumerate(data["analyses"], 1):
        lines += [
            f"## Repair {i}: `{item['check_code']}`","",
            f"**Scope:** {item['repair_scope']}","",
            item["recommended_repair"],"",
        ]
    return "\n".join(lines) + "\n"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--input", type=Path, default=Path("docs/audits/genesis_ix_a4_3/end_to_end_certification.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("docs/audits/genesis_ix_a4_3a"))
    args = parser.parse_args()

    runtime = CertificationRuntime(start=args.root).bootstrap()
    bootstrap = runtime.certify()

    input_path = args.input if args.input.is_absolute() else Path(bootstrap.repository_root) / args.input
    output = args.output_dir if args.output_dir.is_absolute() else Path(bootstrap.repository_root) / args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    data = CertificationFailureAnalyzer(input_path).analyze()
    (output / "failure_analysis.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "failure_analysis.md").write_text(render(data), encoding="utf-8")
    (output / "failure_classification_matrix.md").write_text(matrix(data), encoding="utf-8")
    (output / "minimal_repair_plan.md").write_text(repair(data), encoding="utf-8")

    print("=" * 76)
    print("GENESIS IX-A4.3A — CERTIFICATION FAILURE ANALYZER")
    print("=" * 76)
    print("Source status     :", data["source_status"])
    print("Failed checks     :", data["failed_check_count"])
    print("Blocking failures :", data["summary"]["blocking_failures"])
    print("Non-blocking      :", data["summary"]["non_blocking_failures"])
    print("Analyzer status   :", data["status"])
    print("Output            :", output)
    print("=" * 76)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
