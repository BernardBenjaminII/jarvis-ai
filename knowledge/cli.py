from pathlib import Path
import argparse

from knowledge.pipeline import run_inventory

DEFAULT_KNOWLEDGE_ROOT = Path(
    "/media/abdullah/JARVISDATA/Knowledge"
)

DEFAULT_CATALOG_PATH = Path(
    "/media/abdullah/JARVISDATA/Knowledge/.jarvis/catalog.sqlite"
)


def main() -> None:

    parser = argparse.ArgumentParser(
        description="JARVIS Knowledge Engine"
    )

    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_KNOWLEDGE_ROOT,
        help="Knowledge library root",
    )

    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG_PATH,
        help="Knowledge SQLite database",
    )

    args = parser.parse_args()

    summary = run_inventory(
        args.root,
        args.catalog,
    )

    print("=" * 60)
    print("JARVIS KNOWLEDGE ENGINE")
    print("=" * 60)

    print()
    print("Discovery")
    print("-" * 60)

    print(f"Scanned Files     : {summary['scanned']}")
    print(f"Catalog Entries   : {summary['total']}")
    print(f"Discovery Errors  : {len(summary['errors'])}")

    print()
    print("Inspection")
    print("-" * 60)

    print(f"Documents         : {summary['inspected']}")
    print(f"Unsupported       : {summary['unsupported']}")
    print(f"Inspection Errors : {len(summary['inspection_errors'])}")

    print()
    print("Structure")
    print("-" * 60)

    print(f"Structured Docs   : {summary['structured']}")
    print(f"Structure Errors  : {len(summary['structure_errors'])}")

    if summary["structure_summary"]:

        print()
        print("Structure Sources")
        print("-" * 60)

        for source, count in summary["structure_summary"]:
            print(f"{source:<24}{count}")

    print()
    print("By Extension")
    print("-" * 60)

    for ext, count in summary["by_extension"]:
        print(f"{ext:<12}{count}")

    print()
    print("By Category")
    print("-" * 60)

    for category, count in summary["by_category"]:
        print(f"{category:<24}{count}")

    if summary["errors"]:

        print()
        print("Discovery Errors")
        print("-" * 60)

        for path, error in summary["errors"]:
            print(path)
            print(f"    {error}")

    if summary["inspection_errors"]:

        print()
        print("Inspection Errors")
        print("-" * 60)

        for path, error in summary["inspection_errors"]:
            print(path)
            print(f"    {error}")

    if summary["structure_errors"]:

        print()
        print("Structure Errors")
        print("-" * 60)

        for path, error in summary["structure_errors"]:
            print(path)
            print(f"    {error}")

    print()
    print("=" * 60)
    print("Knowledge Engine Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
