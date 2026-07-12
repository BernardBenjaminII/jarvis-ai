"""
Read-only source-collection planning handler.

Phase VI-D2 resolves one source_collection object and creates a deterministic
direct-child expansion plan. It does not write to the registry or queue.
"""

from __future__ import annotations

from typing import Any

from knowledge_engine.assimilation.collection_plan import (
    CollectionExpansionPlanner,
)
from knowledge_engine.assimilation.handlers.base import (
    AssimilationHandler,
)


class SourceCollectionHandler(AssimilationHandler):
    """Plan the direct children of one registered source collection."""

    object_type = "source_collection"

    def __init__(
        self,
        db: Any,
        *,
        planner: CollectionExpansionPlanner | None = None,
    ):
        self.db = db
        self.planner = planner or CollectionExpansionPlanner()

    def plan(
        self,
        *,
        object_uuid: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Prepare a planning request.

        Phase VI-D2 performs planning during execute(), so this currently
        records the intent only.
        """
        del kwargs

        return {
            "status": "planning_ready",
            "object_uuid": object_uuid,
            "object_type": self.object_type,
        }

    def verify(
        self,
        *,
        object_uuid: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Verify that the collection exists before planning.
        """
        del kwargs

        collection = self._load_collection(object_uuid)

        return {
            "status": (
                "verified"
                if collection is not None
                else "not_found"
            ),
            "object_uuid": object_uuid,
            "object_type": self.object_type,
        }

    def recover(
        self,
        *,
        object_uuid: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Source collection planning is read-only, so no recovery is required.
        """
        del kwargs

        return {
            "status": "no_recovery_required",
            "object_uuid": object_uuid,
            "object_type": self.object_type,
        }

    def report(
        self,
        *,
        object_uuid: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Produce a minimal planning report.
        """
        del kwargs

        return {
            "status": "report_available",
            "object_uuid": object_uuid,
            "object_type": self.object_type,
        }


    def execute(
        self,
        *,
        object_uuid: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        del kwargs

        collection = self._load_collection(object_uuid)

        if collection is None:
            return {
                "processed": 0,
                "failed": 1,
                "object_uuid": object_uuid,
                "object_type": self.object_type,
                "status": "not_found",
                "message": (
                    "No registered source_collection object was found "
                    f"for UUID {object_uuid!r}."
                ),
            }

        try:
            plan = self.planner.plan(
                object_uuid=object_uuid,
                collection_path=collection["object_path"],
            )
        except (
            FileNotFoundError,
            NotADirectoryError,
            OSError,
        ) as exc:
            return {
                "processed": 0,
                "failed": 1,
                "object_uuid": object_uuid,
                "object_type": self.object_type,
                "status": "planning_failed",
                "message": str(exc),
                "error_type": type(exc).__name__,
            }

        return {
            "processed": 0,
            "failed": 0,
            "object_uuid": object_uuid,
            "object_type": self.object_type,
            "status": "planned",
            "message": (
                "Source collection direct-child expansion plan created. "
                "No registry changes were made."
            ),
            "plan": plan.to_dict(),
        }

    def _load_collection(
        self,
        object_uuid: str,
    ) -> dict[str, Any] | None:
        with self.db.connect() as conn:
            row = conn.execute(
                """
                SELECT
                    object_uuid,
                    object_path,
                    object_type,
                    lifecycle_state,
                    assimilation_state,
                    updated_at
                FROM knowledge_registry
                WHERE object_uuid=?
                  AND object_type='source_collection'
                LIMIT 1
                """,
                (object_uuid,),
            ).fetchone()

        if row is None:
            return None

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
        }
