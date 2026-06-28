"""
shell tool.
"""

from typing import Any

TOOL = {
    "name": "shell",
    "version": "1.0",
    "description": "shell operations",
}

def execute(action: str, **kwargs: Any) -> dict:
    return {
        "success": False,
        "tool": "shell",
        "action": action,
        "error": f"Unsupported action: {action}",
    }
