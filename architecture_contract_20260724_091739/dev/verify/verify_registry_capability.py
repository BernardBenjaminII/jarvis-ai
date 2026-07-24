from pathlib import Path

from core.capabilities.models import CapabilityContext

from knowledge_engine.capabilities.knowledge_registry import (
    KnowledgeRegistryCapability,
)
from knowledge_engine.storage.database import KnowledgeDatabase


def main():

    db = KnowledgeDatabase(
        "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
    )

    context = CapabilityContext(
        root=Path(
            "/media/abdullah/JARVISDATA/Knowledge/Xfer_Staged_Files"
        ),
        database=db,
    )

    result = KnowledgeRegistryCapability().execute(context)

    if not result.success:
        print("Registry capability FAILED")
        print(result.errors)
        raise SystemExit(1)

    print()
    print("Registry capability OK")

    for key, value in sorted(result.metrics.items()):
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
