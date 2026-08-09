def pct(value):
    return f"{float(value):.2%}"

def authority_md(data):
    lines = [
        "# Genesis IX-A5.8 Pack 1 — Corpus Authority Resolution",
        "",
        f"**Status:** **{data['status']}**",
        f"**Classification:** **{data['classification']}**",
        "",
        "## Authority Ranking",
        "",
        "| Rank | Database | Score | Configured Runtime | Role | Reasons |",
        "|---:|---|---:|---|---|---|",
    ]
    for item in data["authorities"]:
        lines.append(
            f"| {item['rank']} | `{item['path']}` | {item['authority_score']:.1f} | "
            f"{item['configured_runtime']} | `{item['recommended_role']}` | "
            f"`{item['authority_reasons']}` |"
        )
    return "\n".join(lines) + "\n"

def pipeline_md(data):
    lines = [
        "# Genesis IX-A5.8 Pack 1 — Materialization Pipeline Trace",
        "",
        "| Stage | Table | Present | Rows | Identity Columns |",
        "|---|---|---|---:|---|",
    ]
    for item in data["pipeline_stages"]:
        lines.append(
            f"| `{item['stage']}` | `{item['table']}` | {item['present']} | "
            f"{item['row_count']:,} | `{item['identity_columns']}` |"
        )
    lines += [
        "",
        "## Lineage Edges",
        "",
        "| Source | Target | Identity | Match Rate | Target/Source | Classification |",
        "|---|---|---|---:|---:|---|",
    ]
    for edge in data["lineage_edges"]:
        match = "—" if edge["source_match_rate"] is None else pct(edge["source_match_rate"])
        lines.append(
            f"| `{edge['source_stage']}` | `{edge['target_stage']}` | "
            f"`{edge['identity_pair']}` | {match} | "
            f"{edge['target_to_source_ratio']:.4f} | `{edge['classification']}` |"
        )
    return "\n".join(lines) + "\n"

def dropoff_md(data):
    d = data["dropoff"]
    lines = [
        "# Genesis IX-A5.8 Pack 1 — Corpus Drop-Off",
        "",
        f"- Catalog base: **{d['catalog_base']:,}**",
        f"- Runtime documents: **{d['runtime_documents']:,}**",
        f"- Unmaterialized catalog objects: **{d['unmaterialized_catalog_objects']:,}**",
        f"- Materialization rate: **{pct(d['materialization_rate'])}**",
        f"- Runtime chunks: **{d['runtime_chunks']:,}**",
        f"- Chunks per runtime document: **{d['chunks_per_runtime_document']:.2f}**",
        f"- Runtime FTS rows: **{d['runtime_fts_rows']:,}**",
        f"- FTS chunk coverage: **{pct(d['fts_chunk_coverage'])}**",
        "",
        "## Recommendations",
        "",
    ]
    lines.extend(f"- {item}" for item in data["recommendations"])
    return "\n".join(lines) + "\n"

def summary_md(data):
    s = data["summary"]
    return "\n".join([
        "# Genesis IX-A5.8 Pack 1 — Executive Findings",
        "",
        f"**Status:** **{data['status']}**",
        f"**Classification:** **{data['classification']}**",
        "",
        f"- Authoritative catalog: `{s['authoritative_path']}`",
        f"- Configured catalog is authoritative: **{s['configured_catalog_is_authoritative']}**",
        f"- Catalog base: **{s['catalog_base']:,}**",
        f"- Runtime documents: **{s['runtime_documents']:,}**",
        f"- Materialization rate: **{pct(s['materialization_rate'])}**",
        f"- Runtime chunks: **{s['runtime_chunks']:,}**",
        f"- Runtime FTS rows: **{s['runtime_fts_rows']:,}**",
        f"- FTS chunk coverage: **{pct(s['fts_chunk_coverage'])}**",
        "",
        "## First Non-Strong Edge",
        "",
        f"`{s['first_non_strong_edge']}`",
        "",
    ]) + "\n"
