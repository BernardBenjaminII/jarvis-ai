from __future__ import annotations
from typing import Protocol, runtime_checkable
from core.integration.contracts import ProjectionEnvelope, ProjectionHealth

@runtime_checkable
class ProjectionProvider(Protocol):
    projection_id: str
    schema_version: str
    def health(self) -> ProjectionHealth: ...
    def project(self) -> ProjectionEnvelope: ...
