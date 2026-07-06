from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


DEFAULT_DB = "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
DEFAULT_FAISS_DIR = "/media/abdullah/JARVIS_RUNTIME_L/vector_db/faiss"


def run_step(name: str, args: list[str], keep_going: bool = False) -> bool:
    print()
    print("=" * 80)
    print(f"JARVIS MASS ASSIMILATION :: {name}")
    print("=" * 80)
    print(" ".join(args))
    print()

    start = time.perf_counter()

    proc = subprocess.run(
        args,
        text=True,
    )

    elapsed = time.perf_counter() - start

    print()
    print(f"[{name}] exit={proc.returncode} elapsed={elapsed:.2f}s")

    if proc.returncode != 0 and not keep_going:
        raise SystemExit(proc.returncode)

    return proc.returncode == 0


def py_module(module: str, *extra: str) -> list[str]:
    return [sys.executable, "-m", module, *extra]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run full JARVIS mass assimilation over a library directory."
    )

    parser.add_argument("root", help="Directory to assimilate")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--chunk-limit", type=int, default=100000)
    parser.add_argument("--embedding-limit", type=int, default=100000)
    parser.add_argument("--queue-limit", type=int, default=100000)
    parser.add_argument("--processing-cycles", type=int, default=5)
    parser.add_argument("--faiss-index-dir", default=DEFAULT_FAISS_DIR)
    parser.add_argument("--keep-going", action="store_true")

    args = parser.parse_args()

    root = str(Path(args.root).expanduser().resolve())
    db = str(Path(args.db).expanduser().resolve())

    print()
    print("=" * 80)
    print("JARVIS MASS ASSIMILATION")
    print("=" * 80)
    print(f"Root : {root}")
    print(f"DB   : {db}")
    print(f"Python: {sys.executable}")
    print("=" * 80)

    stages: list[tuple[str, list[str]]] = [
        (
            "Discovery",
            py_module(
                "knowledge_engine.discovery_cli",
                "--root", root,
                "--db", db,
            ),
        ),
        (
            "Knowledge Objects",
            py_module(
                "knowledge_engine.object_builder_cli",
                "--db", db,
                "--root-filter", root,
            ),
        ),
        (
            "Registry",
            py_module(
                "knowledge_engine.registry_cli",
                "--db", db,
                "--root-filter", root,
            ),
        ),
        (
            "Validation",
            py_module(
                "knowledge_engine.validation_cli",
                "--db", db,
            ),
        ),
        (
            "Queue",
            py_module(
                "knowledge_engine.queue_cli",
                "--db", db,
                "--root-filter", root,
                "--limit", str(args.queue_limit),
            ),
        ),
        (
            "Resource Inspection",
            py_module(
                "knowledge_engine.resource_inspection_cli",
                "--db", db,
                "--root-filter", root,
            ),
        ),
        (
            "Librarian",
            py_module(
                "knowledge_engine.librarian_cli",
                "--db", db,
                "--root-filter", root,
            ),
        ),
        (
            "Catalog Enrichment",
            py_module(
                "knowledge_engine.catalog_enrichment_cli",
                "--db", db,
                "--root-filter", root,
            ),
        ),
    ]

    for name, command in stages:
        run_step(name, command, keep_going=args.keep_going)

    for cycle in range(1, args.processing_cycles + 1):
        run_step(
            f"Processing Cycle {cycle}",
            py_module(
                "knowledge_engine.processing_cli",
                "--db", db,
            ),
            keep_going=args.keep_going,
        )

    run_step(
        "Chunking",
        py_module(
            "knowledge_engine.chunking_cli",
            "--db", db,
            "--limit", str(args.chunk_limit),
        ),
        keep_going=args.keep_going,
    )

    run_step(
        "Embeddings",
        py_module(
            "knowledge_engine.embeddings_cli",
            "--db", db,
            "--limit", str(args.embedding_limit),
        ),
        keep_going=args.keep_going,
    )

    run_step(
        "FAISS Rebuild",
        py_module(
            "knowledge_engine.hybrid_search_cli",
            "rebuild",
            "--db", db,
            "--index-dir", args.faiss_index_dir,
        ),
        keep_going=args.keep_going,
    )

    run_step(
        "Knowledge Graph",
        py_module(
            "knowledge_engine.knowledge_graph_cli",
            "build",
            "--db", db,
            "--root-filter", root,
        ),
        keep_going=args.keep_going,
    )

    run_step(
        "Knowledge Doctor",
        py_module(
            "knowledge_engine.doctor_cli",
            "--db", db,
            "--faiss-dir", args.faiss_index_dir,
        ),
        keep_going=args.keep_going,
    )

    print()
    print("=" * 80)
    print("JARVIS MASS ASSIMILATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
