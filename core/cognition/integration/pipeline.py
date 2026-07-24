"""Deterministic translation from integration contracts to workspace state."""

from __future__ import annotations

from core.cognition.integration.contracts import WorkspaceIntegrationRequest, stable_identifier
from core.cognition.integration.models import WorkspaceIntegrationResult
from core.cognition.workspace import (
    Assumption,
    CognitiveWorkspace,
    CognitiveWorkspaceService,
    EvidenceReference,
    Hypothesis,
    OpenQuestion,
)


class WorkspaceIntegrationPipeline:
    """Apply one request to a new or existing immutable workspace."""

    def __init__(self, service: CognitiveWorkspaceService | None = None) -> None:
        self._service = service or CognitiveWorkspaceService()

    def apply(
        self,
        request: WorkspaceIntegrationRequest,
        *,
        workspace: CognitiveWorkspace | None = None,
    ) -> WorkspaceIntegrationResult:
        created = workspace is None
        current = workspace or self._service.create_workspace(
            request.objective,
            workspace_id=request.workspace_id,
        )
        if current.objective != request.objective:
            raise ValueError("request objective does not match existing workspace")
        if request.workspace_id is not None and current.workspace_id != request.workspace_id:
            raise ValueError("request workspace_id does not match existing workspace")

        hypotheses_by_statement: dict[str, Hypothesis] = {
            item.statement: item for item in current.hypotheses
        }
        applied_hypotheses = 0
        applied_evidence = 0
        applied_assumptions = 0
        applied_questions = 0

        for seed in request.hypotheses:
            hypothesis = hypotheses_by_statement.get(seed.statement)
            if hypothesis is None:
                hypothesis = Hypothesis.create(
                    seed.statement,
                    confidence=seed.confidence,
                    rationale=seed.rationale,
                )
                current = self._service.add_hypothesis(current, hypothesis)
                hypotheses_by_statement[seed.statement] = hypothesis
                applied_hypotheses += 1

        existing_evidence_ids = {item.evidence_id for item in current.evidence}
        for seed in request.evidence:
            hypothesis = hypotheses_by_statement[seed.hypothesis_statement]
            evidence_id = seed.evidence_id or stable_identifier(
                "evr",
                seed.hypothesis_statement,
                seed.summary,
                seed.source_uri or "",
            )
            if evidence_id in existing_evidence_ids:
                continue
            evidence = EvidenceReference(
                evidence_id=evidence_id,
                summary=seed.summary,
                source_uri=seed.source_uri,
                credibility=seed.credibility,
            )
            current = self._service.attach_evidence(
                current,
                hypothesis.hypothesis_id,
                evidence,
            )
            existing_evidence_ids.add(evidence_id)
            applied_evidence += 1

        existing_assumptions = {item.statement for item in current.assumptions}
        for seed in request.assumptions:
            if seed.statement in existing_assumptions:
                continue
            current = self._service.add_assumption(
                current,
                Assumption.create(seed.statement, confidence=seed.confidence),
            )
            existing_assumptions.add(seed.statement)
            applied_assumptions += 1

        existing_questions = {item.prompt for item in current.questions}
        for seed in request.questions:
            if seed.prompt in existing_questions:
                continue
            current = self._service.open_question(
                current,
                OpenQuestion.create(seed.prompt, priority=seed.priority),
            )
            existing_questions.add(seed.prompt)
            applied_questions += 1

        return WorkspaceIntegrationResult(
            workspace=current,
            snapshot=current.snapshot(),
            created=created,
            persisted=False,
            applied_hypotheses=applied_hypotheses,
            applied_evidence=applied_evidence,
            applied_assumptions=applied_assumptions,
            applied_questions=applied_questions,
        )
