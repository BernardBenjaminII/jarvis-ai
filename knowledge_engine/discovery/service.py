from __future__ import annotations

from knowledge_engine.discovery.filesystem import discover


class DiscoveryService:

    def __init__(self, db_path: str):
        self.db_path = db_path

    def run(
        self,
        root_path: str,
        limit: int | None = None,
    ) -> dict[str, int]:

        return discover(
            root_path=root_path,
            db_path=self.db_path,
            limit=limit,
        )
