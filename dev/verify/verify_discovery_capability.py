from __future__ import annotations

from pathlib import Path

from core.capabilities.models import CapabilityContext
from knowledge_engine.capabilities.discovery import DiscoveryCapability
from knowledge_engine.storage.database import KnowledgeDatabase


def main() -> None:
    db = KnowledgeDatabase("/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite")

    context = CapabilityContext(
        root=Path("/media/abdullah/JARVISDATA/Knowledge/Xfer_Staged_Files"),
        database=db,
    )

    result = DiscoveryCapability(limit=25).execute(context)

    assert result.success, result.errors
    assert result.metrics.get("seen", 0) > 0, result.metrics

    print("Discovery capability OK")
    print(result.metrics)


if __name__ == "__main__":
    main()
