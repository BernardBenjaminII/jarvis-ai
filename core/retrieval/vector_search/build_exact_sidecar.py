from __future__ import annotations

import argparse
import json
from pathlib import Path

from .exact_sidecar import ExactVectorSidecarBuilder


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the JARVIS R6.1 exact vector sidecar."
    )

    parser.add_argument(
        "--semantic-db",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--provider",
        default="ollama",
    )

    parser.add_argument(
        "--model",
        default="mxbai-embed-large",
    )

    parser.add_argument(
        "--dimensions",
        type=int,
        default=1024,
    )

    parser.add_argument(
        "--block-size",
        type=int,
        default=4096,
    )

    args = parser.parse_args()

    builder = ExactVectorSidecarBuilder(
        semantic_db=args.semantic_db,
        output_dir=args.output_dir,
        provider=args.provider,
        model=args.model,
        expected_dimensions=args.dimensions,
        block_size=args.block_size,
    )

    result = builder.build()

    print(json.dumps(result, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
