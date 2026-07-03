from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegistryRecord:
    object_uuid: str
    object_path: str
    object_type: str
    title: str | None
    status: str
    lifecycle_state: str
    validation_state: str
    assimilation_state: str
    source: str | None
    trust_level: str
    duplicate_of: str | None
    notes: str | None
