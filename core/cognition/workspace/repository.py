"""Persistence contracts and SQLite repository for cognitive workspaces."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Protocol

from core.cognition.workspace.enums import (
    HypothesisStatus,
    WorkspaceEventKind,
    WorkspaceStatus,
)
from core.cognition.workspace.errors import CognitiveWorkspaceError
from core.cognition.workspace.models import (
    Assumption,
    CognitiveWorkspace,
    EvidenceReference,
    Hypothesis,
    OpenQuestion,
    WorkspaceEvent,
)


class CognitiveWorkspaceRepositoryError(CognitiveWorkspaceError):
    """Base repository failure."""


class CognitiveWorkspaceNotFoundError(CognitiveWorkspaceRepositoryError):
    """Raised when a requested workspace does not exist."""


class CognitiveWorkspaceConflictError(CognitiveWorkspaceRepositoryError):
    """Raised when optimistic revision checks fail."""


class CognitiveWorkspaceRepository(Protocol):
    """Persistence boundary for cognitive workspaces."""

    def save(
        self,
        workspace: CognitiveWorkspace,
        *,
        expected_revision: int | None = None,
    ) -> CognitiveWorkspace:
        """Persist a workspace and return the stored representation."""

    def get(self, workspace_id: str) -> CognitiveWorkspace:
        """Load one workspace by identity."""

    def exists(self, workspace_id: str) -> bool:
        """Return whether a workspace exists."""

    def list_ids(self) -> tuple[str, ...]:
        """Return stable workspace identities in lexical order."""

    def delete(
        self,
        workspace_id: str,
        *,
        expected_revision: int | None = None,
    ) -> None:
        """Delete one workspace, optionally with revision protection."""


class CognitiveWorkspaceCodec:
    """Canonical JSON codec for immutable workspace models."""

    VERSION = 1

    @classmethod
    def encode(cls, workspace: CognitiveWorkspace) -> str:
        payload = {
            "schema_version": cls.VERSION,
            "workspace_id": workspace.workspace_id,
            "objective": workspace.objective,
            "status": workspace.status.value,
            "revision": workspace.revision,
            "created_at": workspace.created_at.isoformat(),
            "updated_at": workspace.updated_at.isoformat(),
            "hypotheses": [
                {
                    "hypothesis_id": item.hypothesis_id,
                    "statement": item.statement,
                    "status": item.status.value,
                    "confidence": item.confidence,
                    "evidence_ids": list(item.evidence_ids),
                    "rationale": item.rationale,
                }
                for item in workspace.hypotheses
            ],
            "evidence": [
                {
                    "evidence_id": item.evidence_id,
                    "summary": item.summary,
                    "source_uri": item.source_uri,
                    "credibility": item.credibility,
                }
                for item in workspace.evidence
            ],
            "assumptions": [
                {
                    "assumption_id": item.assumption_id,
                    "statement": item.statement,
                    "confidence": item.confidence,
                    "challenged": item.challenged,
                }
                for item in workspace.assumptions
            ],
            "questions": [
                {
                    "question_id": item.question_id,
                    "prompt": item.prompt,
                    "priority": item.priority,
                    "resolved": item.resolved,
                    "answer": item.answer,
                }
                for item in workspace.questions
            ],
            "events": [
                {
                    "event_id": item.event_id,
                    "kind": item.kind.value,
                    "occurred_at": item.occurred_at.isoformat(),
                    "subject_id": item.subject_id,
                    "detail": item.detail,
                }
                for item in workspace.events
            ],
        }
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def decode(cls, serialized: str) -> CognitiveWorkspace:
        try:
            payload = json.loads(serialized)
        except json.JSONDecodeError as exc:
            raise CognitiveWorkspaceRepositoryError(
                "workspace payload is not valid JSON"
            ) from exc

        if payload.get("schema_version") != cls.VERSION:
            raise CognitiveWorkspaceRepositoryError(
                "unsupported workspace schema version"
            )

        try:
            return CognitiveWorkspace(
                workspace_id=payload["workspace_id"],
                objective=payload["objective"],
                status=WorkspaceStatus(payload["status"]),
                hypotheses=tuple(
                    Hypothesis(
                        hypothesis_id=item["hypothesis_id"],
                        statement=item["statement"],
                        status=HypothesisStatus(item["status"]),
                        confidence=item["confidence"],
                        evidence_ids=tuple(item["evidence_ids"]),
                        rationale=item["rationale"],
                    )
                    for item in payload["hypotheses"]
                ),
                evidence=tuple(
                    EvidenceReference(
                        evidence_id=item["evidence_id"],
                        summary=item["summary"],
                        source_uri=item["source_uri"],
                        credibility=item["credibility"],
                    )
                    for item in payload["evidence"]
                ),
                assumptions=tuple(
                    Assumption(
                        assumption_id=item["assumption_id"],
                        statement=item["statement"],
                        confidence=item["confidence"],
                        challenged=item["challenged"],
                    )
                    for item in payload["assumptions"]
                ),
                questions=tuple(
                    OpenQuestion(
                        question_id=item["question_id"],
                        prompt=item["prompt"],
                        priority=item["priority"],
                        resolved=item["resolved"],
                        answer=item["answer"],
                    )
                    for item in payload["questions"]
                ),
                events=tuple(
                    WorkspaceEvent(
                        event_id=item["event_id"],
                        kind=WorkspaceEventKind(item["kind"]),
                        occurred_at=datetime.fromisoformat(
                            item["occurred_at"]
                        ),
                        subject_id=item["subject_id"],
                        detail=item["detail"],
                    )
                    for item in payload["events"]
                ),
                revision=payload["revision"],
                created_at=datetime.fromisoformat(payload["created_at"]),
                updated_at=datetime.fromisoformat(payload["updated_at"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CognitiveWorkspaceRepositoryError(
                "workspace payload violates the canonical schema"
            ) from exc


class SQLiteCognitiveWorkspaceRepository:
    """SQLite implementation with optimistic revision protection."""

    SCHEMA_VERSION = 1

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS cognitive_workspace_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS cognitive_workspaces (
                    workspace_id TEXT PRIMARY KEY,
                    revision INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_cognitive_workspaces_status
                ON cognitive_workspaces(status)
                """
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO cognitive_workspace_metadata(
                    key,
                    value
                ) VALUES ('schema_version', ?)
                """,
                (str(self.SCHEMA_VERSION),),
            )
            stored = connection.execute(
                """
                SELECT value
                FROM cognitive_workspace_metadata
                WHERE key = 'schema_version'
                """
            ).fetchone()
            if stored is None or int(stored["value"]) != self.SCHEMA_VERSION:
                raise CognitiveWorkspaceRepositoryError(
                    "unsupported repository schema version"
                )

    def save(
        self,
        workspace: CognitiveWorkspace,
        *,
        expected_revision: int | None = None,
    ) -> CognitiveWorkspace:
        serialized = CognitiveWorkspaceCodec.encode(workspace)

        with self._connect() as connection:
            current = connection.execute(
                """
                SELECT revision
                FROM cognitive_workspaces
                WHERE workspace_id = ?
                """,
                (workspace.workspace_id,),
            ).fetchone()

            if current is None:
                if expected_revision is not None:
                    raise CognitiveWorkspaceConflictError(
                        "cannot apply expected_revision to a new workspace"
                    )
                connection.execute(
                    """
                    INSERT INTO cognitive_workspaces(
                        workspace_id,
                        revision,
                        status,
                        objective,
                        payload_json,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        workspace.workspace_id,
                        workspace.revision,
                        workspace.status.value,
                        workspace.objective,
                        serialized,
                        workspace.created_at.isoformat(),
                        workspace.updated_at.isoformat(),
                    ),
                )
                return workspace

            stored_revision = int(current["revision"])
            required_revision = (
                stored_revision
                if expected_revision is None
                else expected_revision
            )

            if stored_revision != required_revision:
                raise CognitiveWorkspaceConflictError(
                    "workspace revision conflict: "
                    f"expected {required_revision}, found {stored_revision}"
                )

            if workspace.revision <= stored_revision:
                raise CognitiveWorkspaceConflictError(
                    "replacement workspace must advance the stored revision"
                )

            cursor = connection.execute(
                """
                UPDATE cognitive_workspaces
                SET revision = ?,
                    status = ?,
                    objective = ?,
                    payload_json = ?,
                    created_at = ?,
                    updated_at = ?
                WHERE workspace_id = ?
                  AND revision = ?
                """,
                (
                    workspace.revision,
                    workspace.status.value,
                    workspace.objective,
                    serialized,
                    workspace.created_at.isoformat(),
                    workspace.updated_at.isoformat(),
                    workspace.workspace_id,
                    stored_revision,
                ),
            )
            if cursor.rowcount != 1:
                raise CognitiveWorkspaceConflictError(
                    "workspace changed during persistence"
                )
            return workspace

    def get(self, workspace_id: str) -> CognitiveWorkspace:
        normalized = workspace_id.strip()
        if not normalized:
            raise CognitiveWorkspaceRepositoryError(
                "workspace_id must not be empty"
            )

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT payload_json
                FROM cognitive_workspaces
                WHERE workspace_id = ?
                """,
                (normalized,),
            ).fetchone()

        if row is None:
            raise CognitiveWorkspaceNotFoundError(
                f"workspace not found: {normalized}"
            )
        return CognitiveWorkspaceCodec.decode(row["payload_json"])

    def exists(self, workspace_id: str) -> bool:
        normalized = workspace_id.strip()
        if not normalized:
            return False
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM cognitive_workspaces
                WHERE workspace_id = ?
                """,
                (normalized,),
            ).fetchone()
        return row is not None

    def list_ids(self) -> tuple[str, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT workspace_id
                FROM cognitive_workspaces
                ORDER BY workspace_id ASC
                """
            ).fetchall()
        return tuple(row["workspace_id"] for row in rows)

    def delete(
        self,
        workspace_id: str,
        *,
        expected_revision: int | None = None,
    ) -> None:
        normalized = workspace_id.strip()
        if not normalized:
            raise CognitiveWorkspaceRepositoryError(
                "workspace_id must not be empty"
            )

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT revision
                FROM cognitive_workspaces
                WHERE workspace_id = ?
                """,
                (normalized,),
            ).fetchone()

            if row is None:
                raise CognitiveWorkspaceNotFoundError(
                    f"workspace not found: {normalized}"
                )

            stored_revision = int(row["revision"])
            if (
                expected_revision is not None
                and stored_revision != expected_revision
            ):
                raise CognitiveWorkspaceConflictError(
                    "workspace revision conflict during delete"
                )

            connection.execute(
                """
                DELETE FROM cognitive_workspaces
                WHERE workspace_id = ?
                """,
                (normalized,),
            )
