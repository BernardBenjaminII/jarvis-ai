"""Validation for Genesis IV-A2 evidence objects."""

from __future__ import annotations

from .errors import CognitionValidationError
from .evidence import EvidenceRecord, make_evidence_id
from .evidence_chain import (
    EvidenceChain,
    EvidenceChainStatus,
    make_evidence_chain_id,
)
from .provenance import (
    ProvenanceRecord,
    make_provenance_id,
)


def validate_provenance_record(
    record: ProvenanceRecord,
) -> None:
    """Validate provenance structure and deterministic identity."""

    if not isinstance(record, ProvenanceRecord):
        raise CognitionValidationError(
            "Expected a ProvenanceRecord."
        )

    expected_id = make_provenance_id(record.identity_payload())

    if record.provenance_id != expected_id:
        raise CognitionValidationError(
            "Provenance identity verification failed."
        )

    if record.provenance_id in record.parent_provenance_ids:
        raise CognitionValidationError(
            "Provenance records may not directly parent themselves."
        )


def validate_evidence_record(
    record: EvidenceRecord,
) -> None:
    """Validate evidence structure and deterministic identity."""

    if not isinstance(record, EvidenceRecord):
        raise CognitionValidationError(
            "Expected an EvidenceRecord."
        )

    validate_provenance_record(record.provenance)

    expected_id = make_evidence_id(record.identity_payload())

    if record.evidence_id != expected_id:
        raise CognitionValidationError(
            "Evidence identity verification failed."
        )

    if len(record.observation_ids) != len(
        set(record.observation_ids)
    ):
        raise CognitionValidationError(
            "Evidence observation identifiers must be unique."
        )


def validate_evidence_chain(
    chain: EvidenceChain,
) -> None:
    """Validate an evidence chain and all contained evidence."""

    if not isinstance(chain, EvidenceChain):
        raise CognitionValidationError(
            "Expected an EvidenceChain."
        )

    for record in chain.evidence:
        validate_evidence_record(record)

    expected_id = make_evidence_chain_id(
        chain.identity_payload()
    )

    if chain.chain_id != expected_id:
        raise CognitionValidationError(
            "Evidence-chain identity verification failed."
        )

    evidence_ids = tuple(
        record.evidence_id
        for record in chain.evidence
    )

    if len(evidence_ids) != len(set(evidence_ids)):
        raise CognitionValidationError(
            "Evidence-chain records must be unique."
        )

    if (
        chain.status is EvidenceChainStatus.CONTESTED
        and not chain.is_contested
    ):
        raise CognitionValidationError(
            "A contested chain requires supporting and opposing evidence."
        )


def validate_evidence_object(value: object) -> None:
    """Dispatch validation for Genesis IV-A2 evidence objects."""

    if isinstance(value, ProvenanceRecord):
        validate_provenance_record(value)
        return

    if isinstance(value, EvidenceRecord):
        validate_evidence_record(value)
        return

    if isinstance(value, EvidenceChain):
        validate_evidence_chain(value)
        return

    raise CognitionValidationError(
        "Unsupported Genesis IV-A2 evidence object."
    )
