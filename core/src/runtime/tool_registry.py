from __future__ import annotations

import importlib
from pathlib import Path


class ToolRegistry:

    def __init__(self):
        self._tools = {}

    def discover(self):

        tools_root = Path(__file__).resolve().parents[3] / "tools"

        for item in tools_root.iterdir():

            if not item.is_dir():
                continue

            if item.name.startswith("_"):
                continue

            operations = item / "operations.py"

            if not operations.exists():
                continue

            module_name = f"tools.{item.name}.operations"

            try:

                module = importlib.import_module(module_name)

                self._tools[item.name] = module

                print(f"✓ Loaded tool: {item.name}")

            except Exception as e:

                print(f"Failed loading {item.name}: {e}")

    def execute(self, tool: str, **kwargs):

        module = self._tools.get(tool)

        if module is None:
            return {
                "success": False,
                "error": f"Unknown tool '{tool}'",
            }

        return module.execute(**kwargs)

    def tools(self):
        return sorted(self._tools.keys())


_registry = ToolRegistry()
_registry.discover()


def registry():
    return _registry
