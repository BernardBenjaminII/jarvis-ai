from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class TrustedSource:
    name: str
    trust_score: int
    base_url: str
    formats: list[str]
    topics: list[str]
    method: str
    query_templates: list[str]


@dataclass(slots=True)
class DiscoveryCandidate:
    topic: str
    source_name: str
    trust_score: int
    method: str
    base_url: str
    query: str
    priority: int
    reason: str
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)
