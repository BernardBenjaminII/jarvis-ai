from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def locate_root():
    current = Path(__file__).resolve()
    for candidate in (current.parent, *current.parents):
        if all((candidate/name).is_dir() for name in ("core","dev","docs")):
            if str(candidate) not in sys.path: sys.path.insert(0,str(candidate))
            return candidate
    raise RuntimeError("Unable to locate JARVIS root.")

ROOT = locate_root()

from core.certification.runtime import CertificationRuntime
from core.retrieval.gap_trace import KnowledgeGapPropagationTracer

def summary(data):
    v=data["verdict"]
    lines=["# Genesis IX-A4.3B — Knowledge Gap Propagation Trace","",
           f"**Classification:** **{v['classification']}**",
           f"**Blocking:** **{v['blocking']}**","",
           "## Verdict","",v["reason"],"",
           f"- First gap stage: `{v.get('first_gap_stage')}`",
           f"- Loss stage: `{v.get('loss_stage')}`","",
           "| # | Stage | Gap | Count | Status | Function | Source |",
           "|---:|---|---|---:|---|---|---|"]
    for x in data["stages"]:
        lines.append(f"| {x['ordinal']} | `{x['stage']}` | {x['gap_present']} | "
                     f"{x['gap_count']} | `{x['status']}` | `{x['function']}` | "
                     f"`{x['file']}:{x['line']}` |")
    return "\n".join(lines)+"\n"

def creation(data):
    first=next((x for x in data["stages"] if x["gap_present"]),None)
    if not first: return "# Knowledge Gap Creation Trace\n\nNo KnowledgeGap object was observed.\n"
    return ("# Knowledge Gap Creation Trace\n\n"
            f"First appears at `{first['stage']}`.\n\n"
            f"- Function: `{first['function']}`\n- Source: `{first['file']}:{first['line']}`\n"
            f"- Count: `{first['gap_count']}`\n\n```json\n"
            f"{json.dumps(first['serialized'],indent=2,sort_keys=True)}\n```\n")

def propagation(data):
    lines=["# Knowledge Gap Propagation Trace",""]
    for x in data["stages"]:
        lines += [f"## {x['ordinal']}. `{x['stage']}`","",
                  f"- Gap present: **{x['gap_present']}**",
                  f"- Gap count: **{x['gap_count']}**",
                  f"- Status: `{x['status']}`",
                  f"- Function: `{x['function']}`",
                  f"- Source: `{x['file']}:{x['line']}`","",
                  "```json",json.dumps(x["serialized"],indent=2,sort_keys=True),"```",""]
    return "\n".join(lines)+"\n"

def graph(data):
    lines=["# Knowledge Gap Object Graph","","```mermaid","flowchart TD"]
    for i,x in enumerate(data["stages"],1):
        state="GAP" if x["gap_present"] else "NO GAP"
        label=f"{x['stage']}\\n{state}".replace('"',"'")
        lines.append(f'    N{i}["{label}"]')
    for i in range(1,len(data["stages"])): lines.append(f"    N{i} --> N{i+1}")
    lines += ["```","",f"**Verdict:** {data['verdict']['classification']}","",data["verdict"]["reason"]]
    return "\n".join(lines)+"\n"

def mutation(data):
    lines=["# Knowledge Gap Mutation Trace","",
           "| Transition | Before | After | Mutation |","|---|---|---|---|"]
    for a,b in zip(data["stages"],data["stages"][1:]):
        mutation="preserved" if a["gap_present"]==b["gap_present"] else "lost" if a["gap_present"] else "created"
        lines.append(f"| `{a['stage']}` → `{b['stage']}` | {a['gap_present']} | {b['gap_present']} | **{mutation}** |")
    return "\n".join(lines)+"\n"

def prompt_trace(data):
    prompt=str(data["capture"].get("prompt") or "")
    return ("# Knowledge Gap Prompt Trace\n\n"
            f"- Prompt length: **{len(prompt)}**\n"
            f"- Contains gap marker: **{'Knowledge gaps:' in prompt}**\n"
            f"- Contains no-evidence marker: **{'No catalog evidence was retrieved.' in prompt}**\n"
            f"- Contains acquisition guidance: **{'Queue targeted acquisition' in prompt or 'Acquire authoritative sources' in prompt}**\n\n"
            f"```text\n{prompt}\n```\n")

def decision(data):
    v=data["verdict"]
    return ("# Knowledge Gap Decision Tree\n\n```text\n"
            "Unknown query\n  ↓\nGroundingResult\n  ↓\nKnowledgeGap created?\n"
            f"  └── {v.get('first_gap_stage') is not None}\n"
            "  ↓\nKnowledgeGap lost?\n"
            f"  └── {v.get('loss_stage') is not None}\n"
            "```\n\n"
            f"**Classification:** `{v['classification']}`\n\n{v['reason']}\n")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--output-dir",type=Path,default=Path("docs/audits/genesis_ix_a4_3b"))
    args=parser.parse_args()

    runtime=CertificationRuntime(start=args.root).bootstrap()
    bootstrap=runtime.certify()
    catalog=Path(bootstrap.catalog_database) if bootstrap.catalog_database else None
    data=KnowledgeGapPropagationTracer(Path(bootstrap.repository_root),catalog).run()

    output=args.output_dir if args.output_dir.is_absolute() else Path(bootstrap.repository_root)/args.output_dir
    output.mkdir(parents=True,exist_ok=True)
    files={
        "trace_summary.json":json.dumps(data,indent=2,sort_keys=True)+"\n",
        "runtime_objects.json":json.dumps({"stages":data["stages"],"source_locations":data["source_locations"]},indent=2,sort_keys=True)+"\n",
        "trace_summary.md":summary(data),
        "gap_creation_trace.md":creation(data),
        "gap_propagation_trace.md":propagation(data),
        "knowledge_gap_graph.md":graph(data),
        "mutation_trace.md":mutation(data),
        "prompt_trace.md":prompt_trace(data),
        "decision_tree.md":decision(data),
    }
    for name,content in files.items(): (output/name).write_text(content,encoding="utf-8")

    v=data["verdict"]
    print("="*76)
    print("GENESIS IX-A4.3B — KNOWLEDGE GAP PROPAGATION TRACE")
    print("="*76)
    print("Stages captured :",len(data["stages"]))
    print("Classification  :",v["classification"])
    print("First gap stage :",v.get("first_gap_stage"))
    print("Loss stage      :",v.get("loss_stage"))
    print("Blocking        :",v["blocking"])
    print("Output          :",output)
    print("="*76)
    return 0

if __name__=="__main__": raise SystemExit(main())
