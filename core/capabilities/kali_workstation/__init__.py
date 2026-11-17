"""R9.19 R2: Read-only Kali workstation inventory."""

from __future__ import annotations

import shutil

from core.capabilities.base import Capability
from core.capabilities.metadata import (
    CapabilityBindingState,
    CapabilityMetadata,
    CapabilityOperation,
)
from core.capabilities.models import (
    CapabilityContext,
    CapabilityResult,
)
from core.security.external_arsenal import snapshot as arsenal_snapshot


TOOLS = (
    "nmap",
    "subfinder",
    "httpx",
    "dnsx",
    "nuclei",
    "ffuf",
    "amass",
    "masscan",
)


def inventory_snapshot() -> dict:
    """Discover local tools without executing them."""

    tools = {}

    for name in TOOLS:
        path = shutil.which(name)
        tools[name] = {
            "installed": path is not None,
            "path": path,
        }

    installed = sum(
        item["installed"] for item in tools.values()
    )

    return {
        "state": (
            "ready" if installed == len(TOOLS)
            else "degraded"
        ),
        "mode": "inventory_only",
        "execution_authorized": False,
        "tool_count": len(TOOLS),
        "installed_count": installed,
        "tools": tools,
        "arsenal": arsenal_snapshot(),
    }


class KaliWorkstationInventory(Capability):
    name = "kali.workstation.inventory"
    description = "Read-only Kali workstation inventory"
    requires = set()
    provides = {"kali.workstation.inventory.read"}
    order = 500

    metadata = CapabilityMetadata(
        display_name="Kali Bug Bounty Workstation",
        description=(
            "Discover installed security tools and "
            "external arsenal availability."
        ),
        domain="security",
        subsystem="kali_workstation",
        binding_state=CapabilityBindingState.BOUND,
        operations=(
            CapabilityOperation(
                name="inventory",
                destructive=False,
                supports_dry_run=False,
                bound=True,
            ),
        ),
        tags=(
            "kali",
            "bug-bounty",
            "read-only",
            "inventory",
            "execution-disabled",
        ),
        source="core.capabilities.kali_workstation",
        version="r919r2",
    )

    def execute(
        self, context: CapabilityContext
    ) -> CapabilityResult:
        try:
            inventory = inventory_snapshot()
            warnings = []

            if inventory["state"] != "ready":
                warnings.append("Some Kali tools are missing.")

            if inventory["arsenal"]["state"] != "ready":
                warnings.append(
                    "External arsenal is not fully ready."
                )

            return CapabilityResult(
                name=self.name,
                success=True,
                metrics={"inventory": inventory},
                warnings=warnings,
            )
        except Exception as exc:
            return CapabilityResult(
                name=self.name,
                success=False,
                errors=[str(exc)],
            )


def register_capabilities(registry):
    registry.register(KaliWorkstationInventory())
