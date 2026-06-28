"""
ollama tool.
"""

from typing import Any

TOOL = {
    "name": "ollama",
    "version": "1.0",
    "description": "ollama operations",
}

def execute(action: str, **kwargs: Any) -> dict:
    return {
        "success": False,
        "tool": "ollama",
        "action": action,
        "error": f"Unsupported action: {action}",
    }
