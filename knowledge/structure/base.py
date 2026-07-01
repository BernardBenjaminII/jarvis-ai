from dataclasses import dataclass
from typing import Optional


@dataclass
class StructureNode:
    document_path: str
    title: str
    level: int
    page: Optional[int]
    order_index: int
    parent_title: Optional[str] = None
    source: str = "unknown"
