from pprint import pprint

from core.src.planner.tool_planner import planner
from core.src.runtime.executor import executor


questions = [
    "List the runtime directory",
    "Does the knowledge directory exist?",
    "How much free space is left?",
    "Find launcher.py",
]


for q in questions:

    print("=" * 60)
    print(q)

    plan = planner.plan(q)

    print("\nPLAN")
    pprint(plan)

    print("\nRESULT")
    pprint(executor.execute(plan))
