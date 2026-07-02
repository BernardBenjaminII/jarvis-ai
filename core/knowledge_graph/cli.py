from __future__ import annotations

import argparse

from core.knowledge_graph.gap_analysis import analyze_gaps, write_reports
from core.knowledge_graph.ontology import load_ontology


def cmd_summary() -> None:
    ontology = load_ontology()

    print("=" * 60)
    print("JARVIS KNOWLEDGE GRAPH")
    print("=" * 60)
    print()
    print("Domains:")
    print(list(ontology.domains["domains"].keys()))
    print()
    print("Campaigns:")
    print(list(ontology.campaigns["campaigns"].keys()))
    print()
    print("Concepts:")
    print(len(ontology.concepts["concepts"]))
    print()
    print("Prerequisite Rules:")
    print(len(ontology.prerequisites["prerequisites"]))


def cmd_gaps() -> None:
    rows = analyze_gaps()
    json_path, txt_path = write_reports(rows)

    summary = {
        "missing": sum(1 for r in rows if r.status == "missing"),
        "weak": sum(1 for r in rows if r.status == "weak"),
        "developing": sum(1 for r in rows if r.status == "developing"),
        "strong": sum(1 for r in rows if r.status == "strong"),
    }

    print("=" * 60)
    print("JARVIS GAP ANALYSIS")
    print("=" * 60)
    print()
    print(f"Subjects analyzed: {len(rows)}")
    print(f"Missing:           {summary['missing']}")
    print(f"Weak:              {summary['weak']}")
    print(f"Developing:        {summary['developing']}")
    print(f"Strong:            {summary['strong']}")
    print()
    print("Top gaps:")
    for row in rows[:20]:
        print(
            f"{row.status.upper():<10} "
            f"{row.domain}/{row.discipline}/{row.subject} "
            f"files={row.file_count}"
        )

    print()
    print(f"[OK] JSON report: {json_path}")
    print(f"[OK] Text report: {txt_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS Knowledge Graph CLI")
    parser.add_argument(
        "command",
        nargs="?",
        default="summary",
        choices=["summary", "gaps"],
    )

    args = parser.parse_args()

    if args.command == "summary":
        cmd_summary()
    elif args.command == "gaps":
        cmd_gaps()


if __name__ == "__main__":
    main()
