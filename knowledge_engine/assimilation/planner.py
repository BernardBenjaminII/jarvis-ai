"""
Object-type-aware mission planning for JARVIS knowledge assimilation.

Planning is read-only. Every queued registry object is classified through the
assimilation dispatch registry and assigned to its intended handler.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from knowledge_engine.assimilation.dispatch import get_handler_spec
from knowledge_engine.assimilation.mission import (
    AssimilationMission,
    AssimilationMissionItem,
    MissionStatus,
    build_mission_id,
    utc_now,
)


class AssimilationPlanner:
    """Build deterministic read-only plans from queued registry objects."""

    def __init__(self, db: Any):
        self.db = db

    def plan(
        self,
        *,
        limit: int = 25,
        object_types: Sequence[str] | None = None,
    ) -> AssimilationMission:
        """
        Plan queued knowledge objects across all registered object types.

        The only universal queue requirement is:

            assimilation_state = 'queued'

        Lifecycle states remain object-type specific. For example, the current
        registry correctly contains validated objects awaiting assimilation.
        """

        if limit < 1:
            raise ValueError("Assimilation mission limit must be at least 1")

        normalized_types = self._normalize_object_types(object_types)
        database_path = self._database_path()

        query = """
            SELECT
                object_uuid,
                object_path,
                object_type,
                lifecycle_state,
                assimilation_state,
                updated_at
            FROM knowledge_registry
            WHERE assimilation_state='queued'
        """

        parameters: list[Any] = []

        if normalized_types:
            placeholders = ", ".join("?" for _ in normalized_types)
            query += f" AND object_type IN ({placeholders})"
            parameters.extend(normalized_types)

        query += """
            ORDER BY
                updated_at ASC,
                object_type ASC,
                object_uuid ASC
            LIMIT ?
        """
        parameters.append(limit)

        with self.db.connect() as conn:
            rows = conn.execute(
                query,
                tuple(parameters),
            ).fetchall()

        items = [
            self._build_item(sequence=index, row=row)
            for index, row in enumerate(rows, start=1)
        ]

        mission_id = build_mission_id(
            database_path=database_path,
            object_uuids=[item.object_uuid for item in items],
        )

        notes = self._build_planning_notes(
            items=items,
            object_types=normalized_types,
        )

        return AssimilationMission(
            mission_id=mission_id,
            created_at=utc_now(),
            database_path=database_path,
            requested_limit=limit,
            requested_object_types=list(normalized_types),
            status=MissionStatus.PLANNED,
            items=items,
            planning_notes=notes,
        )

    def inventory(self) -> list[dict[str, Any]]:
        """Return aggregate registry state counts without modifying the DB."""

        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    object_type,
                    lifecycle_state,
                    assimilation_state,
                    COUNT(*) AS total
                FROM knowledge_registry
                GROUP BY
                    object_type,
                    lifecycle_state,
                    assimilation_state
                ORDER BY total DESC, object_type ASC
                """
            ).fetchall()

        inventory: list[dict[str, Any]] = []

        for row in rows:
            spec = get_handler_spec(str(row["object_type"]))

            inventory.append(
                {
                    "object_type": str(row["object_type"]),
                    "lifecycle_state": str(row["lifecycle_state"]),
                    "assimilation_state": str(row["assimilation_state"]),
                    "total": int(row["total"]),
                    "handler_name": spec.handler_name,
                    "handler_kind": spec.handler_kind,
                    "handler_readiness": spec.readiness.value,
                }
            )

        return inventory

    def peek_next(
        self,
        *,
        object_types: Sequence[str] | None = None,
    ) -> dict[str, Any] | None:
        """Return the next queued registry object without modifying it."""

        normalized_types = self._normalize_object_types(object_types)

        query = """
            SELECT
                object_uuid,
                object_path,
                object_type,
                lifecycle_state,
                assimilation_state,
                updated_at
            FROM knowledge_registry
            WHERE assimilation_state='queued'
        """

        parameters: list[Any] = []

        if normalized_types:
            placeholders = ", ".join("?" for _ in normalized_types)
            query += f" AND object_type IN ({placeholders})"
            parameters.extend(normalized_types)

        query += """
            ORDER BY
                updated_at ASC,
                object_type ASC,
                object_uuid ASC
            LIMIT 1
        """

        with self.db.connect() as conn:
            row = conn.execute(
                query,
                tuple(parameters),
            ).fetchone()

        if row is None:
            return None

        spec = get_handler_spec(str(row["object_type"]))

        return {
            "object_uuid": str(row["object_uuid"]),
            "object_path": str(row["object_path"]),
            "object_type": str(row["object_type"]),
            "lifecycle_state": str(row["lifecycle_state"]),
            "assimilation_state": str(row["assimilation_state"]),
            "updated_at": (
                str(row["updated_at"])
                if row["updated_at"] is not None
                else None
            ),
            "handler_name": spec.handler_name,
        }

    def _database_path(self) -> str:
        for attribute in (
            "path",
            "db_path",
            "database_path",
            "filename",
        ):
            value = getattr(self.db, attribute, None)
            if value:
                return str(Path(value).expanduser().resolve())

        return "<configured KnowledgeDatabase>"

    @staticmethod
    def _normalize_object_types(
        object_types: Sequence[str] | None,
    ) -> tuple[str, ...]:
        if not object_types:
            return ()

        normalized = {
            str(object_type).strip()
            for object_type in object_types
            if str(object_type).strip()
        }

        return tuple(sorted(normalized))

    @staticmethod
    def _build_item(
        *,
        sequence: int,
        row: Any,
    ) -> AssimilationMissionItem:
        object_type = str(row["object_type"])
        spec = get_handler_spec(object_type)

        path = Path(str(row["object_path"])).expanduser()
        exists = path.exists()
        is_file = path.is_file() if exists else False
        is_directory = path.is_dir() if exists else False

        size_bytes: int | None = None

        if is_file:
            try:
                size_bytes = path.stat().st_size
            except OSError:
                size_bytes = None

        return AssimilationMissionItem(
            sequence=sequence,
            object_uuid=str(row["object_uuid"]),
            object_path=str(path),
            object_type=object_type,
            lifecycle_state=str(row["lifecycle_state"]),
            assimilation_state=str(row["assimilation_state"]),
            updated_at=(
                str(row["updated_at"])
                if row["updated_at"] is not None
                else None
            ),
            handler_name=spec.handler_name,
            handler_kind=spec.handler_kind,
            handler_readiness=spec.readiness.value,
            handler_description=spec.description,
            executable_in_current_phase=spec.executable,
            path_exists=exists,
            path_is_file=is_file,
            path_is_directory=is_directory,
            size_bytes=size_bytes,
        )

    @staticmethod
    def _build_planning_notes(
        *,
        items: list[AssimilationMissionItem],
        object_types: tuple[str, ...],
    ) -> list[str]:
        notes: list[str] = []

        if object_types:
            notes.append(
                "Object-type filter: " + ", ".join(object_types)
            )

        if not items:
            notes.append(
                "No registry objects matched the requested queued-work plan."
            )
            return notes

        unsupported = sum(not item.dispatchable for item in items)
        missing_paths = sum(not item.path_exists for item in items)
        available_handlers = sum(
            item.handler_readiness == "available"
            for item in items
        )
        planned_handlers = sum(
            item.handler_readiness == "planned"
            for item in items
        )

        notes.append(
            f"{len(items)} queued object(s) were assigned to assimilation "
            "handlers."
        )
        notes.append(
            f"{available_handlers} object(s) map to implemented handlers; "
            f"{planned_handlers} map to planned handlers."
        )

        if unsupported:
            notes.append(
                f"{unsupported} object(s) have no registered handler."
            )

        if missing_paths:
            notes.append(
                f"{missing_paths} planned object path(s) are currently absent."
            )

        notes.append(
            "Execution remains disabled in Phase VI-A2 until handler safety "
            "and recovery contracts are implemented."
        )

        return notes
