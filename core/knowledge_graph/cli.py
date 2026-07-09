from __future__ import annotations

import argparse

from core.knowledge_graph.gap_analysis import analyze_gaps, write_reports
from core.knowledge_graph.ontology import load_ontology


def print_section(title, rows):

    print()
    print("=" * 60)
    print(title)
    print("=" * 60)

    if not rows:
        print("None")
        return

    for r in rows:
        print(
            f"{r.status:<11}"
            f"{r.domain}/{r.discipline}/{r.subject}"
            f"  ({r.file_count} files)"
        )


def cmd_summary():

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


def cmd_gaps():

    rows = analyze_gaps()

    json_path, txt_path = write_reports(rows)

    strong = sorted(
        [r for r in rows if r.status == "strong"],
        key=lambda r: r.file_count,
        reverse=True,
    )

    developing = sorted(
        [r for r in rows if r.status == "developing"],
        key=lambda r: r.file_count,
        reverse=True,
    )

    weak = sorted(
        [r for r in rows if r.status == "weak"],
        key=lambda r: r.file_count,
        reverse=True,
    )

    missing = sorted(
        [r for r in rows if r.status == "missing"],
        key=lambda r: (
            r.domain,
            r.discipline,
            r.subject,
        ),
    )

    print("=" * 60)
    print("JARVIS GAP ANALYSIS")
    print("=" * 60)

    print()

    print(f"Subjects analyzed : {len(rows)}")
    print(f"Strong            : {len(strong)}")
    print(f"Developing        : {len(developing)}")
    print(f"Weak              : {len(weak)}")
    print(f"Missing           : {len(missing)}")

    print_section("STRONG SUBJECTS", strong)

    print_section("DEVELOPING SUBJECTS", developing)

    print_section("WEAK SUBJECTS", weak)

    print_section("MISSING SUBJECTS", missing)

    print()

    print(f"[OK] JSON report : {json_path}")
    print(f"[OK] Text report : {txt_path}")


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "command",
        nargs="?",
        default="summary",
        choices=[
            "summary",
            "gaps",
        ],
    )

    args = parser.parse_args()

    if args.command == "summary":
        cmd_summary()

    else:
        cmd_gaps()


if __name__ == "__main__":
    main()
