from dataclasses import dataclass


@dataclass
class QueueItem:
    document_path: str
    priority: int
    reason: str
