from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

def locate_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in (current.parent, *current.parents):
        if all((candidate / name).is_dir() for name in ("core", "dev", "docs")):
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            return candidate
    raise RuntimeError("Unable to locate JARVIS project root.")

ROOT = locate_root()

from core.certification.runtime import CertificationRuntime
from core.retrieval import build_inventory

def render_runtime(data):
    lines = [
        "# Genesis IX-A4.2A — Retrieval Runtime Inventory", "",
        f"**Generated:** {data['generated_at']}",
        f"**Repository:** `{data['repository_root']}`",
        f"**Catalog:** `{data['catalog_database']}`", "",
        "## Summary", "",
    ]
    for k, v in data["summary"].items():
        lines.append(f"- **{k}:** {v}")
    lines += ["", "## Runtime bindings", "",
              "| Owner | Attribute | Module | Type | Callable |",
              "|---|---|---|---|---|"]
    for item in data["runtime_bindings"]:
        lines.append(
            f"| `{item['owner']}` | `{item['attribute']}` | `{item['module']}` | "
            f"`{item['type_name']}` | `{item['callable_name']}` |"
        )
    return "\n".join(lines) + "\n"

def render_capabilities(data):
    lines = [
        "# Genesis IX-A4.2A — Capability Matrix", "",
        "| Capability | Present | Used | Certified | Evidence |",
        "|---|---|---|---|---|",
    ]
    for item in data["capabilities"]:
        lines.append(
            f"| {item['capability']} | {item['present']} | {item['used']} | "
            f"{item['certified']} | {'<br>'.join(item['evidence'])} |"
        )
    return "\n".join(lines) + "\n"

def render_graph(data):
    nodes = {}
    for edge in data["graph_edges"]:
        for label in (edge["source"], edge["target"]):
            nodes.setdefault(label, f"N{len(nodes)+1}")
    lines = ["# Genesis IX-A4.2A — Retrieval Graph", "", "```mermaid", "flowchart TD"]
    for label, node in nodes.items():
        lines.append(f'    {node}["{label.replace(chr(34), chr(39))}"]')
    for edge in data["graph_edges"]:
        lines.append(
            f"    {nodes[edge['source']]} -->|{edge['relation']}| {nodes[edge['target']]}"
        )
    lines += ["```", "", "| Source | Target | Relation | Evidence |", "|---|---|---|---|"]
    for edge in data["graph_edges"]:
        lines.append(
            f"| `{edge['source']}` | `{edge['target']}` | "
            f"{edge['relation']} | {edge['evidence']} |"
        )
    return "\n".join(lines) + "\n"

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, default=Path("docs/audits/retrieval_inventory"))
    args = parser.parse_args()

    runtime = CertificationRuntime(start=args.root).bootstrap()
    bootstrap = runtime.certify()
    catalog = Path(bootstrap.catalog_database) if bootstrap.catalog_database else None
    data = build_inventory(Path(bootstrap.repository_root), catalog)

    output = args.output_dir
    if not output.is_absolute():
        output = Path(bootstrap.repository_root) / output
    output.mkdir(parents=True, exist_ok=True)

    (output / "pipeline_inventory.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "retrieval_graph.json").write_text(
        json.dumps({"schema_version": data["schema_version"], "graph_edges": data["graph_edges"]},
                   indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "runtime_inventory.md").write_text(render_runtime(data), encoding="utf-8")
    (output / "capability_matrix.md").write_text(render_capabilities(data), encoding="utf-8")
    (output / "retrieval_graph.md").write_text(render_graph(data), encoding="utf-8")

    failures = []
    if bootstrap.status != "EXCELLENT":
        failures.append("Certification runtime bootstrap failed.")
    if not data["components"]:
        failures.append("No retrieval components found.")
    if not data["runtime_bindings"]:
        failures.append("No runtime bindings found.")
    if not data["graph_edges"]:
        failures.append("No retrieval graph generated.")
    if not data["tables"]:
        failures.append("No retrieval-related tables classified.")

    status = "EXCELLENT" if not failures else "FAILED"
    print("=" * 76)
    print("GENESIS IX-A4.2A — RETRIEVAL PIPELINE INVENTORY")
    print("=" * 76)
    print("Components       :", len(data["components"]))
    print("Runtime bindings :", len(data["runtime_bindings"]))
    print("Tables           :", len(data["tables"]))
    print("Graph edges      :", len(data["graph_edges"]))
    print("Capabilities     :", len(data["capabilities"]))
    print("Overall status   :", status)
    for failure in failures:
        print("[FAIL]", failure)
    print("Output           :", output)
    print("=" * 76)
    return 0 if status == "EXCELLENT" else 1

if __name__ == "__main__":
    raise SystemExit(main())
