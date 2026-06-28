#!/usr/bin/env python3
"""
Migrate JARVIS tools to the new plugin architecture.

Converts:

tools/<tool>/
    execute.py
    operations.py

into

tools/<tool>/
    __init__.py
    operations.py

without deleting anything.

Safe to run multiple times.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"

HEADER = '''"""
JARVIS Plugin

This package exposes the public interface for the plugin.
"""

from .operations import execute

TOOL = {
    "name": "%NAME%",
    "description": "%NAME% plugin",
    "version": "1.0.0",
    "actions": [],
}
'''


def migrate_tool(tool_dir: Path):

    if not tool_dir.is_dir():
        return

    name = tool_dir.name

    if name.startswith("_"):
        return

    operations = tool_dir / "operations.py"

    if not operations.exists():
        return

    init_file = tool_dir / "__init__.py"

    if not init_file.exists():

        init_file.write_text(
            HEADER.replace("%NAME%", name)
        )

        print(f"✓ Created {init_file.relative_to(PROJECT_ROOT)}")

    execute = tool_dir / "execute.py"

    if execute.exists():

        execute.rename(tool_dir / "execute.py.bak")

        print(
            f"✓ Renamed {execute.relative_to(PROJECT_ROOT)} -> execute.py.bak"
        )


def main():

    print()

    print("=" * 60)
    print("JARVIS Tool Migration")
    print("=" * 60)
    print()

    count = 0

    for tool in sorted(TOOLS_DIR.iterdir()):

        migrate_tool(tool)
        count += 1

    print()
    print(f"Processed {count} tool directories.")
    print()
    print("Migration complete.")


if __name__ == "__main__":
    main()
