from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import shutil
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class ArsenalTool:
    id: str
    label: str
    command: str
    category: str
    capabilities: tuple[str, ...]
    description: str = ""
    optional: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ArsenalCapability:
    id: str
    label: str
    category: str
    description: str

    def to_dict(self) -> dict:
        return asdict(self)


CAPABILITIES: Dict[str, ArsenalCapability] = {
    "subdomain_discovery": ArsenalCapability(
        "subdomain_discovery",
        "Subdomain Discovery",
        "discovery",
        "Enumerate candidate subdomains for an authorized scope.",
    ),
    "dns_resolution": ArsenalCapability(
        "dns_resolution",
        "DNS Resolution",
        "discovery",
        "Resolve and validate DNS names.",
    ),
    "http_probe": ArsenalCapability(
        "http_probe",
        "HTTP Probing",
        "web",
        "Identify responding HTTP/S services.",
    ),
    "port_discovery": ArsenalCapability(
        "port_discovery",
        "Port Discovery",
        "network",
        "Identify exposed network services within authorized scope.",
    ),
    "service_enumeration": ArsenalCapability(
        "service_enumeration",
        "Service Enumeration",
        "network",
        "Identify service and protocol metadata.",
    ),
    "web_crawling": ArsenalCapability(
        "web_crawling",
        "Web Crawling",
        "web",
        "Discover links and application paths.",
    ),
    "historical_url_discovery": ArsenalCapability(
        "historical_url_discovery",
        "Historical URL Discovery",
        "web",
        "Collect previously observed URLs from passive archives.",
    ),
    "content_discovery": ArsenalCapability(
        "content_discovery",
        "Content Discovery",
        "web",
        "Discover files and paths within an authorized web target.",
    ),
    "template_scanning": ArsenalCapability(
        "template_scanning",
        "Template Scanning",
        "analysis",
        "Apply approved vulnerability and exposure templates.",
    ),
    "manual_web_testing": ArsenalCapability(
        "manual_web_testing",
        "Manual Web Testing",
        "analysis",
        "Interactive inspection of authorized web applications.",
    ),
    "domain_intelligence": ArsenalCapability(
        "domain_intelligence",
        "Domain Intelligence",
        "intelligence",
        "Inspect registration and DNS metadata.",
    ),
}


TOOLS: tuple[ArsenalTool, ...] = (
    ArsenalTool(
        "subfinder",
        "Subfinder",
        "subfinder",
        "discovery",
        ("subdomain_discovery",),
        "Passive subdomain discovery.",
    ),
    ArsenalTool(
        "amass",
        "Amass",
        "amass",
        "discovery",
        ("subdomain_discovery", "dns_resolution"),
        "Attack-surface and subdomain enumeration.",
        optional=True,
    ),
    ArsenalTool(
        "dnsx",
        "dnsx",
        "dnsx",
        "discovery",
        ("dns_resolution",),
        "DNS resolution and probing.",
        optional=True,
    ),
    ArsenalTool(
        "httpx",
        "ProjectDiscovery HTTPX",
        "httpx",
        "web",
        ("http_probe",),
        "HTTP service probing.",
    ),
    ArsenalTool(
        "naabu",
        "Naabu",
        "naabu",
        "network",
        ("port_discovery",),
        "Fast port discovery.",
        optional=True,
    ),
    ArsenalTool(
        "nmap",
        "Nmap",
        "nmap",
        "network",
        ("port_discovery", "service_enumeration"),
        "Network and service discovery.",
    ),
    ArsenalTool(
        "katana",
        "Katana",
        "katana",
        "web",
        ("web_crawling",),
        "Web application crawler.",
        optional=True,
    ),
    ArsenalTool(
        "gau",
        "gau",
        "gau",
        "web",
        ("historical_url_discovery",),
        "Passive historical URL collection.",
        optional=True,
    ),
    ArsenalTool(
        "waybackurls",
        "waybackurls",
        "waybackurls",
        "web",
        ("historical_url_discovery",),
        "Wayback Machine URL collection.",
        optional=True,
    ),
    ArsenalTool(
        "ffuf",
        "ffuf",
        "ffuf",
        "web",
        ("content_discovery",),
        "Web content discovery and fuzzing.",
    ),
    ArsenalTool(
        "nuclei",
        "Nuclei",
        "nuclei",
        "analysis",
        ("template_scanning",),
        "Template-based exposure and vulnerability analysis.",
    ),
    ArsenalTool(
        "burpsuite",
        "Burp Suite",
        "burpsuite",
        "analysis",
        ("manual_web_testing",),
        "Interactive web security testing proxy.",
        optional=True,
    ),
    ArsenalTool(
        "whois",
        "WHOIS",
        "whois",
        "intelligence",
        ("domain_intelligence",),
        "Domain registration metadata.",
    ),
    ArsenalTool(
        "dig",
        "dig",
        "dig",
        "intelligence",
        ("dns_resolution", "domain_intelligence"),
        "DNS query utility.",
    ),
)


