from __future__ import annotations

from .contracts import (
    DEFAULT_EXCLUDED_DIRECTORIES,
    DEFAULT_INCLUDED_SUFFIXES,
    OPTIONAL_SOURCE_SUFFIXES,
)
from .models import RepositoryAuditPolicy


def default_repository_audit_policy(
    *,
    include_source_code: bool = False,
) -> RepositoryAuditPolicy:
    suffixes = list(DEFAULT_INCLUDED_SUFFIXES)
    if include_source_code:
        suffixes.extend(OPTIONAL_SOURCE_SUFFIXES)
    return RepositoryAuditPolicy(
        included_suffixes=tuple(sorted(set(suffixes))),
        excluded_directories=tuple(sorted(DEFAULT_EXCLUDED_DIRECTORIES)),
        include_source_code=include_source_code,
    )
