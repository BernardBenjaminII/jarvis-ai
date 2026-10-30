from __future__ import annotations

from fastapi import APIRouter

from core.bootstrap.discovery.platform import detect_platform
from core.platform_workspace.registry import (
    get_current_workspace,
    get_platform_workspace,
)

router = APIRouter(
    prefix="/api/platform-workspace",
    tags=["platform-workspace"],
)


def _normalize_detection(result) -> dict:
    """
    Normalize the existing Jarvis platform detector without replacing it.

    detect_platform() may return a string or a structured mapping depending
    on the calling layer/version.  The workspace API exposes a stable shape.
    """

    if isinstance(result, str):
        return {
            "environment": result.strip().lower(),
        }

    if isinstance(result, dict):
        payload = dict(result)

        environment = (
            payload.get("environment")
            or payload.get("platform")
            or payload.get("distribution")
            or "unknown"
        )

        payload["environment"] = str(environment).strip().lower()
        return payload

    environment = getattr(result, "environment", None)

    return {
        "environment": str(environment or "unknown").strip().lower(),
    }


def build_workspace_payload() -> dict:
    detection = detect_platform()
    platform_info = _normalize_detection(detection)

    workspace = get_current_workspace()

    return {
        "platform": platform_info,
        "workspace": workspace.to_dict(),
    }


@router.get("")
def platform_workspace():
    """
    Return the workspace Jarvis should expose on the current host.
    """
    return build_workspace_payload()


@router.get("/")
def platform_workspace_slash():
    """
    Slash-compatible alias.
    """
    return build_workspace_payload()


@router.get("/{platform_name}")
def platform_workspace_for(platform_name: str):
    """
    Resolve a platform workspace without changing the running host.

    Primarily useful for diagnostics and tests.
    """
    workspace = get_platform_workspace(platform_name)

    return {
        "requested_platform": platform_name.strip().lower(),
        "workspace": workspace.to_dict(),
    }
