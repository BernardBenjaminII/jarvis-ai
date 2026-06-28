"""
memory tool.
"""

from typing import Any

TOOL = {
    "name": "memory",
    "version": "1.0",
    "description": "memory operations",
}

def execute(action: str, **kwargs: Any) -> dict:
    return {
        "success": False,
        "tool": "memory",
        "action": action,
        "error": f"Unsupported action: {action}",
    }
