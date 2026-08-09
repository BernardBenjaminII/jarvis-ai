from __future__ import annotations

import json
import sys
from pathlib import Path

_ENTRY_ROOT = Path(__file__).resolve().parents[1]
if str(_ENTRY_ROOT) not in sys.path:
    sys.path.insert(0, str(_ENTRY_ROOT))

from dev.runtime import bootstrap_runtime

RUNTIME = bootstrap_runtime(Path(__file__))
PROJECT_ROOT = RUNTIME.project_root

from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from dev.qualification_forensics import QualificationRecallAnalyzer


def render_markdown(data: dict) -> str:
    summary = data["summary"]
    lines = [
        "# Genesis IX-A5 Pack 3 — Qualification Recall Forensics",
        "",
        f"**Status:** **{data['status']}**",
        f"**Classification:** **{data['classification']}**",
        "",
        "## Summary",
        "",
        f"- Known probes: **{summary['known_probe_count']}**",
        f"- Raw recall: **{summary['known_raw_recall']:.1%}**",
        f"- Qualified recall: **{summary['known_qualified_recall']:.1%}**",
        f"- Top failure: **{summary.get('top_failure')}**",
        "",
        "## Rejection Reasons",
        "",
    ]

    reasons = summary.get("rejection_reasons") or {}
    if reasons:
        for key, value in reasons.items():
            lines.append(f"- `{key}`: **{value}**")
    else:
        lines.append("- None recorded.")

    lines.extend(
        [
            "",
            "## Probe Matrix",
            "",
            "| Probe | Query | Raw | Qualified | Dominant Failure |",
            "|---|---|---:|---:|---|",
        ]
    )

    for probe in data["probes"]:
        lines.append(
            f"| `{probe['probe_id']}` | {probe['query']} | "
            f"{probe['raw_count']} | {probe['qualified_count']} | "
            f"{probe.get('dominant_failure') or 'None'} |"
        )

    lines.extend(["", "## Candidate Forensics", ""])

    for probe in data["probes"]:
        lines.extend(
            [
                f"### {probe['probe_id']} — {probe['query']}",
                "",
                "| Rank | Title | Decision | Lexical | Phrase | Subject | Confidence | Final | Threshold | Margin | Reason |",
                "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
            ]
        )

        if not probe["candidates"]:
            lines.append(
                "| — | No candidate diagnostics | — | — | — | — | — | — | — | — | — |"
            )

        for item in probe["candidates"]:
            def fmt(value):
                return "—" if value is None else f"{value:.3f}"

            lines.append(
                f"| {item['raw_rank']} | {item['title']} | "
                f"{item['decision']} | {fmt(item['lexical_score'])} | "
                f"{fmt(item['phrase_score'])} | {fmt(item['subject_score'])} | "
                f"{fmt(item['confidence_score'])} | {fmt(item['final_score'])} | "
                f"{fmt(item['threshold'])} | {fmt(item['score_margin'])} | "
                f"{item.get('rejection_reason') or '—'} |"
            )

        lines.extend(["", "Recommendations:", ""])
        for recommendation in probe["recommendations"]:
            lines.append(f"- {recommendation}")
        lines.append("")

    lines.extend(["## Global Recommendations", ""])
    for recommendation in data["recommendations"]:
        lines.append(f"- {recommendation}")

    return "\n".join(lines) + "\n"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_CATALOG_DB,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT
        / "docs/audits/genesis_ix_a5_pack3",
    )
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    output = args.output_dir
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.mkdir(parents=True, exist_ok=True)

    report = QualificationRecallAnalyzer(
        database_path=args.database,
        limit=args.limit,
    ).execute()
    data = report.to_dict()

    (output / "qualification_forensics.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "qualification_forensics.md").write_text(
        render_markdown(data),
        encoding="utf-8",
    )

    print("=" * 76)
    print("GENESIS IX-A5 PACK 3 — QUALIFICATION RECALL FORENSICS")
    print("=" * 76)
    print("Classification :", data["classification"])
    print("Raw recall     :", f"{data['summary']['known_raw_recall']:.1%}")
    print("Qualified recall:", f"{data['summary']['known_qualified_recall']:.1%}")
    print("Top failure    :", data["summary"].get("top_failure"))
    print("Output         :", output)
    print("=" * 76)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
