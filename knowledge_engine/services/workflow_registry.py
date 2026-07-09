from __future__ import annotations

import uuid


class WorkflowRegistryService:
    """
    Temporary in-memory registry service.

    Produces registry identifiers without
    writing to the production database.

    The Librarian will later commit these
    into the Knowledge Registry.
    """

    def register(
        self,
        chunks: list[str],
    ) -> list[str]:

        return [
            str(uuid.uuid4())
            for _ in chunks
        ]
