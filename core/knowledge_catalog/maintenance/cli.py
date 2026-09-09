from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .controller import ACK, AssimilationController, Config, find_latest_plan


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="jarvis assimilate",
        description="Journaled relocation or identity-aware knowledge processing.")
    p.add_argument("root", type=Path)
    p.add_argument("--plan", type=Path)
    p.add_argument("--catalog", type=Path, default=Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"))
    p.add_argument("--state-root", type=Path, default=Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/maintenance"))
    p.add_argument("--apply", action="store_true")
    p.add_argument("--acknowledge")
    p.add_argument("--canary", type=int, metavar="N")
    p.add_argument("--batch-size", type=int, default=250)
    p.add_argument("--run-id")
    p.add_argument("--skip-as1", action="store_true")
    return p


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "process":
        from .processing import main as processing_main
        return processing_main(sys.argv[2:])
    args = parser().parse_args()
    plan = args.plan or find_latest_plan(Path.home() / "Downloads")
    cfg = Config(root=args.root.resolve(), plan=plan.resolve(), catalog=args.catalog.resolve(),
        state_root=args.state_root.resolve(), apply=args.apply, acknowledge=args.acknowledge,
        canary=args.canary, batch_size=args.batch_size, run_id=args.run_id,
        run_as1=not args.skip_as1)
    result = AssimilationController(cfg).run()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not args.apply:
        print("\nRead-only preflight complete. No corpus or database writes were made.")
        if result["decision"] == "READY":
            print(f"Canary gate: --apply --canary 25 --acknowledge {ACK}")
    return 0 if result["decision"] in {"READY", "COMPLETE", "PARTIAL"} else 2


if __name__ == "__main__":
    raise SystemExit(main())

