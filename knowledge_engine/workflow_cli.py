from __future__ import annotations

import argparse
from pathlib import Path

from knowledge_engine.storage.database import KnowledgeDatabase
from knowledge_engine.workflow.report import print_workflow_report
from knowledge_engine.workflow.runner import WorkflowRunner
from knowledge_engine.workflow.stage import WorkflowContext
from knowledge_engine.workflows.registry import (
    available,
    build,
)


def run_workflow(args):

    db = KnowledgeDatabase(args.db)

    context = WorkflowContext(
        root=Path(args.root).expanduser().resolve(),
        database=db,
    )

    registry = build(args.workflow)

    results = WorkflowRunner(registry).run(context)

    print_workflow_report(results)


def main():

    parser = argparse.ArgumentParser(
        description="JARVIS Workflow Engine"
    )

    parser.add_argument(
        "workflow",
        choices=available(),
        help="Workflow name",
    )

    parser.add_argument(
        "root",
        help="Root directory",
    )

    parser.add_argument(
        "--db",
        required=True,
    )

    args = parser.parse_args()

    run_workflow(args)


if __name__ == "__main__":
    main()
