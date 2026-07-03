from dataclasses import dataclass


@dataclass
class QueueItem:
    # Legacy
    document_path: str | None = None

    # Knowledge Object
    object_uuid: str | None = None
    object_path: str | None = None
    object_type: str | None = None

    # Queue
    priority: int = 0
    lifecycle_state: str = "queued"
    reason: str = ""

    def __str__(self) -> str:
        path = self.object_path or self.document_path or "<unknown>"

        return (
            f"[P{self.priority:03}] "
            f"{self.object_type or 'document'} | "
            f"{self.lifecycle_state} | "
            f"{path}"
        )

    __repr__ = __str__
