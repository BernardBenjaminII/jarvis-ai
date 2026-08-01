from __future__ import annotations
from enum import Enum

RATIFICATION_SCHEMA_VERSION = "1.0.0"

class RatificationStatus(str, Enum):
    RATIFIED = "ratified"
    REVIEW_REQUIRED = "review_required"
    REJECTED = "rejected"

DEFAULT_SECTION_ORDER = (
    "executive","governance","knowledge","evidence","reasoning","planning",
    "execution","memory","experience","security","safety","engineering",
    "operations","general",
)
