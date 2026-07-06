from pathlib import Path

from core.capabilities.models import CapabilityContext

from knowledge_engine.capabilities.objects import ObjectCapability
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

    result = ObjectCapability(
        dry_run=True
    ).execute(context)

    assert result.success

    print()

    print("Object capability OK")

    for k, v in sorted(result.metrics.items()):
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
