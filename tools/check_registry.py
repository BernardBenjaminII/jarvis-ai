from pprint import pprint

from core.src.runtime.tool_registry import registry

r = registry()

print()

print("Available tools")
print("----------------")

for tool in r.tools():
    print(tool)

print()

pprint(
    r.execute(
        "filesystem",
        action="ls",
        path="runtime"
    )
)
