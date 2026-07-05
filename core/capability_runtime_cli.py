from __future__ import annotations

import argparse
from pathlib import Path

from core.capabilities import (
    CapabilityContext,
    CapabilityLoader,
    CapabilityRegistry,
    CapabilityRunner,
)
from core.capabilities.report import print_capability_report
from knowledge_engine.storage.database import KnowledgeDatabase


DEFAULT_CAPABILITY_PACKAGES = [
    "knowledge_engine.capabilities",
]


def cmd_list(args) -> None:
    registry = CapabilityRegistry()
    loader = CapabilityLoader(args.package)
    results = loader.load(registry)

    print()
    print("Capability packages:")
    for result in results:
        status = "OK" if result.loaded else "FAIL"
        print(f"{status}: {result.module}")
        if result.error:
            print(f"  {result.error}")

    print()
    print("Capabilities:")
    for capability in registry.resolve():
        print(f"- {capability.name}")
        print(f"  description: {capability.description}")
        print(f"  requires   : {sorted(capability.requires)}")
        print(f"  provides   : {sorted(capability.provides)}")
        print(f"  order      : {capability.order}")


def cmd_run(args) -> None:
    registry = CapabilityRegistry()
    loader = CapabilityLoader(args.package)
    loader.load(registry)

    db = KnowledgeDatabase(args.db)

    context = CapabilityContext(
        root=Path(args.root).expanduser().resolve(),
        database=db,
        runtime={
            "faiss_index_dir": args.faiss_index_dir,
        },
    )

    results = CapabilityRunner(registry).run(context)
    print_capability_report(results)


def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS Capability Runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    common_packages = argparse.ArgumentParser(add_help=False)
    common_packages.add_argument(
        "--package",
        action="append",
        default=DEFAULT_CAPABILITY_PACKAGES,
        help="Capability package root to load",
    )

    list_cmd = sub.add_parser("list", parents=[common_packages])
    list_cmd.set_defaults(func=cmd_list)

    run_cmd = sub.add_parser("run", parents=[common_packages])
    run_cmd.add_argument("root", nargs="?", default=".")
    run_cmd.add_argument("--db", required=True)
    run_cmd.add_argument(
        "--faiss-index-dir",
        default="/media/abdullah/JARVIS_RUNTIME_L/vector_db/faiss",
    )
    run_cmd.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
