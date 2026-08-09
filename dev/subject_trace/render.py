from __future__ import annotations


def fmt(value) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return str(value)


def render_markdown(data: dict) -> str:
    summary = data["summary"]
    lines = [
        "# Genesis IX-A5 Pack 4 — Subject Qualification Trace",
        "",
        f"**Status:** **{data['status']}**",
        f"**Classification:** **{data['classification']}**",
        "",
        "## Summary",
        "",
        f"- Probes: **{summary['probe_count']}**",
        f"- Candidates: **{summary['candidate_count']}**",
        f"- Missing subject metadata: **{summary['missing_subject_metadata']}**",
        f"- Taxonomy mismatches: **{summary['taxonomy_mismatches']}**",
        f"- Zero subject scores: **{summary['zero_subject_scores']}**",
        f"- Top diagnosis: **{summary.get('top_diagnosis') or 'None'}**",
        "",
        "## Diagnosis Counts",
        "",
    ]

    diagnoses = summary.get("diagnoses") or {}
    lines.extend(
        [
            f"- `{key}`: **{value}**"
            for key, value in diagnoses.items()
        ]
        or ["- None."]
    )

    lines.extend(
        [
            "",
            "## Subject Heatmap",
            "",
            "| Subject | Candidates | Exact | Alias | Missing | Mismatch | Accepted | Acceptance | Avg Subject Score |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )

    for subject, bucket in sorted(
        summary.get("heatmap", {}).items()
    ):
        lines.append(
            f"| `{subject}` | {bucket['candidates']} | "
            f"{bucket['exact_matches']} | {bucket['alias_matches']} | "
            f"{bucket['missing_metadata']} | "
            f"{bucket['taxonomy_mismatches']} | "
            f"{bucket['accepted']} | "
            f"{bucket['acceptance_rate']:.1%} | "
            f"{bucket['average_subject_score']:.3f} |"
        )

    lines.extend(["", "## Probe Traces", ""])

    for probe in data["probes"]:
        lines.extend(
            [
                f"### {probe['probe_id']} — {probe['query']}",
                "",
                f"- Normalized query: `{probe['normalized_query']}`",
                f"- Query tokens: `{probe['query_tokens']}`",
                f"- Detected subjects: `{probe['detected_subjects']}`",
                f"- Raw rows: **{probe['raw_count']}**",
                f"- Qualified rows: **{probe['qualified_count']}**",
                f"- Dominant diagnosis: **{probe.get('dominant_diagnosis') or 'None'}**",
                "",
                "| Candidate | Stored Subjects | Domain | Exact | Alias | Overlap | Subject Score | Final | Threshold | Decision | Diagnosis |",
                "|---|---|---|---|---|---:|---:|---:|---:|---|---|",
            ]
        )

        if not probe["candidates"]:
            lines.append(
                "| No candidates | — | — | — | — | — | — | — | — | — | — |"
            )

        for candidate in probe["candidates"]:
            lines.append(
                f"| {candidate['title']} | "
                f"`{candidate['candidate_subjects']}` | "
                f"`{candidate['candidate_domain']}` | "
                f"`{candidate['exact_matches']}` | "
                f"`{candidate['alias_matches']}` | "
                f"{candidate['overlap_score']:.3f} | "
                f"{fmt(candidate['subject_score'])} | "
                f"{fmt(candidate['final_score'])} | "
                f"{fmt(candidate['threshold'])} | "
                f"{candidate['decision']} | "
                f"{candidate['diagnosis']} |"
            )

        lines.append("")

    lines.extend(["## Recommendations", ""])
    lines.extend(
        f"- {item}"
        for item in data["recommendations"]
    )

    return "\n".join(lines) + "\n"
