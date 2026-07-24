"""Genesis IV-R1 Cognitive Object Model."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib, json
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid4

class CognitiveObjectError(ValueError): pass
class InvalidConfidenceError(CognitiveObjectError): pass
class InvalidObjectIdentifierError(CognitiveObjectError): pass

class CognitiveLifecycleState(str, Enum):
    CREATED='created'; ACTIVE='active'; SUPERSEDED='superseded'; RETIRED='retired'; REJECTED='rejected'

class CognitiveObjectKind(str, Enum):
    GENERIC='generic'; OBSERVATION='observation'; EVIDENCE='evidence'; CLAIM='claim'; RELATIONSHIP='relationship'; HYPOTHESIS='hypothesis'; INTERPRETATION='interpretation'; INFERENCE='inference'; JUSTIFICATION='justification'

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise CognitiveObjectError('timestamps must be timezone-aware')
    return value.astimezone(timezone.utc)

def _freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))

def _canonicalize(value: Any) -> Any:
    if isinstance(value, Enum): return value.value
    if isinstance(value, UUID): return str(value)
    if isinstance(value, datetime): return _normalize_datetime(value).isoformat()
    if isinstance(value, Mapping):
        return {str(k): _canonicalize(v) for k, v in sorted(value.items(), key=lambda p: str(p[0]))}
    if isinstance(value, (tuple, list)): return [_canonicalize(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None: return value
    raise TypeError(f'Unsupported canonical value: {type(value).__name__}')

@dataclass(frozen=True, slots=True)
class ProvenanceReference:
    source_id: str
    source_type: str
    locator: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self) -> None:
        if not self.source_id.strip(): raise CognitiveObjectError('source_id must not be empty')
        if not self.source_type.strip(): raise CognitiveObjectError('source_type must not be empty')
        object.__setattr__(self, 'metadata', _freeze_mapping(self.metadata))
    def to_primitive(self) -> dict[str, Any]:
        return {'source_id': self.source_id, 'source_type': self.source_type, 'locator': self.locator, 'metadata': _canonicalize(self.metadata)}

@dataclass(frozen=True, slots=True)
class CognitiveObject:
    object_id: UUID = field(default_factory=uuid4)
    kind: CognitiveObjectKind = CognitiveObjectKind.GENERIC
    created_at: datetime = field(default_factory=utc_now)
    confidence: float = 1.0
    lifecycle_state: CognitiveLifecycleState = CognitiveLifecycleState.CREATED
    provenance: tuple[ProvenanceReference, ...] = ()
    evidence_ids: tuple[UUID, ...] = ()
    justification_ids: tuple[UUID, ...] = ()
    authority: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self) -> None:
        if not isinstance(self.object_id, UUID): raise InvalidObjectIdentifierError('object_id must be a UUID')
        if not 0.0 <= float(self.confidence) <= 1.0: raise InvalidConfidenceError('confidence must be within [0.0, 1.0]')
        object.__setattr__(self, 'created_at', _normalize_datetime(self.created_at))
        object.__setattr__(self, 'confidence', float(self.confidence))
        object.__setattr__(self, 'provenance', tuple(self.provenance))
        object.__setattr__(self, 'evidence_ids', tuple(self.evidence_ids))
        object.__setattr__(self, 'justification_ids', tuple(self.justification_ids))
        object.__setattr__(self, 'attributes', _freeze_mapping(self.attributes))
    def to_primitive(self) -> dict[str, Any]:
        return {'object_id': str(self.object_id), 'kind': self.kind.value, 'created_at': self.created_at.isoformat(), 'confidence': self.confidence, 'lifecycle_state': self.lifecycle_state.value, 'provenance': [x.to_primitive() for x in self.provenance], 'evidence_ids': [str(x) for x in self.evidence_ids], 'justification_ids': [str(x) for x in self.justification_ids], 'authority': self.authority, 'attributes': _canonicalize(self.attributes)}
    def to_canonical_json(self) -> str:
        return json.dumps(self.to_primitive(), sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    @property
    def deterministic_hash(self) -> str:
        return hashlib.sha256(self.to_canonical_json().encode('utf-8')).hexdigest()

__all__=('CognitiveLifecycleState','CognitiveObject','CognitiveObjectError','CognitiveObjectKind','InvalidConfidenceError','InvalidObjectIdentifierError','ProvenanceReference','utc_now')
