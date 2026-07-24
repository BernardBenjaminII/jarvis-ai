#!/usr/bin/env python3

from pathlib import Path

TOOLS = [
    "filesystem",
    "git",
    "docker",
    "knowledge",
    "memory",
    "network",
    "ollama",
    "shell",
]

OPERATIONS_TEMPLATE = '''"""
{name} tool.
"""

from typing import Any

TOOL = {{
    "name": "{name}",
    "version": "1.0",
    "description": "{name} operations",
}}

def execute(action: str, **kwargs: Any) -> dict:
    return {{
        "success": False,
        "tool": "{name}",
        "action": action,
        "error": f"Unsupported action: {{action}}",
    }}
'''

ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = ROOT / "tools"

print("\nBootstrapping plugins...\n")

for tool in TOOLS:

    tool_dir = TOOLS_DIR / tool
    tool_dir.mkdir(exist_ok=True)

    init_file = tool_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")

    operations = tool_dir / "operations.py"

    if not operations.exists():
        operations.write_text(
            OPERATIONS_TEMPLATE.format(name=tool)
        )
        print(f"Created {operations.relative_to(ROOT)}")

    execute = tool_dir / "execute.py"

    if execute.exists():
        legacy = tool_dir / "legacy_execute.py"

        if not legacy.exists():
            execute.rename(legacy)
            print(f"Renamed {execute.name} -> {legacy.name}")

print("\nDone.")
