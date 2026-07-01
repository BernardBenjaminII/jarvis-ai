from pathlib import Path
import argparse

from knowledge_engine.pipeline import run_inventory


DEFAULT_KNOWLEDGE_ROOT = Path(
    "/media/abdullah/JARVISDATA/Knowledge"
)

DEFAULT_CATALOG_PATH = Path(
    "/media/abdullah/JARVISDATA/Knowledge/.jarvis/catalog.sqlite"
)


def section(title: str) -> None:
    print()
    print(title)
    print("-" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="JARVIS Knowledge Engine"
    )

    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_KNOWLEDGE_ROOT,
        help="Knowledge Warehouse root",
    )

    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG_PATH,
        help="SQLite catalog database",
    )

    args = parser.parse_args()

    summary = run_inventory(args.root, args.catalog)

    print("=" * 60)
    print("JARVIS KNOWLEDGE ENGINE")
    print("=" * 60)

    section("Stage 1 : Discovery")
    print(f"Scanned Files     : {summary['scanned']}")
    print(f"Catalog Entries   : {summary['total']}")
    print(f"Discovery Errors  : {len(summary['errors'])}")

    section("Stage 2 : Inspection")
    print(f"Documents         : {summary['inspected']}")
    print(f"Unsupported       : {summary['unsupported']}")
    print(f"Inspection Errors : {len(summary['inspection_errors'])}")

    section("Stage 3 : Structure Extraction")
    print(f"Structured Docs   : {summary['structured']}")
    print(f"Structure Errors  : {len(summary['structure_errors'])}")

    if summary["structure_summary"]:
        print()
        print("Structure Sources")
        for source, count in summary["structure_summary"]:
            print(f"    {source:<20} {count}")

    section("Stage 4 : Knowledge Index")
    print(f"Indexed Records   : {summary['indexed']}")
    print(f"Index Total       : {summary['index_total']}")
    print(f"With TOC          : {summary['index_with_toc']}")
    print(f"Index Errors      : {len(summary['index_errors'])}")

    section("Warehouse Statistics")

    print("By Extension")
    for ext, count in summary["by_extension"]:
        print(f"    {ext:<12} {count}")

    print()
    print("By Category")
    for category, count in summary["by_category"]:
        print(f"    {category:<20} {count}")

    error_sections = [
        ("Discovery Errors", "errors"),
        ("Inspection Errors", "inspection_errors"),
        ("Structure Errors", "structure_errors"),
        ("Index Errors", "index_errors"),
    ]

    for title, key in error_sections:
        if summary.get(key):
            section(title)
            for path, error in summary[key]:
                print(path)
                print(f"    {error}")

    print()
    print("=" * 60)
    print("Knowledge Engine Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
