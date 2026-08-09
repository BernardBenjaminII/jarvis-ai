def n(value):
    return "—" if value is None else f"{int(value):,}"

def corpus_md(d):
    s=d["summary"]
    lines=["# Genesis IX-A5.7 Pack 1 — Corpus Intelligence","",
           f"**Status:** **{d['status']}**",
           f"**Classification:** **{d['classification']}**",
           f"**Generated:** {d['generated_at']}","",
           "## Summary","",
           f"- Candidates: **{s['candidate_count']}**",
           f"- Verified databases: **{s['verified_database_count']}**",
           f"- Invalid candidates: **{s['invalid_candidate_count']}**",
           f"- Corpora: **{s['table_count']}**",
           f"- Searchable corpora: **{s['searchable_corpus_count']}**",
           f"- Runtime corpora: **{s['runtime_corpus_count']}**",
           f"- FTS corpora: **{s['fts_corpus_count']}**","",
           "## Corpora","",
           "| Corpus | Rows | Roles | Pipeline | Searchable | Runtime | FTS |",
           "|---|---:|---|---|---|---|---|"]
    for x in d["corpora"]:
        lines.append(f"| `{x['corpus_id']}` | {n(x['row_count'])} | `{x['roles']}` | `{x['pipeline_stages']}` | {x['searchable']} | {x['runtime']} | {x['fts']} |")
    lines += ["","## Recommendations",""]+[f"- {x}" for x in d["recommendations"]]
    return "\n".join(lines)+"\n"

def databases_md(d):
    lines=["# Database Inventory","","| Database | Size | Tables | Views | Indexes | Triggers | FTS | Integrity |",
           "|---|---:|---:|---:|---:|---:|---|---|"]
    for x in d["databases"]:
        lines.append(f"| `{x['path']}` | {x['size_bytes']:,} | {len(x['tables'])} | {len(x['views'])} | {len(x['indexes'])} | {len(x['triggers'])} | `{x['fts_tables']}` | {x['integrity_check']} |")
    return "\n".join(lines)+"\n"

def tables_md(d):
    lines=["# Table Inventory","","| Database | Table | Rows | Columns | PK | FK | Virtual | FTS | Roles |",
           "|---|---|---:|---:|---|---:|---|---|---|"]
    for db in d["databases"]:
        for x in db["tables"]:
            lines.append(f"| {db['name']} | `{x['name']}` | {n(x['row_count'])} | {len(x['columns'])} | `{x['primary_key']}` | {len(x['foreign_keys'])} | {x['is_virtual']} | {x['is_fts']} | `{x['roles']}` |")
    return "\n".join(lines)+"\n"

def runtime_md(d):
    lines=["# Runtime Inventory","","| Corpus | Rows | Pipeline | FTS |",
           "|---|---:|---|---|"]
    for x in d["corpora"]:
        if x["runtime"] or x["fts"]:
            lines.append(f"| `{x['corpus_id']}` | {n(x['row_count'])} | `{x['pipeline_stages']}` | {x['fts']} |")
    return "\n".join(lines)+"\n"

def relationships_md(d):
    lines=["# Corpus Relationships","","| Source | Relation | Target | Confidence | Evidence |",
           "|---|---|---|---:|---|"]
    for x in d["relationships"]:
        lines.append(f"| `{x['source']}` | `{x['relation']}` | `{x['target']}` | {x['confidence']:.2f} | `{x['evidence']}` |")
    return "\n".join(lines)+"\n"

def candidates_md(d):
    lines=["# Database Candidate Validation","","| Candidate | Header | SQLite | Classification | Error |",
           "|---|---|---|---|---|"]
    for x in d["database_candidates"]:
        lines.append(f"| `{x['path']}` | {x['header_valid']} | {x['sqlite_valid']} | `{x['classification']}` | {x.get('error') or ''} |")
    return "\n".join(lines)+"\n"
