"""Executive Knowledge Inventory projection provider."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.integration.contracts import (
    ProjectionEnvelope,
    ProjectionHealth,
    ProjectionStatus,
)
from core.integration.knowledge_inventory import KnowledgeInventoryService


class KnowledgeProjectionProvider:
    """Project the read-only state of the JARVIS knowledge estate."""

    projection_id = "knowledge"
    schema_version = "1.0"

    def __init__(
        self,
        inventory_service: KnowledgeInventoryService,
    ) -> None:
        self.inventory_service = inventory_service

    @staticmethod
    def _qualified_type(value: object) -> str:
        cls = value.__class__
        return f"{cls.__module__}.{cls.__qualname__}"

    @staticmethod
    def _health_for(
        inventory: dict[str, Any],
    ) -> ProjectionHealth:
        if not inventory.get("root_exists"):
            return ProjectionHealth(
                status=ProjectionStatus.NOT_CONFIGURED,
                summary="The configured knowledge root does not exist.",
                details={
                    "root": inventory.get("root"),
                    "database_count": 0,
                },
                errors=tuple(inventory.get("errors", [])),
            )

        if not inventory.get("root_readable"):
            return ProjectionHealth(
                status=ProjectionStatus.UNAVAILABLE,
                summary="The configured knowledge root is not readable.",
                details={
                    "root": inventory.get("root"),
                    "database_count": inventory.get(
                        "database_count",
                        0,
                    ),
                },
                errors=tuple(inventory.get("errors", [])),
            )

        unavailable_databases = [
            database["name"]
            for database in inventory.get("databases", [])
            if database.get("status") == "unavailable"
        ]
        degraded_databases = [
            database["name"]
            for database in inventory.get("databases", [])
            if database.get("status") == "degraded"
        ]

        if inventory.get("errors") or unavailable_databases:
            return ProjectionHealth(
                status=ProjectionStatus.DEGRADED,
                summary="Knowledge inventory completed with unavailable resources.",
                details={
                    "root": inventory.get("root"),
                    "database_count": inventory.get(
                        "database_count",
                        0,
                    ),
                    "unavailable_databases": unavailable_databases,
                    "degraded_databases": degraded_databases,
                },
                warnings=tuple(inventory.get("warnings", [])),
                errors=tuple(inventory.get("errors", [])),
            )

        if inventory.get("warnings") or degraded_databases:
            return ProjectionHealth(
                status=ProjectionStatus.DEGRADED,
                summary="Knowledge inventory completed with warnings.",
                details={
                    "root": inventory.get("root"),
                    "database_count": inventory.get(
                        "database_count",
                        0,
                    ),
                    "degraded_databases": degraded_databases,
                },
                warnings=tuple(inventory.get("warnings", [])),
            )

        return ProjectionHealth(
            status=ProjectionStatus.AVAILABLE,
            summary="Knowledge inventory is available.",
            details={
                "root": inventory.get("root"),
                "database_count": inventory.get(
                    "database_count",
                    0,
                ),
                "database_total_rows": inventory.get(
                    "database_total_rows",
                    0,
                ),
                "total_files": inventory.get(
                    "filesystem",
                    {},
                ).get("total_files", 0),
            },
        )

    def health(self) -> ProjectionHealth:
        try:
            inventory = self.inventory_service.inventory()
        except Exception as exc:
            return ProjectionHealth(
                status=ProjectionStatus.UNAVAILABLE,
                summary="Knowledge inventory projection failed.",
                errors=(str(exc),),
            )

        return self._health_for(inventory)


    def project(self) -> ProjectionEnvelope:
        generated_at = datetime.now(timezone.utc)

        try:
            inventory = self.inventory_service.inventory()
            health = self._health_for(inventory)

            data = {
                "inventory": inventory,
                "summary": {
                    "root": inventory.get("root"),
                    "database_count": inventory.get(
                        "database_count",
                        0,
                    ),
                    "database_total_rows": inventory.get(
                        "database_total_rows",
                        0,
                    ),
                    "total_files": inventory.get(
                        "filesystem",
                        {},
                    ).get("total_files", 0),
                    "total_directories": inventory.get(
                        "filesystem",
                        {},
                    ).get("total_directories", 0),
                    "total_bytes": inventory.get(
                        "filesystem",
                        {},
                    ).get("total_bytes", 0),
                    "scan_truncated": inventory.get(
                        "filesystem",
                        {},
                    ).get("scan_truncated", False),
                    "fingerprint": inventory.get("fingerprint"),
                },
            }

            warnings = tuple(inventory.get("warnings", []))
            errors = tuple(inventory.get("errors", []))

            captured_at = inventory.get("captured_at")

            if isinstance(captured_at, datetime):
                source_timestamp = captured_at
            elif isinstance(captured_at, str):
                source_timestamp = datetime.fromisoformat(
                    captured_at.replace("Z", "+00:00")
                )
            else:
                source_timestamp = None

        except Exception as exc:
            health = ProjectionHealth(
                status=ProjectionStatus.UNAVAILABLE,
                summary="Knowledge inventory projection failed.",
                errors=(str(exc),),
            )

            data = {
                "inventory": None,
                "summary": None,
            }

            warnings = ()
            errors = (str(exc),)
            source_timestamp = None

        return ProjectionEnvelope(
            projection_id=self.projection_id,
            schema_version=self.schema_version,
            generated_at=generated_at,
            source_timestamp=source_timestamp,
            provider=self._qualified_type(self),
            health=health,
            data=data,
            warnings=warnings,
            errors=errors,
        )
