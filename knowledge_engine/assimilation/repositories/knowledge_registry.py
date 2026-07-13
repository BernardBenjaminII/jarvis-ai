"""
Knowledge Registry persistence repository.

This repository owns read access to knowledge_registry records required by
the assimilation layer.

It does not:

- make assimilation decisions
- plan collection expansion
- change lifecycle states
- manage queue state
- commit or roll back caller-owned transactions
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class KnowledgeRegistryObject:
    """Immutable representation of one knowledge_registry record."""

    object_uuid: str
    object_path: str
    object_type: str
    lifecycle_state: str
    assimilation_state: str
    updated_at: str | None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation of the registry object."""

        return asdict(self)


class KnowledgeRegistryRepository:
    """Read knowledge objects from the canonical knowledge registry."""

    def __init__(self, db: Any):
        if db is None:
            raise ValueError("db must not be None")

        if not hasattr(db, "connect"):
            raise TypeError(
                "db must expose a callable connect() method"
            )

        if not callable(db.connect):
            raise TypeError(
                "db.connect must be callable"
            )

        self.db = db

    def get_object(
        self,
        *,
        object_uuid: str,
        object_type: str | None = None,
    ) -> KnowledgeRegistryObject | None:
        """
        Load one registry object by UUID.

        When object_type is provided, the record must also match that type.
        """

        normalized_uuid = object_uuid.strip()

        if not normalized_uuid:
            raise ValueError("object_uuid must not be empty")

        if object_type is not None and not object_type.strip():
            raise ValueError(
                "object_type must not be blank when provided"
            )

        query = """
            SELECT
                object_uuid,
                object_path,
                object_type,
                lifecycle_state,
                assimilation_state,
                updated_at
            FROM knowledge_registry
            WHERE object_uuid=?
        """

        parameters: list[Any] = [
            normalized_uuid,
        ]

        if object_type is not None:
            query += " AND object_type=?"
            parameters.append(object_type.strip())

        query += " LIMIT 1"

        with self.db.connect() as conn:
            row = conn.execute(
                query,
                tuple(parameters),
            ).fetchone()

        if row is None:
            return None

        return self._map_row(row)

    def get_source_collection(
        self,
        *,
        object_uuid: str,
    ) -> KnowledgeRegistryObject | None:
        """Load one source_collection registry object."""

        return self.get_object(
            object_uuid=object_uuid,
            object_type="source_collection",
        )

    @staticmethod
    def _map_row(row: Any) -> KnowledgeRegistryObject:
        """Convert one SQLite-style row into an immutable model."""

        return KnowledgeRegistryObject(
            object_uuid=str(row["object_uuid"]),
            object_path=str(row["object_path"]),
            object_type=str(row["object_type"]),
            lifecycle_state=str(row["lifecycle_state"]),
            assimilation_state=str(row["assimilation_state"]),
            updated_at=(
                str(row["updated_at"])
                if row["updated_at"] is not None
                else None
            ),
        )
