"""
docker tool.
"""

from typing import Any

TOOL = {
    "name": "docker",
    "version": "1.0",
    "description": "docker operations",
}

def execute(action: str, **kwargs: Any) -> dict:
    return {
        "success": False,
        "tool": "docker",
        "action": action,
        "error": f"Unsupported action: {action}",
    }
