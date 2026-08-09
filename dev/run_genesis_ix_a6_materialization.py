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


from core.knowledge_catalog.config import (
    DEFAULT_CATALOG_DB,
    DEFAULT_KNOWLEDGE_ROOT,
)
from core.knowledge_catalog.materialization_campaign import (
    CampaignConfig,
    FullCorpusMaterializationCampaign,
)
from core.knowledge_catalog.materialization_campaign.render import (
    render_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run or inspect the Genesis IX-A6 full corpus "
            "materialization campaign."
        )
    )
    parser.add_argument(
        "command",
        choices=(
            "prepare",
            "dry-run",
            "execute",
            "status",
        ),
    )
    parser.add_argument(
        "--runtime-catalog",
        type=Path,
        default=DEFAULT_CATALOG_DB,
    )
    parser.add_argument(
        "--inventory-catalog",
        type=Path,
        default=(
            Path(DEFAULT_KNOWLEDGE_ROOT)
            / ".jarvis/catalog.sqlite"
        ),
    )
    parser.add_argument(
        "--knowledge-root",
        type=Path,
        default=DEFAULT_KNOWLEDGE_ROOT,
    )
    parser.add_argument(
        "--checkpoint-db",
        type=Path,
        default=(
            PROJECT_ROOT
            / ".runtime/materialization/"
            "genesis_ix_a6_campaign.sqlite"
        ),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=(
            PROJECT_ROOT
            / "docs/audits/genesis_ix_a6"
        ),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
    )
    parser.add_argument(
        "--max-batches",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--max-documents",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
    )
    parser.add_argument(
        "--retry-failures",
        action="store_true",
    )
    return parser


def configuration(args, *, dry_run: bool) -> CampaignConfig:
    return CampaignConfig(
        project_root=PROJECT_ROOT,
        runtime_catalog=args.runtime_catalog,
        knowledge_root=args.knowledge_root,
        checkpoint_db=args.checkpoint_db,
        report_dir=args.report_dir,
        batch_size=max(1, args.batch_size),
        max_batches=args.max_batches,
        max_documents=args.max_documents,
        stop_on_error=args.stop_on_error,
        dry_run=dry_run,
        retry_failures=args.retry_failures,
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "status":
        from core.knowledge_catalog.materialization_campaign.checkpoint import (
            CheckpointStore,
        )

        store = CheckpointStore(args.checkpoint_db)
        payload = {
            "candidate_count": store.candidate_count(),
            "disposition_counts": store.disposition_counts(),
            "checkpoint_db": str(
                args.checkpoint_db.resolve()
            ),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    dry_run = args.command != "execute"
    campaign = FullCorpusMaterializationCampaign(
        configuration(args, dry_run=dry_run)
    )

    if args.command == "prepare":
        payload = campaign.prepare(
            inventory_catalog=args.inventory_catalog,
        )
        print(
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if campaign.store.candidate_count() == 0:
        campaign.prepare(
            inventory_catalog=args.inventory_catalog,
        )

    report = campaign.run()
    data = report.to_dict()

    args.report_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    suffix = (
        "dry_run"
        if report.dry_run
        else "execution"
    )
    json_path = (
        args.report_dir
        / f"{suffix}_report.json"
    )
    markdown_path = (
        args.report_dir
        / f"{suffix}_report.md"
    )
    json_path.write_text(
        json.dumps(
            data,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_report(data),
        encoding="utf-8",
    )

    print("=" * 76)
    print("GENESIS IX-A6 — FULL CORPUS MATERIALIZATION CAMPAIGN")
    print("=" * 76)
    print("Campaign       :", data["campaign_id"])
    print("Classification :", data["classification"])
    print("Dry run        :", data["dry_run"])
    print("Batches        :", data["batches_completed"])
    print("Examined       :", data["candidates_examined"])
    print("Before         :", data["pre_counts"])
    print("After          :", data["post_counts"])
    print("Checkpoint     :", data["checkpoint_db"])
    print("Report         :", markdown_path)
    print("=" * 76)

    return (
        0
        if data["status"] == "EXCELLENT"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
