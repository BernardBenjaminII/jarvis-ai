def fmt(value):
    if value is None: return "—"
    try: return f"{float(value):.3f}"
    except (TypeError,ValueError): return str(value)

def render_markdown(data):
    s=data["summary"]
    lines=[
        "# Genesis IX-A5 Pack 3R — Runtime Qualification Forensics","",
        f"**Status:** **{data['status']}**",
        f"**Classification:** **{data['classification']}**","",
        "## Summary","",
        f"- Known probes: **{s['known_probe_count']}**",
        f"- Raw recall: **{s['known_raw_recall']:.1%}**",
        f"- Qualified recall: **{s['known_qualified_recall']:.1%}**",
        f"- Top failure: **{s.get('top_failure') or 'None'}**",
        f"- Probe errors: **{s['probe_error_count']}**","",
        "## Rejection Reasons","",
    ]
    reasons=s.get("rejection_reasons") or {}
    lines.extend([f"- `{k}`: **{v}**" for k,v in reasons.items()] or ["- None recorded."])
    lines += ["","## Probe Matrix","",
              "| Probe | Query | Expected | Raw | Qualified | Dominant Failure | Error |",
              "|---|---|---|---:|---:|---|---|"]
    for p in data["probes"]:
        err=p["raw_error"] or p["qualified_error"] or ""
        lines.append(f"| `{p['probe_id']}` | {p['query']} | {p['expectation']} | {p['raw_count']} | {p['qualified_count']} | {p.get('dominant_failure') or 'None'} | {err} |")
    lines += ["","## Candidate Forensics",""]
    for p in data["probes"]:
        lines += [
            f"### {p['probe_id']} — {p['query']}","",
            "| Rank | Title | Decision | Retrieval | Lexical | Phrase | Subject | Confidence | Final | Threshold | Margin | Reason |",
            "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
        if not p["candidates"]:
            lines.append("| — | No candidate diagnostics | — | — | — | — | — | — | — | — | — | — |")
        for i in p["candidates"]:
            lines.append(
                f"| {i['raw_rank']} | {i['title']} | {i['decision']} | {fmt(i['retrieval_score'])} | "
                f"{fmt(i['lexical_score'])} | {fmt(i['phrase_score'])} | {fmt(i['subject_score'])} | "
                f"{fmt(i['confidence_score'])} | {fmt(i['final_score'])} | {fmt(i['threshold'])} | "
                f"{fmt(i['margin'])} | {i.get('rejection_reason') or '—'} |"
            )
        lines += ["","Recommendations:",""]
        lines.extend(f"- {x}" for x in p["recommendations"])
        lines.append("")
    lines += ["## Global Recommendations",""]
    lines.extend(f"- {x}" for x in data["recommendations"])
    return "\n".join(lines)+"\n"
