"""Catalog and deterministic search for cognitive workspaces."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Iterable

from core.cognition.workspace.enums import (
    HypothesisStatus,
    WorkspaceStatus,
)
from core.cognition.workspace.models import CognitiveWorkspace
from core.cognition.workspace.repository import CognitiveWorkspaceRepository


class WorkspaceSortField(StrEnum):
    """Supported deterministic catalog ordering fields."""

    UPDATED_AT = "updated_at"
    CREATED_AT = "created_at"
    OBJECTIVE = "objective"
    REVISION = "revision"
    STRONGEST_CONFIDENCE = "strongest_confidence"


class SortDirection(StrEnum):
    """Supported deterministic sort directions."""

    ASCENDING = "ascending"
    DESCENDING = "descending"


@dataclass(frozen=True, slots=True)
class WorkspaceQuery:
    """Structured query over persisted cognitive workspaces."""

    text: str | None = None
    statuses: tuple[WorkspaceStatus, ...] = ()
    hypothesis_statuses: tuple[HypothesisStatus, ...] = ()
    minimum_confidence: float | None = None
    maximum_confidence: float | None = None
    has_unresolved_questions: bool | None = None
    has_assumptions: bool | None = None
    updated_after: datetime | None = None
    updated_before: datetime | None = None
    sort_by: WorkspaceSortField = WorkspaceSortField.UPDATED_AT
    direction: SortDirection = SortDirection.DESCENDING
    limit: int | None = None

    def __post_init__(self) -> None:
        if self.minimum_confidence is not None:
            if not 0.0 <= self.minimum_confidence <= 1.0:
                raise ValueError(
                    "minimum_confidence must be between 0.0 and 1.0"
                )
        if self.maximum_confidence is not None:
            if not 0.0 <= self.maximum_confidence <= 1.0:
                raise ValueError(
                    "maximum_confidence must be between 0.0 and 1.0"
                )
        if (
            self.minimum_confidence is not None
            and self.maximum_confidence is not None
            and self.minimum_confidence > self.maximum_confidence
        ):
            raise ValueError(
                "minimum_confidence cannot exceed maximum_confidence"
            )
        if self.limit is not None and self.limit <= 0:
            raise ValueError("limit must be greater than zero")
        if self.updated_after is not None and self.updated_after.tzinfo is None:
            raise ValueError("updated_after must be timezone-aware")
        if self.updated_before is not None and self.updated_before.tzinfo is None:
            raise ValueError("updated_before must be timezone-aware")


@dataclass(frozen=True, slots=True)
class WorkspaceCatalogEntry:
    """Searchable summary of one cognitive workspace."""

    workspace_id: str
    objective: str
    status: WorkspaceStatus
    revision: int
    created_at: datetime
    updated_at: datetime
    hypothesis_count: int
    evidence_count: int
    assumption_count: int
    unresolved_question_count: int
    strongest_hypothesis_id: str | None
    strongest_confidence: float | None
    searchable_text: str

    @classmethod
    def from_workspace(
        cls,
        workspace: CognitiveWorkspace,
    ) -> "WorkspaceCatalogEntry":
        snapshot = workspace.snapshot()
        searchable_parts = [
            workspace.workspace_id,
            workspace.objective,
            *(item.statement for item in workspace.hypotheses),
            *(item.rationale for item in workspace.hypotheses),
            *(item.summary for item in workspace.evidence),
            *(item.statement for item in workspace.assumptions),
            *(item.prompt for item in workspace.questions),
            *(item.answer or "" for item in workspace.questions),
        ]
        searchable_text = "\n".join(
            part.strip()
            for part in searchable_parts
            if part and part.strip()
        ).casefold()

        return cls(
            workspace_id=workspace.workspace_id,
            objective=workspace.objective,
            status=workspace.status,
            revision=workspace.revision,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
            hypothesis_count=snapshot.hypothesis_count,
            evidence_count=snapshot.evidence_count,
            assumption_count=snapshot.assumption_count,
            unresolved_question_count=(
                snapshot.unresolved_question_count
            ),
            strongest_hypothesis_id=(
                snapshot.strongest_hypothesis_id
            ),
            strongest_confidence=snapshot.strongest_confidence,
            searchable_text=searchable_text,
        )


class CognitiveWorkspaceCatalog:
    """Deterministic searchable view over a workspace repository."""

    def __init__(
        self,
        repository: CognitiveWorkspaceRepository,
    ) -> None:
        self.repository = repository

    def rebuild(self) -> tuple[WorkspaceCatalogEntry, ...]:
        """Materialize the current catalog from repository state."""

        return tuple(
            WorkspaceCatalogEntry.from_workspace(
                self.repository.get(workspace_id)
            )
            for workspace_id in self.repository.list_ids()
        )

    def search(
        self,
        query: WorkspaceQuery | None = None,
    ) -> tuple[WorkspaceCatalogEntry, ...]:
        """Return deterministic entries matching the structured query."""

        resolved = query or WorkspaceQuery()
        entries = list(self.rebuild())
        entries = [
            entry
            for entry in entries
            if self._matches(entry, resolved)
        ]
        entries.sort(
            key=lambda entry: self._sort_key(entry, resolved.sort_by),
            reverse=resolved.direction == SortDirection.DESCENDING,
        )

        if resolved.limit is not None:
            entries = entries[: resolved.limit]

        return tuple(entries)

    def resumable(
        self,
        *,
        limit: int | None = None,
    ) -> tuple[WorkspaceCatalogEntry, ...]:
        """Return active workspaces suitable for resumption."""

        return self.search(
            WorkspaceQuery(
                statuses=(
                    WorkspaceStatus.OPEN,
                    WorkspaceStatus.SUSPENDED,
                ),
                sort_by=WorkspaceSortField.UPDATED_AT,
                direction=SortDirection.DESCENDING,
                limit=limit,
            )
        )

    def blocked(
        self,
        *,
        limit: int | None = None,
    ) -> tuple[WorkspaceCatalogEntry, ...]:
        """Return active workspaces with unresolved questions."""

        return self.search(
            WorkspaceQuery(
                statuses=(
                    WorkspaceStatus.OPEN,
                    WorkspaceStatus.SUSPENDED,
                ),
                has_unresolved_questions=True,
                sort_by=WorkspaceSortField.UPDATED_AT,
                direction=SortDirection.DESCENDING,
                limit=limit,
            )
        )

    def low_confidence(
        self,
        maximum_confidence: float,
        *,
        limit: int | None = None,
    ) -> tuple[WorkspaceCatalogEntry, ...]:
        """Return active workspaces whose strongest hypothesis is weak."""

        return self.search(
            WorkspaceQuery(
                statuses=(
                    WorkspaceStatus.OPEN,
                    WorkspaceStatus.SUSPENDED,
                ),
                maximum_confidence=maximum_confidence,
                sort_by=WorkspaceSortField.STRONGEST_CONFIDENCE,
                direction=SortDirection.ASCENDING,
                limit=limit,
            )
        )

    @staticmethod
    def _matches(
        entry: WorkspaceCatalogEntry,
        query: WorkspaceQuery,
    ) -> bool:
        if query.text is not None:
            terms = tuple(
                term.casefold()
                for term in query.text.split()
                if term.strip()
            )
            if not all(
                term in entry.searchable_text
                for term in terms
            ):
                return False

        if query.statuses and entry.status not in query.statuses:
            return False

        if query.updated_after is not None:
            if entry.updated_at < query.updated_after:
                return False

        if query.updated_before is not None:
            if entry.updated_at > query.updated_before:
                return False

        if query.has_unresolved_questions is not None:
            has_unresolved = entry.unresolved_question_count > 0
            if has_unresolved != query.has_unresolved_questions:
                return False

        if query.has_assumptions is not None:
            has_assumptions = entry.assumption_count > 0
            if has_assumptions != query.has_assumptions:
                return False

        if query.minimum_confidence is not None:
            if (
                entry.strongest_confidence is None
                or entry.strongest_confidence
                < query.minimum_confidence
            ):
                return False

        if query.maximum_confidence is not None:
            if (
                entry.strongest_confidence is None
                or entry.strongest_confidence
                > query.maximum_confidence
            ):
                return False

        return True

    def search_workspaces(
        self,
        query: WorkspaceQuery | None = None,
    ) -> tuple[CognitiveWorkspace, ...]:
        """Return full workspaces matching a catalog query."""

        return tuple(
            self.repository.get(entry.workspace_id)
            for entry in self.search(query)
        )

    @staticmethod
    def _sort_key(
        entry: WorkspaceCatalogEntry,
        field: WorkspaceSortField,
    ) -> tuple[object, str]:
        if field == WorkspaceSortField.UPDATED_AT:
            value: object = entry.updated_at
        elif field == WorkspaceSortField.CREATED_AT:
            value = entry.created_at
        elif field == WorkspaceSortField.OBJECTIVE:
            value = entry.objective.casefold()
        elif field == WorkspaceSortField.REVISION:
            value = entry.revision
        elif field == WorkspaceSortField.STRONGEST_CONFIDENCE:
            value = (
                -1.0
                if entry.strongest_confidence is None
                else entry.strongest_confidence
            )
        else:
            raise ValueError(f"unsupported sort field: {field}")

        return value, entry.workspace_id
