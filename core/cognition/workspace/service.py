"""Deterministic operations over immutable cognitive workspaces."""

from __future__ import annotations

from dataclasses import replace

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


class CognitiveWorkspaceService:
    """Application service for explicit reasoning-state transitions."""

    def create_workspace(
        self,
        objective: str,
        *,
        workspace_id: str | None = None,
    ) -> CognitiveWorkspace:
        return CognitiveWorkspace.create(
            objective,
            workspace_id=workspace_id,
        )

    def add_hypothesis(
        self,
        workspace: CognitiveWorkspace,
        hypothesis: Hypothesis,
    ) -> CognitiveWorkspace:
        self._require_open(workspace)

        if any(
            item.hypothesis_id == hypothesis.hypothesis_id
            for item in workspace.hypotheses
        ):
            raise CognitiveWorkspaceError(
                f"hypothesis already exists: {hypothesis.hypothesis_id}"
            )

        event = WorkspaceEvent.create(
            WorkspaceEventKind.HYPOTHESIS_ADDED,
            hypothesis.hypothesis_id,
            hypothesis.statement,
        )
        return workspace.evolve(
            hypotheses=(*workspace.hypotheses, hypothesis),
            events=(*workspace.events, event),
        )

    def attach_evidence(
        self,
        workspace: CognitiveWorkspace,
        hypothesis_id: str,
        evidence: EvidenceReference,
    ) -> CognitiveWorkspace:
        self._require_open(workspace)

        if any(
            item.evidence_id == evidence.evidence_id
            for item in workspace.evidence
        ):
            raise CognitiveWorkspaceError(
                f"evidence already exists: {evidence.evidence_id}"
            )

        updated_hypotheses: list[Hypothesis] = []
        found = False

        for hypothesis in workspace.hypotheses:
            if hypothesis.hypothesis_id == hypothesis_id:
                updated_hypotheses.append(
                    hypothesis.attach_evidence(evidence.evidence_id)
                )
                found = True
            else:
                updated_hypotheses.append(hypothesis)

        if not found:
            raise CognitiveWorkspaceError(
                f"unknown hypothesis: {hypothesis_id}"
            )

        event = WorkspaceEvent.create(
            WorkspaceEventKind.EVIDENCE_ATTACHED,
            evidence.evidence_id,
            f"Attached to hypothesis {hypothesis_id}",
        )
        return workspace.evolve(
            hypotheses=tuple(updated_hypotheses),
            evidence=(*workspace.evidence, evidence),
            events=(*workspace.events, event),
        )

    def transition_hypothesis(
        self,
        workspace: CognitiveWorkspace,
        hypothesis_id: str,
        status: HypothesisStatus,
        *,
        confidence: float | None = None,
        rationale: str | None = None,
    ) -> CognitiveWorkspace:
        self._require_open(workspace)

        updated: list[Hypothesis] = []
        found = False

        for hypothesis in workspace.hypotheses:
            if hypothesis.hypothesis_id == hypothesis_id:
                updated.append(
                    hypothesis.transition(
                        status,
                        confidence=confidence,
                        rationale=rationale,
                    )
                )
                found = True
            else:
                updated.append(hypothesis)

        if not found:
            raise CognitiveWorkspaceError(
                f"unknown hypothesis: {hypothesis_id}"
            )

        event = WorkspaceEvent.create(
            WorkspaceEventKind.HYPOTHESIS_STATUS_CHANGED,
            hypothesis_id,
            f"Hypothesis transitioned to {status.value}",
        )
        return workspace.evolve(
            hypotheses=tuple(updated),
            events=(*workspace.events, event),
        )

    def add_assumption(
        self,
        workspace: CognitiveWorkspace,
        assumption: Assumption,
    ) -> CognitiveWorkspace:
        self._require_open(workspace)

        if any(
            item.assumption_id == assumption.assumption_id
            for item in workspace.assumptions
        ):
            raise CognitiveWorkspaceError(
                f"assumption already exists: {assumption.assumption_id}"
            )

        event = WorkspaceEvent.create(
            WorkspaceEventKind.ASSUMPTION_ADDED,
            assumption.assumption_id,
            assumption.statement,
        )
        return workspace.evolve(
            assumptions=(*workspace.assumptions, assumption),
            events=(*workspace.events, event),
        )

    def open_question(
        self,
        workspace: CognitiveWorkspace,
        question: OpenQuestion,
    ) -> CognitiveWorkspace:
        self._require_open(workspace)

        if any(
            item.question_id == question.question_id
            for item in workspace.questions
        ):
            raise CognitiveWorkspaceError(
                f"question already exists: {question.question_id}"
            )

        event = WorkspaceEvent.create(
            WorkspaceEventKind.QUESTION_OPENED,
            question.question_id,
            question.prompt,
        )
        return workspace.evolve(
            questions=(*workspace.questions, question),
            events=(*workspace.events, event),
        )

    def resolve_question(
        self,
        workspace: CognitiveWorkspace,
        question_id: str,
        answer: str,
    ) -> CognitiveWorkspace:
        self._require_open(workspace)

        updated: list[OpenQuestion] = []
        found = False

        for question in workspace.questions:
            if question.question_id == question_id:
                if question.resolved:
                    raise CognitiveWorkspaceError(
                        f"question already resolved: {question_id}"
                    )
                updated.append(question.resolve(answer))
                found = True
            else:
                updated.append(question)

        if not found:
            raise CognitiveWorkspaceError(
                f"unknown question: {question_id}"
            )

        event = WorkspaceEvent.create(
            WorkspaceEventKind.QUESTION_RESOLVED,
            question_id,
            answer,
        )
        return workspace.evolve(
            questions=tuple(updated),
            events=(*workspace.events, event),
        )

    def set_workspace_status(
        self,
        workspace: CognitiveWorkspace,
        status: WorkspaceStatus,
        *,
        detail: str,
    ) -> CognitiveWorkspace:
        if workspace.status == status:
            return workspace

        normalized_detail = detail.strip()
        if not normalized_detail:
            raise CognitiveWorkspaceError(
                "workspace status transitions require detail"
            )

        if workspace.status in {
            WorkspaceStatus.RESOLVED,
            WorkspaceStatus.ABANDONED,
        }:
            raise CognitiveWorkspaceError(
                "terminal workspaces cannot transition"
            )

        event = WorkspaceEvent.create(
            WorkspaceEventKind.WORKSPACE_STATUS_CHANGED,
            workspace.workspace_id,
            normalized_detail,
        )
        return workspace.evolve(
            status=status,
            events=(*workspace.events, event),
        )

    @staticmethod
    def _require_open(
        workspace: CognitiveWorkspace,
    ) -> None:
        if workspace.status != WorkspaceStatus.OPEN:
            raise CognitiveWorkspaceError(
                "workspace operation requires open status"
            )
