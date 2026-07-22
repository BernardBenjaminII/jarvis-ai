from __future__ import annotations
from dataclasses import dataclass
from .reports import IntegrityCode, IntegrityDisposition, IntegritySeverity

SEVERITY={
 IntegrityCode.EMPTY_SESSION:IntegritySeverity.WARNING,
 IntegrityCode.DUPLICATE_SEQUENCE:IntegritySeverity.CRITICAL,
 IntegrityCode.SEQUENCE_GAP:IntegritySeverity.ERROR,
 IntegrityCode.INVALID_SEQUENCE:IntegritySeverity.CRITICAL,
 IntegrityCode.PARENT_MISMATCH:IntegritySeverity.CRITICAL,
 IntegrityCode.PAYLOAD_DIGEST_MISMATCH:IntegritySeverity.CRITICAL,
 IntegrityCode.CHECKPOINT_DIGEST_MISMATCH:IntegritySeverity.CRITICAL,
 IntegrityCode.UNSUPPORTED_SCHEMA:IntegritySeverity.ERROR,
 IntegrityCode.MALFORMED_CHECKPOINT:IntegritySeverity.CRITICAL,
 IntegrityCode.REPOSITORY_ERROR:IntegritySeverity.CRITICAL,
}
DISPOSITION={
 IntegrityCode.EMPTY_SESSION:IntegrityDisposition.RECOVERABLE,
 IntegrityCode.UNSUPPORTED_SCHEMA:IntegrityDisposition.REQUIRES_MIGRATION,
 IntegrityCode.MALFORMED_CHECKPOINT:IntegrityDisposition.UNRECOVERABLE,
 IntegrityCode.REPOSITORY_ERROR:IntegrityDisposition.UNRECOVERABLE,
}
@dataclass(frozen=True, slots=True)
class IntegrityPolicy:
    supported_schemas: frozenset[str]=frozenset()
    allow_empty_session: bool=False
    sequence_origin: int=1
    def severity_for(self, code): return SEVERITY.get(code, IntegritySeverity.ERROR)
    def disposition_for(self, code): return DISPOSITION.get(code, IntegrityDisposition.QUARANTINE)
    def schema_supported(self, schema): return not self.supported_schemas or schema in self.supported_schemas
