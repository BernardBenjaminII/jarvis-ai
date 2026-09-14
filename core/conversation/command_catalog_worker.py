"""Private subprocess entry point; receives one command-advice query on stdin."""
from pathlib import Path
import json
import sys


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from core.conversation.contracts import ExecutiveRequestContext, CompiledObjective
    from core.conversation.grounding import CatalogGroundingService
    payload = json.load(sys.stdin)
    context = ExecutiveRequestContext.create(
        operator_input=payload["operator_input"], session_id=payload["session_id"],
        mode=payload["mode"], channel=payload["channel"],
        objectives=tuple(CompiledObjective(**item) for item in payload["objectives"]),
    )
    service = CatalogGroundingService(database_path=sys.argv[1], limit_per_objective=int(sys.argv[3]))
    result = service.ground(context)
    Path(sys.argv[2]).write_text(json.dumps(result.to_dict()))


if __name__ == "__main__":
    main()
