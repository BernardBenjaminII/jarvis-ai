from __future__ import annotations

from knowledge_engine.objects.builder import build_objects


class ObjectService:
    """
    Thin service wrapper around the production object builder.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def run(
        self,
        root_filter: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, int]:

        return build_objects(
            db_path=self.db_path,
            root_filter=root_filter,
            dry_run=dry_run,
        )
