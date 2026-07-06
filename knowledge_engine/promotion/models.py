from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PromotionPlanItem:
    object_uuid: str
    title: str
    subject: str | None
    object_type: str
    source_path: str
    destination_path: str
    action: str
    reason: str
