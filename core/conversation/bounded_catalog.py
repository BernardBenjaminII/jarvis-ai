"""Cancelable subprocess boundary for command-advice catalog retrieval."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import time

CATALOG_BUDGET_SECONDS = 8


def bounded_command_grounding(service, context, *, budget=CATALOG_BUDGET_SECONDS):
    from .grounding import GroundingResult, ObjectiveGrounding, GroundingEvidence, KnowledgeGap
    started = time.monotonic()
    def report(status, **extra):
        return {"status": status, "budget_seconds": budget,
                "elapsed_seconds": round(time.monotonic()-started, 3), **extra}
    if service is None:
        return None, report("unavailable")
    worker = Path(__file__).with_name("command_catalog_worker.py")
    try:
        with tempfile.TemporaryDirectory(prefix="jarvis-command-catalog-") as folder:
            output = Path(folder)/"result.json"
            # A separate process can be killed and reaped on timeout. A timed-out
            # thread would keep running the same blocking retrieval in the server.
            result = subprocess.run(
                [sys.executable, str(worker), str(service.database_path),
                 str(output), str(service.limit_per_objective)],
                input=json.dumps(context.to_dict()), text=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=budget, shell=False,
            )
            if result.returncode != 0 or not output.is_file():
                return None, report("unavailable", reason="Catalog worker failed")
            if output.stat().st_size > 2_000_000:
                return None, report("unavailable", reason="Catalog result exceeded size limit")
            data = json.loads(output.read_text())
        objectives = []
        for item in data["objectives"]:
            evidence = tuple(GroundingEvidence(**entry) for entry in item["evidence"])
            gap = KnowledgeGap(**item["gap"]) if item.get("gap") else None
            objectives.append(ObjectiveGrounding(item["objective_id"], item["query"], evidence, gap))
        grounding = GroundingResult(tuple(objectives), data["catalog_path"])
        return grounding, report(grounding.status)
    except subprocess.TimeoutExpired:
        # subprocess.run kills and waits for the child before raising this.
        return None, report("timeout", reason="Catalog search exceeded its time budget")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return None, report("unavailable", reason=type(exc).__name__)
