"""Genesis II-A4 constitutional tests for canonical Evidence contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from core.reasoning.evidence import (
    AssessmentMethod,
    BeliefMass,
    ClassificationLevel,
    EvidenceAssessment,
    EvidenceContent,
    EvidenceModality,
    EvidenceOrigin,
    EvidenceProvenance,
    EvidenceProvenanceStep,
    EvidenceRecord,
    EvidenceRelationship,
    EvidenceRelationshipError,
    EvidenceRelationshipType,
    EvidenceSourceType,
    EvidenceStatus,
    EvidenceStatusEvent,
    EvidenceTemporalError,
    EvidenceTemporalScope,
    EvidenceUncertainty,
    EvidenceUncertaintyError,
    EvidenceValidationError,
    UncertaintyKind,
    canonical_json,
)


FIXED_TIME = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)


def build_record(
    *,
    statement: str = "The observed system completed verification.",
    source_id: str = "verification-suite",
    observed_at: datetime = FIXED_TIME,
) -> EvidenceRecord:
    content = EvidenceContent(
        statement=statement,
        media_type="text/plain",
        language="en",
        attributes=(
            ("phase", "genesis-ii-a4"),
            ("domain", "reasoning"),
        ),
    )

    origin = EvidenceOrigin(
        source_type=EvidenceSourceType.TOOL,
        source_id=source_id,
        immediate_source_id="dev/verify_genesis_2a4.sh",
        origin_id="jarvis-repository",
        source_family_id="genesis-verification",
        collection_event_id="genesis-ii-a4-contract-test",
        dependency_group_ids=("local-runtime",),
    )

    provenance = EvidenceProvenance(
        steps=(
            EvidenceProvenanceStep(
                sequence=0,
                actor="pytest",
                mechanism="deterministic-fixture",
                input_ids=("genesis-ii-a4",),
                transformation="construct immutable Evidence fixture",
            ),
        )
    )

    temporal_scope = EvidenceTemporalScope(
        recorded_at=FIXED_TIME,
        observed_at=observed_at,
        valid_from=observed_at,
    )

    uncertainty = EvidenceUncertainty(
        kind=UncertaintyKind.PROBABILITY,
        probability=Decimal("0.95"),
    )

    return EvidenceRecord.create(
        content=content,
        origin=origin,
        provenance=provenance,
        temporal_scope=temporal_scope,
        uncertainty=uncertainty,
        modality=EvidenceModality.OBSERVATIONAL,
        status=EvidenceStatus.ACTIVE,
        classification=ClassificationLevel.INTERNAL,
        tags=("verification", "genesis"),
    )


def test_evidence_record_is_deterministic() -> None:
    first = build_record()
    second = build_record()

    assert first == second
    assert first.evidence_id == second.evidence_id
    assert canonical_json(first) == canonical_json(second)


def test_content_identity_is_distinct_from_record_identity() -> None:
    first = build_record(source_id="source-a")
    second = build_record(source_id="source-b")

    assert first.content.content_id == second.content.content_id
    assert first.evidence_id != second.evidence_id


def test_identical_content_does_not_imply_independent_corroboration() -> None:
    first = build_record(source_id="mirror-a")
    second = build_record(source_id="mirror-b")

    assert first.content.content_id == second.content.content_id

    relationship = EvidenceRelationship.create(
        source_evidence_id=first.evidence_id,
        target_evidence_id=second.evidence_id,
        relationship_type=EvidenceRelationshipType.SAME_ORIGIN_AS,
        rationale="Both records descend from one underlying report.",
    )

    assert relationship.source_evidence_id == first.evidence_id
    assert relationship.target_evidence_id == second.evidence_id
    assert (
        relationship.relationship_type
        is EvidenceRelationshipType.SAME_ORIGIN_AS
    )


def test_evidence_contracts_are_immutable() -> None:
    record = build_record()

    with pytest.raises(FrozenInstanceError):
        record.status = EvidenceStatus.SUPERSEDED  # type: ignore[misc]


def test_evidence_revision_uses_status_event() -> None:
    record = build_record()
    replacement = build_record(
        statement="The corrected system result completed verification."
    )

    event = EvidenceStatusEvent.create(
        evidence_id=record.evidence_id,
        previous_status=EvidenceStatus.ACTIVE,
        new_status=EvidenceStatus.SUPERSEDED,
        sequence=1,
        reason="A corrected Evidence record was admitted.",
        related_evidence_ids=(replacement.evidence_id,),
    )

    assert event.previous_status is EvidenceStatus.ACTIVE
    assert event.new_status is EvidenceStatus.SUPERSEDED
    assert event.related_evidence_ids == (replacement.evidence_id,)
    assert record.status is EvidenceStatus.ACTIVE


def test_assessment_is_context_specific() -> None:
    record = build_record()

    mission_assessment = EvidenceAssessment.create(
        evidence_id=record.evidence_id,
        reasoning_context_id="context:mission-alpha",
        assessor_id="reasoning-director",
        method=AssessmentMethod.RULE_BASED,
        sequence=0,
        rationale="Directly relevant to mission-alpha verification.",
        source_reliability="0.90",
        content_credibility="0.95",
        relevance="1.0",
        freshness="1.0",
        independence="0.80",
        diagnosticity="0.90",
    )

    unrelated_assessment = EvidenceAssessment.create(
        evidence_id=record.evidence_id,
        reasoning_context_id="context:mission-beta",
        assessor_id="reasoning-director",
        method=AssessmentMethod.RULE_BASED,
        sequence=0,
        rationale="The Evidence is not relevant to mission-beta.",
        source_reliability="0.90",
        content_credibility="0.95",
        relevance="0.05",
        freshness="1.0",
        independence="0.80",
        diagnosticity="0.05",
    )

    assert mission_assessment.evidence_id == unrelated_assessment.evidence_id
    assert mission_assessment.assessment_id != unrelated_assessment.assessment_id
    assert mission_assessment.relevance == Decimal("1")
    assert unrelated_assessment.relevance == Decimal("0.05")


def test_source_reliability_and_content_credibility_are_separate() -> None:
    record = build_record()

    assessment = EvidenceAssessment.create(
        evidence_id=record.evidence_id,
        reasoning_context_id="context:credibility-test",
        assessor_id="constitutional-test",
        method=AssessmentMethod.HUMAN_REVIEW,
        sequence=0,
        rationale="Reliable source, but content remains partly unverified.",
        source_reliability="0.95",
        content_credibility="0.60",
    )

    assert assessment.source_reliability == Decimal("0.95")
    assert assessment.content_credibility == Decimal("0.6")
    assert assessment.source_reliability != assessment.content_credibility


def test_uncertainty_is_typed() -> None:
    probability = EvidenceUncertainty(
        kind=UncertaintyKind.PROBABILITY,
        probability=Decimal("0.70"),
    )

    interval = EvidenceUncertainty(
        kind=UncertaintyKind.INTERVAL,
        lower_bound=Decimal("0.50"),
        upper_bound=Decimal("0.80"),
    )

    qualitative = EvidenceUncertainty(
        kind=UncertaintyKind.QUALITATIVE,
        qualitative_label="moderate",
    )

    likelihood = EvidenceUncertainty(
        kind=UncertaintyKind.LIKELIHOOD,
        likelihood=Decimal("3.5"),
    )

    belief_function = EvidenceUncertainty(
        kind=UncertaintyKind.BELIEF_FUNCTION,
        belief_masses=(
            BeliefMass(
                focal_set=("hypothesis-a",),
                mass=Decimal("0.6"),
            ),
            BeliefMass(
                focal_set=("hypothesis-a", "hypothesis-b"),
                mass=Decimal("0.4"),
            ),
        ),
    )

    assert probability.kind is UncertaintyKind.PROBABILITY
    assert interval.kind is UncertaintyKind.INTERVAL
    assert qualitative.kind is UncertaintyKind.QUALITATIVE
    assert likelihood.kind is UncertaintyKind.LIKELIHOOD
    assert belief_function.kind is UncertaintyKind.BELIEF_FUNCTION


def test_incompatible_uncertainty_values_are_rejected() -> None:
    with pytest.raises(EvidenceUncertaintyError):
        EvidenceUncertainty(
            kind=UncertaintyKind.PROBABILITY,
            probability=Decimal("0.75"),
            qualitative_label="high",
        )


def test_belief_function_mass_must_sum_to_one() -> None:
    with pytest.raises(EvidenceUncertaintyError):
        EvidenceUncertainty(
            kind=UncertaintyKind.BELIEF_FUNCTION,
            belief_masses=(
                BeliefMass(
                    focal_set=("hypothesis-a",),
                    mass=Decimal("0.4"),
                ),
                BeliefMass(
                    focal_set=("hypothesis-b",),
                    mass=Decimal("0.4"),
                ),
            ),
        )


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(EvidenceTemporalError):
        EvidenceTemporalScope(
            recorded_at=datetime(2026, 7, 20, 12, 0),
        )


def test_invalid_validity_interval_is_rejected() -> None:
    with pytest.raises(EvidenceTemporalError):
        EvidenceTemporalScope(
            recorded_at=FIXED_TIME,
            valid_from=FIXED_TIME,
            valid_until=FIXED_TIME - timedelta(seconds=1),
        )


def test_float_scores_are_rejected() -> None:
    record = build_record()

    with pytest.raises(EvidenceValidationError):
        EvidenceAssessment.create(
            evidence_id=record.evidence_id,
            reasoning_context_id="context:float-test",
            assessor_id="constitutional-test",
            method=AssessmentMethod.RULE_BASED,
            sequence=0,
            rationale="Floating point is not canonical.",
            relevance=0.5,
        )


def test_modality_is_explicit() -> None:
    observational = build_record()

    predictive = EvidenceRecord.create(
        content=observational.content,
        origin=observational.origin,
        provenance=observational.provenance,
        temporal_scope=observational.temporal_scope,
        uncertainty=observational.uncertainty,
        modality=EvidenceModality.PREDICTIVE,
        classification=observational.classification,
        tags=observational.tags,
    )

    assert observational.modality is EvidenceModality.OBSERVATIONAL
    assert predictive.modality is EvidenceModality.PREDICTIVE
    assert observational.evidence_id != predictive.evidence_id


def test_tag_order_does_not_change_identity() -> None:
    base = build_record()

    first = EvidenceRecord.create(
        content=base.content,
        origin=base.origin,
        provenance=base.provenance,
        temporal_scope=base.temporal_scope,
        uncertainty=base.uncertainty,
        modality=base.modality,
        tags=("alpha", "beta"),
    )

    second = EvidenceRecord.create(
        content=base.content,
        origin=base.origin,
        provenance=base.provenance,
        temporal_scope=base.temporal_scope,
        uncertainty=base.uncertainty,
        modality=base.modality,
        tags=("beta", "alpha"),
    )

    assert first.tags == ("alpha", "beta")
    assert first.evidence_id == second.evidence_id


def test_provenance_sequence_must_be_contiguous() -> None:
    with pytest.raises(EvidenceValidationError):
        EvidenceProvenance(
            steps=(
                EvidenceProvenanceStep(
                    sequence=1,
                    actor="test",
                    mechanism="invalid-sequence",
                ),
            )
        )


def test_public_contracts_do_not_execute_external_behavior() -> None:
    import core.reasoning.evidence.contracts as contracts
    import core.reasoning.evidence.identifiers as identifiers
    import core.reasoning.evidence.serialization as serialization

    prohibited_names = {
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "sqlite3",
        "sqlalchemy",
        "random",
        "uuid4",
    }

    loaded_names = (
        set(vars(contracts))
        | set(vars(identifiers))
        | set(vars(serialization))
    )

    assert prohibited_names.isdisjoint(loaded_names)


def test_assessment_validation_precedes_identity_generation() -> None:
    """Invalid assessment input must fail as validation, not serialization."""

    record = build_record()

    with pytest.raises(EvidenceValidationError):
        EvidenceAssessment.create(
            evidence_id=record.evidence_id,
            reasoning_context_id="context:validation-order",
            assessor_id="constitutional-test",
            method=AssessmentMethod.RULE_BASED,
            sequence=0,
            rationale="Invalid floating-point assessment.",
            relevance=0.5,
        )


def test_relationship_validation_precedes_identity_generation() -> None:
    """Invalid relationship input must fail before canonical hashing."""

    record = build_record()

    with pytest.raises(EvidenceRelationshipError):
        EvidenceRelationship.create(
            source_evidence_id=record.evidence_id,
            target_evidence_id=record.evidence_id,
            relationship_type=EvidenceRelationshipType.CORROBORATES,
        )


def test_record_validation_precedes_identity_generation() -> None:
    """Invalid record input must fail before canonical hashing."""

    valid = build_record()

    with pytest.raises(EvidenceValidationError):
        EvidenceRecord.create(
            content=valid.content,
            origin=valid.origin,
            provenance=valid.provenance,
            temporal_scope=valid.temporal_scope,
            uncertainty=valid.uncertainty,
            modality="observational",  # type: ignore[arg-type]
        )


def test_status_event_validation_precedes_identity_generation() -> None:
    """Invalid standing transition must fail before canonical hashing."""

    record = build_record()

    with pytest.raises(EvidenceValidationError):
        EvidenceStatusEvent.create(
            evidence_id=record.evidence_id,
            previous_status=EvidenceStatus.ACTIVE,
            new_status=EvidenceStatus.ACTIVE,
            sequence=0,
            reason="No standing change occurred.",
        )


def test_normalized_assessment_inputs_produce_same_identity() -> None:
    """Identity must derive from normalized values rather than raw spelling."""

    record = build_record()

    first = EvidenceAssessment.create(
        evidence_id=record.evidence_id,
        reasoning_context_id=" context:normalization-test ",
        assessor_id=" constitutional-test ",
        method=AssessmentMethod.RULE_BASED,
        sequence=0,
        rationale=" Normalized rationale. ",
        relevance="0.500",
    )

    second = EvidenceAssessment.create(
        evidence_id=record.evidence_id,
        reasoning_context_id="context:normalization-test",
        assessor_id="constitutional-test",
        method=AssessmentMethod.RULE_BASED,
        sequence=0,
        rationale="Normalized rationale.",
        relevance=Decimal("0.5"),
    )

    assert first.assessment_id == second.assessment_id
    assert first.relevance == Decimal("0.5")
    assert second.relevance == Decimal("0.5")


def test_normalized_relationship_inputs_produce_same_identity() -> None:
    """Relationship identity must use normalized rationale values."""

    source = build_record(source_id="source")
    target = build_record(
        statement="A second admissible Evidence record.",
        source_id="target",
    )

    first = EvidenceRelationship.create(
        source_evidence_id=source.evidence_id,
        target_evidence_id=target.evidence_id,
        relationship_type=EvidenceRelationshipType.CORROBORATES,
        rationale=" Independent corroboration. ",
    )

    second = EvidenceRelationship.create(
        source_evidence_id=source.evidence_id,
        target_evidence_id=target.evidence_id,
        relationship_type=EvidenceRelationshipType.CORROBORATES,
        rationale="Independent corroboration.",
    )

    assert first.relationship_id == second.relationship_id


def test_parent_order_does_not_change_record_identity() -> None:
    """Unordered parent input must normalize before record identity generation."""

    base = build_record()
    first_parent = build_record(
        statement="First parent Evidence.",
        source_id="parent-a",
    )
    second_parent = build_record(
        statement="Second parent Evidence.",
        source_id="parent-b",
    )

    first = EvidenceRecord.create(
        content=base.content,
        origin=base.origin,
        provenance=base.provenance,
        temporal_scope=base.temporal_scope,
        uncertainty=base.uncertainty,
        modality=base.modality,
        parent_evidence_ids=(
            first_parent.evidence_id,
            second_parent.evidence_id,
        ),
    )

    second = EvidenceRecord.create(
        content=base.content,
        origin=base.origin,
        provenance=base.provenance,
        temporal_scope=base.temporal_scope,
        uncertainty=base.uncertainty,
        modality=base.modality,
        parent_evidence_ids=(
            second_parent.evidence_id,
            first_parent.evidence_id,
        ),
    )

    assert first.parent_evidence_ids == second.parent_evidence_ids
    assert first.evidence_id == second.evidence_id


def test_related_evidence_order_does_not_change_event_identity() -> None:
    """Status-event identity must use normalized related-Evidence order."""

    record = build_record()
    first_related = build_record(
        statement="First related Evidence.",
        source_id="related-a",
    )
    second_related = build_record(
        statement="Second related Evidence.",
        source_id="related-b",
    )

    first = EvidenceStatusEvent.create(
        evidence_id=record.evidence_id,
        previous_status=EvidenceStatus.ACTIVE,
        new_status=EvidenceStatus.SUPERSEDED,
        sequence=1,
        reason="Replacement Evidence was admitted.",
        related_evidence_ids=(
            first_related.evidence_id,
            second_related.evidence_id,
        ),
    )

    second = EvidenceStatusEvent.create(
        evidence_id=record.evidence_id,
        previous_status=EvidenceStatus.ACTIVE,
        new_status=EvidenceStatus.SUPERSEDED,
        sequence=1,
        reason="Replacement Evidence was admitted.",
        related_evidence_ids=(
            second_related.evidence_id,
            first_related.evidence_id,
        ),
    )

    assert first.related_evidence_ids == second.related_evidence_ids
    assert first.event_id == second.event_id
