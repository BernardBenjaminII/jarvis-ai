from __future__ import annotations
import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from dev.acceptance.campaign import CampaignDefinition
from dev.acceptance.question_library import smoke_questions
from dev.acceptance.runner import AcceptanceRunner
from dev.acceptance.runtime import create_live_runtime_adapter

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=Path("docs/audits/genesis_ix_a4_8"))
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()
    campaign = CampaignDefinition.create(
        campaign_id="GENESIS-IX-A4.8-SMOKE",
        name="Genesis IX-A4.8 Smoke Acceptance",
        version="pack2-v1",
        tests=smoke_questions(),
    )
    result = AcceptanceRunner(
        create_live_runtime_adapter(), args.output_root
    ).run(campaign, run_id=args.run_id)
    failed = [x for x in result["results"] if not x.passed]
    print("="*76)
    print("GENESIS IX-A4.8 EXECUTIVE ACCEPTANCE HARNESS")
    print("="*76)
    print("Run root :", result["run_root"])
    print("Executed :", len(result["results"]))
    print("Passed   :", len(result["results"])-len(failed))
    print("Failed   :", len(failed))
    print("="*76)
    return 0 if not failed else 1

if __name__ == "__main__":
    raise SystemExit(main())
