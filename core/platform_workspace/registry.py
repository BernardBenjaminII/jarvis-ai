from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List

from core.bootstrap.discovery.platform import detect_platform


@dataclass(frozen=True)
class WorkspaceCapability:
    id: str
    label: str
    enabled: bool = True
    execution: bool = False
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PlatformWorkspace:
    platform: str
    workspace_id: str
    label: str
    stance: str
    execution_enabled: bool
    navigation: List[str] = field(default_factory=list)
    capabilities: Dict[str, WorkspaceCapability] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "workspace_id": self.workspace_id,
            "label": self.label,
            "stance": self.stance,
            "execution_enabled": self.execution_enabled,
            "navigation": list(self.navigation),
            "capabilities": {
                key: value.to_dict()
                for key, value in self.capabilities.items()
            },
        }


KALI_CAPABILITIES = {
    "missions": WorkspaceCapability(
        "missions",
        "Missions",
        execution=True,
        description="Authorized security mission management.",
    ),
    "bounties": WorkspaceCapability(
        "bounties",
        "Bug Bounties",
        execution=True,
        description="Bug bounty opportunity acquisition and management.",
    ),
    "targets": WorkspaceCapability(
        "targets",
        "Targets",
        execution=True,
        description="Authorized target and scope inventory.",
    ),
    "recon": WorkspaceCapability(
        "recon",
        "Recon",
        execution=True,
        description="Authorized reconnaissance orchestration.",
    ),
    "findings": WorkspaceCapability(
        "findings",
        "Findings",
        execution=False,
        description="Structured candidate vulnerability findings.",
    ),
    "agents": WorkspaceCapability(
        "agents",
        "Agents",
        execution=True,
        description="Human-gated security agents and queued jobs.",
    ),
    "intelligence": WorkspaceCapability(
        "intelligence",
        "Intelligence",
        execution=False,
        description="Security intelligence and vulnerability context.",
    ),
    "arsenal": WorkspaceCapability(
        "arsenal",
        "Arsenal",
        execution=False,
        description="Installed security tools and derived capabilities.",
    ),
    "terminal": WorkspaceCapability(
        "terminal",
        "Terminal",
        execution=True,
        description="Local Kali terminal operations.",
    ),
    "knowledge": WorkspaceCapability(
        "knowledge",
        "Knowledge",
        execution=False,
        description="Jarvis knowledge workspace.",
    ),
    "system": WorkspaceCapability(
        "system",
        "System",
        execution=False,
        description="Runtime, platform, and host health.",
    ),
}


WORKSPACES: Dict[str, PlatformWorkspace] = {
    "kali": PlatformWorkspace(
        platform="kali",
        workspace_id="kali-security",
        label="Kali Operations Center",
        stance="security",
        execution_enabled=True,
        navigation=[
            "missions",
            "bounties",
            "targets",
            "recon",
            "findings",
            "agents",
            "intelligence",
            "arsenal",
            "terminal",
            "knowledge",
            "system",
        ],
        capabilities=KALI_CAPABILITIES,
    ),

    "ubuntu": PlatformWorkspace(
        platform="ubuntu",
        workspace_id="ubuntu-engineering",
        label="Ubuntu Engineering Center",
        stance="engineering",
        execution_enabled=True,
        navigation=[
            "knowledge",
            "system",
        ],
        capabilities={
            "knowledge": WorkspaceCapability(
                "knowledge",
                "Knowledge",
                description="Jarvis knowledge workspace.",
            ),
            "system": WorkspaceCapability(
                "system",
                "System",
                description="Runtime, platform, and host health.",
            ),
        },
    ),

    "windows": PlatformWorkspace(
        platform="windows",
        workspace_id="windows-operations",
        label="Windows Operations Center",
        stance="general",
        execution_enabled=True,
        navigation=[
            "knowledge",
            "system",
        ],
        capabilities={
            "knowledge": WorkspaceCapability(
                "knowledge",
                "Knowledge",
                description="Jarvis knowledge workspace.",
            ),
            "system": WorkspaceCapability(
                "system",
                "System",
                description="Runtime, platform, and host health.",
            ),
        },
    ),

    "linux": PlatformWorkspace(
        platform="linux",
        workspace_id="linux-general",
        label="Linux Operations Center",
        stance="general",
        execution_enabled=False,
        navigation=[
            "knowledge",
            "system",
        ],
        capabilities={
            "knowledge": WorkspaceCapability(
                "knowledge",
                "Knowledge",
                description="Jarvis knowledge workspace.",
            ),
            "system": WorkspaceCapability(
                "system",
                "System",
                description="Runtime, platform, and host health.",
            ),
        },
    ),
}


def _environment_from_detection(result) -> str:
    if isinstance(result, str):
        return result.strip().lower()

    if isinstance(result, dict):
        return str(
            result.get("environment")
            or result.get("platform")
            or result.get("distribution")
            or "unknown"
        ).strip().lower()

    return str(getattr(result, "environment", "unknown")).strip().lower()


def get_platform_workspace(platform_name: str) -> PlatformWorkspace:
    name = (platform_name or "").strip().lower()

    if name in WORKSPACES:
        return WORKSPACES[name]

    return PlatformWorkspace(
        platform=name or "unknown",
        workspace_id="shared-review",
        label="Jarvis",
        stance="general",
        execution_enabled=False,
        navigation=["knowledge", "system"],
        capabilities={
            "knowledge": WorkspaceCapability(
                "knowledge",
                "Knowledge",
                description="Jarvis knowledge workspace.",
            ),
            "system": WorkspaceCapability(
                "system",
                "System",
                description="Runtime and host status.",
            ),
        },
    )


def get_current_workspace() -> PlatformWorkspace:
    detected = detect_platform()
    environment = _environment_from_detection(detected)
    return get_platform_workspace(environment)
