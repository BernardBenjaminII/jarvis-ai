def pct(value):
    return f"{float(value):.2%}"

def summary_md(data):
    s = data["summary"]
    lines = [
        "# Genesis IX-A5.8 Pack 2 — Materializer Eligibility Audit",
        "",
        f"**Status:** **{data['status']}**",
        f"**Classification:** **{data['classification']}**",
        "",
        "## Summary",
        "",
        f"- Candidate records: **{s['candidate_count']:,}**",
        f"- Runtime documents: **{s['runtime_document_count']:,}**",
        f"- Already materialized: **{s['already_materialized']:,}**",
        f"- Eligible but not selected: **{s['eligible_not_selected']:,}**",
        f"- Eligible selection rate: **{pct(s['selection_rate_among_eligible'])}**",
        f"- Missing sources: **{s['missing_source_count']:,}**",
        f"- Unsupported: **{s['unsupported_count']:,}**",
        f"- Containers/archives: **{s['container_count']:,}**",
        f"- Failures: **{s['failure_count']:,}**",
        "",
        "## Disposition Counts",
        "",
    ]
    lines.extend(
        f"- `{name}`: **{count:,}**"
        for name, count in s["disposition_counts"].items()
    )
    lines += ["", "## Recommendations", ""]
    lines.extend(f"- {item}" for item in data["recommendations"])
    return "\n".join(lines) + "\n"

def implementation_md(data):
    impl = data["implementation"]
    return "\n".join([
        "# Materializer Implementation Intelligence",
        "",
        f"- Files inspected: `{impl['files']}`",
        f"- Supported extensions inferred: `{impl['supported_extensions']}`",
        f"- Selection/materialization functions: `{impl['selection_functions']}`",
        f"- Size limits: `{impl['size_limits']}`",
        "",
        "## Filters",
        "",
        *[f"- `{item}`" for item in impl["filters"]],
        "",
        "## Errors",
        "",
        *([f"- {item}" for item in impl["errors"]] or ["- None."]),
        "",
    ])

def authority_md(data):
    lines = ["# Materialization Authority Map", ""]
    for key, value in data["authority_map"].items():
        lines.append(f"- **{key}:** `{value}`")
    return "\n".join(lines) + "\n"

def dispositions_md(data):
    lines = [
        "# Materializer Candidate Dispositions",
        "",
        "| Path | Extension | State | Disposition | Reason |",
        "|---|---|---|---|---|",
    ]
    for item in data["dispositions"][:5000]:
        lines.append(
            f"| `{item['path']}` | `{item['extension']}` | `{item['state']}` | "
            f"**{item['disposition']}** | {item['reason']} |"
        )
    if len(data["dispositions"]) > 5000:
        lines.append(
            f"\n_Report truncated to 5,000 rows; JSON contains all {len(data['dispositions']):,} records._"
        )
    return "\n".join(lines) + "\n"
