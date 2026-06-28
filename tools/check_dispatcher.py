from pprint import pprint

from tools.dispatcher import dispatcher

tests = [
    ("filesystem", "ls", {"path": "runtime"}),
    ("filesystem", "exists", {"path": "knowledge"}),
    ("filesystem", "disk_usage", {"path": "runtime"}),
]

for tool, action, kwargs in tests:

    print("=" * 60)

    pprint(
        dispatcher.dispatch(
            tool,
            action,
            **kwargs,
        )
    )
