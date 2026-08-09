from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from dev.runtime import bootstrap_runtime


RUNTIME = bootstrap_runtime(Path(__file__))
PROJECT_ROOT = RUNTIME.project_root


from core.knowledge_catalog.production_materialization.checkpoint import (
    CheckpointStore,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--checkpoint-db",
        type=Path,
        default=(
            PROJECT_ROOT
            / ".runtime/materialization/"
            "genesis_x_a1_engine.sqlite"
        ),
    )
    args = parser.parse_args()

    store = CheckpointStore(
        args.checkpoint_db
    )
    incomplete = (
        store.recover_incomplete_states()
    )
    locks = (
        store.recover_transient_lock_failures()
    )

    print(
        json.dumps(
            {
                "checkpoint_db": str(
                    args.checkpoint_db.resolve()
                ),
                "recovered_incomplete": incomplete,
                "recovered_transient_locks": locks,
                "stage_counts": store.counts(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
