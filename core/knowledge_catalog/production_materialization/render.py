def duration(seconds):
    if seconds is None: return "—"
    seconds=int(seconds); d,seconds=divmod(seconds,86400); h,seconds=divmod(seconds,3600); m,s=divmod(seconds,60)
    return " ".join(x for x in (f"{d}d" if d else "",f"{h}h" if h else "",f"{m}m" if m else "",f"{s}s") if x)

def render(data):
    lines=["# Genesis X-A1 — Production Materialization Engine","",
      f"**Run:** `{data['run_id']}`",f"**Status:** **{data['status']}**",
      f"**Classification:** **{data['classification']}**",f"**Dry run:** **{data['dry_run']}**","",
      "## Throughput","",f"- Workers: **{data['workers']}**",
      f"- Selected: **{data['candidates_selected']:,}**",f"- Completed: **{data['candidates_completed']:,}**",
      f"- Documents/minute: **{data['documents_per_minute']:.2f}**",
      f"- Chunks/minute: **{data['chunks_per_minute']:.2f}**",
      f"- Estimated remaining: **{duration(data['estimated_remaining_seconds'])}**","",
      "## Runtime Counts","","| Store | Before | After | Delta |","|---|---:|---:|---:|"]
    for n in ("runtime_documents","runtime_chunks","runtime_chunks_fts"):
        b=data["pre_counts"][n]; a=data["post_counts"][n]
        lines.append(f"| `{n}` | {b:,} | {a:,} | {a-b:,} |")
    lines += ["","## Stage Counts",""]+[f"- `{k}`: **{v:,}**" for k,v in sorted(data["stage_counts"].items())]
    lines += ["","## Results","","| Candidate | Stage | Document Δ | Chunk Δ | FTS Δ | Extract s | Write s | Detail |",
              "|---|---|---:|---:|---:|---:|---:|---|"]
    for r in data["results"]:
        lines.append(f"| `{r['candidate_id']}` | `{r['stage']}` | {r['document_delta']} | {r['chunk_delta']} | "
                     f"{r['fts_delta']} | {r['extraction_seconds']:.2f} | {r['write_seconds']:.2f} | {r['detail']} |")
    return "\n".join(lines)+"\n"
