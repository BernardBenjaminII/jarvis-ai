from __future__ import annotations

from core.bounty_catalog.store import Catalog

from .model import ProgramIntakeDraft


def hackerone_catalog_draft(
    catalog: Catalog,
    handle: str,
) -> ProgramIntakeDraft:
    """
    Convert an authenticated HackerOne catalog observation
    into a non-executable R9.0B program intake draft.

    This function deliberately does not infer or manufacture
    structured scope from program listing metadata.
    """

    record = catalog.review_record(
        handle,
        source="hackerone-api",
    )

    return ProgramIntakeDraft.from_catalog_record(
        record
    )
