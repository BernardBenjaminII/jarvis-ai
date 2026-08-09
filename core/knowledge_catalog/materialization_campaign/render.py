from __future__ import annotations


def render_report(data: dict) -> str:
    lines = [
        "# Genesis IX-A6 — Full Corpus Materialization Campaign",
        "",
        f"**Campaign:** `{data['campaign_id']}`",
        f"**Status:** **{data['status']}**",
        f"**Classification:** **{data['classification']}**",
        f"**Dry run:** **{data['dry_run']}**",
        "",
        "## Progress",
        "",
        f"- Batches completed: **{data['batches_completed']}**",
        f"- Candidates examined: **{data['candidates_examined']:,}**",
        f"- Elapsed seconds: **{data['elapsed_seconds']:.2f}**",
        f"- Checkpoint database: `{data['checkpoint_db']}`",
        "",
        "## Runtime Counts",
        "",
        "| Store | Before | After | Delta |",
        "|---|---:|---:|---:|",
    ]

    for name in (
        "runtime_documents",
        "runtime_chunks",
        "runtime_chunks_fts",
    ):
        before = int(data["pre_counts"].get(name, 0))
        after = int(data["post_counts"].get(name, 0))
        lines.append(
            f"| `{name}` | {before:,} | "
            f"{after:,} | {after-before:,} |"
        )

    lines.extend(
        [
            "",
            "## Dispositions",
            "",
        ]
    )
    lines.extend(
        f"- `{name}`: **{count:,}**"
        for name, count in data[
            "disposition_counts"
        ].items()
    )

    lines.extend(
        [
            "",
            "## Batch Reports",
            "",
            "| Batch | Status | Candidates | Seconds | Document Δ | Chunk Δ | FTS Δ |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )

    for batch in data["reports"]:
        document_delta = (
            batch["post_counts"]["runtime_documents"]
            - batch["pre_counts"]["runtime_documents"]
        )
        chunk_delta = (
            batch["post_counts"]["runtime_chunks"]
            - batch["pre_counts"]["runtime_chunks"]
        )
        fts_delta = (
            batch["post_counts"]["runtime_chunks_fts"]
            - batch["pre_counts"]["runtime_chunks_fts"]
        )
        lines.append(
            f"| `{batch['batch_id']}` | "
            f"{batch['status']} | "
            f"{batch['candidate_count']} | "
            f"{batch['elapsed_seconds']:.2f} | "
            f"{document_delta} | {chunk_delta} | {fts_delta} |"
        )

    lines.extend(
        [
            "",
            "## Recommendations",
            "",
        ]
    )
    lines.extend(
        f"- {item}"
        for item in data["recommendations"]
    )

    return "\n".join(lines) + "\n"
