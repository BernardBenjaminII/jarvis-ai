from __future__ import annotations


def pct(value) -> str:
    if value is None:
        return "—"
    return f"{float(value):.1%}"


def render_summary(data: dict) -> str:
    summary = data["summary"]
    lines = [
        "# Genesis IX-A5.6 Pack 1 — Metadata Join and Lineage Audit",
        "",
        f"**Status:** **{data['status']}**",
        f"**Classification:** **{data['classification']}**",
        "",
        "## Summary",
        "",
        f"- Databases: **{summary['database_count']}**",
        f"- Tables: **{summary['table_count']}**",
        f"- Join candidates: **{summary['join_candidate_count']}**",
        f"- Preferred joins: **{summary['preferred_join_count']}**",
        f"- Usable joins: **{summary['usable_join_count']}**",
        f"- Metadata lineage paths: **{summary['metadata_lineage_count']}**",
        f"- Propagation paths: **{summary['propagation_path_count']}**",
        "",
        "## Top Join Candidates",
        "",
        "| Left | Right | Key | Left Match | Right Match | Ambiguous | Score | Recommendation |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]

    for join in summary["top_joins"]:
        lines.append(
            f"| `{join['left_database']}:{join['left_table']}.{join['left_column']}` | "
            f"`{join['right_database']}:{join['right_table']}.{join['right_column']}` | "
            f"`{join['normalized_key']}` | "
            f"{pct(join.get('left_match_rate'))} | "
            f"{pct(join.get('right_match_rate'))} | "
            f"{join.get('ambiguous_values', '—')} | "
            f"{float(join.get('score') or 0.0):.3f} | "
            f"**{join['recommendation']}** |"
        )

    lines.extend(
        [
            "",
            "## Metadata Lineage Paths",
            "",
            "| Source | Target | Key | Score | Category Fields | Propagation |",
            "|---|---|---|---:|---|---|",
        ]
    )

    for path in summary["top_lineage_paths"]:
        fields = (
            path["left_category_fields"]
            + path["right_category_fields"]
        )
        lines.append(
            f"| `{path['source']}` | `{path['target']}` | "
            f"`{path['normalized_key']}` | {path['score']:.3f} | "
            f"`{fields}` | {path['metadata_propagation_possible']} |"
        )

    lines.extend(["", "## Recommendations", ""])
    lines.extend(
        f"- {item}"
        for item in data["recommendations"]
    )

    return "\n".join(lines) + "\n"


def render_table_profiles(data: dict) -> str:
    lines = [
        "# Genesis IX-A5.6 Pack 1 — Table Profiles",
        "",
        "| Database | Table | Rows | Key/Metadata Columns |",
        "|---|---|---:|---|",
    ]

    for profile in data["table_profiles"]:
        names = [
            (
                f"{item['name']} "
                f"(coverage={item['coverage']:.1%}, "
                f"unique={item['uniqueness']:.1%})"
            )
            for item in profile["profiled_columns"]
        ]
        lines.append(
            f"| {profile['database']} | `{profile['table']}` | "
            f"{profile['row_count']} | {'; '.join(names)} |"
        )

    return "\n".join(lines) + "\n"