def _httpx_recon_available() -> Optional[bool]:
    """
    Reuse Jarvis' existing static HTTPX identity inspector.

    Returns None when that subsystem is unavailable rather than
    guessing that any command named 'httpx' is the recon tool.
    """
    try:
        from core.bounty_worker.identity import inventory

        identities = inventory()
        httpx = identities.get("httpx", {})

        if "recon_available" in httpx:
            return bool(httpx["recon_available"])

    except Exception:
        pass

    return None


def _resolve_tool(tool: ArsenalTool) -> dict:
    path = shutil.which(tool.command)
    present = path is not None
    identity_verified = True

    if tool.id == "httpx":
        verified = _httpx_recon_available()

        if verified is None:
            identity_verified = False
            available = False
        else:
            identity_verified = verified
            available = present and verified
    else:
        available = present

    return {
        **tool.to_dict(),
        "present": present,
        "available": available,
        "identity_verified": identity_verified,
        "path": str(Path(path).resolve()) if path else None,
    }


def _derive_capabilities(tools: Iterable[dict]) -> List[dict]:
    resolved = list(tools)
    output: List[dict] = []

    for capability_id, capability in CAPABILITIES.items():
        providers = [
            tool
            for tool in resolved
            if capability_id in tool["capabilities"]
        ]

        available_providers = [
            tool["id"]
            for tool in providers
            if tool["available"]
        ]

        installed_providers = [
            tool["id"]
            for tool in providers
            if tool["present"]
        ]

        output.append(
            {
                **capability.to_dict(),
                "available": bool(available_providers),
                "providers": [tool["id"] for tool in providers],
                "installed_providers": installed_providers,
                "available_providers": available_providers,
            }
        )

    return output


def build_arsenal_snapshot() -> dict:
    tools = [_resolve_tool(tool) for tool in TOOLS]
    capabilities = _derive_capabilities(tools)

    installed_count = sum(
        1 for tool in tools if tool["present"]
    )

    available_tool_count = sum(
        1 for tool in tools if tool["available"]
    )

    available_capability_count = sum(
        1 for capability in capabilities
        if capability["available"]
    )

    required_tools = [
        tool for tool in tools if not tool["optional"]
    ]

    missing_required = [
        tool["id"]
        for tool in required_tools
        if not tool["available"]
    ]

    if not missing_required:
        health = "ready"
    elif available_capability_count:
        health = "partial"
    else:
        health = "unavailable"

    return {
        "health": health,
        "summary": {
            "defined_tools": len(tools),
            "installed_tools": installed_count,
            "available_tools": available_tool_count,
            "defined_capabilities": len(capabilities),
            "available_capabilities": available_capability_count,
            "missing_required_tools": missing_required,
        },
        "tools": tools,
        "capabilities": capabilities,
    }
