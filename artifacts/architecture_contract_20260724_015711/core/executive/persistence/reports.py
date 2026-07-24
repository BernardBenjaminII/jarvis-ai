from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

class IntegritySeverity(str, Enum):
    INFO='info'; WARNING='warning'; ERROR='error'; CRITICAL='critical'
class IntegrityCode(str, Enum):
    EMPTY_SESSION='empty_session'; DUPLICATE_SEQUENCE='duplicate_sequence'; SEQUENCE_GAP='sequence_gap'; INVALID_SEQUENCE='invalid_sequence'; PARENT_MISMATCH='parent_mismatch'; PAYLOAD_DIGEST_MISMATCH='payload_digest_mismatch'; CHECKPOINT_DIGEST_MISMATCH='checkpoint_digest_mismatch'; UNSUPPORTED_SCHEMA='unsupported_schema'; MALFORMED_CHECKPOINT='malformed_checkpoint'; REPOSITORY_ERROR='repository_error'
class IntegrityDisposition(str, Enum):
    TRUSTED='trusted'; RECOVERABLE='recoverable'; REQUIRES_MIGRATION='requires_migration'; QUARANTINE='quarantine'; UNRECOVERABLE='unrecoverable'

def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, default=str)
def fingerprint(value: Any) -> str:
    return sha256(canonical_json(value).encode()).hexdigest()

@dataclass(frozen=True, slots=True)
class IntegrityObservation:
    code: IntegrityCode
    session_id: str
    checkpoint_id: str|None=None
    sequence: int|None=None
    expected: str|int|None=None
    actual: str|int|None=None
    detail: str=''
    def canonical_dict(self):
        return {'actual':self.actual,'checkpoint_id':self.checkpoint_id,'code':self.code.value,'detail':self.detail,'expected':self.expected,'sequence':self.sequence,'session_id':self.session_id}

@dataclass(frozen=True, slots=True)
class IntegrityFinding:
    observation: IntegrityObservation
    severity: IntegritySeverity
    disposition: IntegrityDisposition
    def canonical_dict(self):
        return {'disposition':self.disposition.value,'observation':self.observation.canonical_dict(),'severity':self.severity.value}

@dataclass(frozen=True, slots=True)
class IntegrityReport:
    session_id: str
    checkpoints_examined: int
    findings: tuple[IntegrityFinding,...]
    repository_fingerprint: str
    certified: bool
    disposition: IntegrityDisposition
    report_fingerprint: str
    @property
    def errors(self):
        return tuple(f for f in self.findings if f.severity in {IntegritySeverity.ERROR, IntegritySeverity.CRITICAL})
    @property
    def warnings(self):
        return tuple(f for f in self.findings if f.severity is IntegritySeverity.WARNING)
    def canonical_dict(self, include_fingerprint=True):
        value={'certified':self.certified,'checkpoints_examined':self.checkpoints_examined,'disposition':self.disposition.value,'findings':[f.canonical_dict() for f in self.findings],'repository_fingerprint':self.repository_fingerprint,'session_id':self.session_id}
        if include_fingerprint: value['report_fingerprint']=self.report_fingerprint
        return value
    def verify_fingerprint(self):
        return fingerprint(self.canonical_dict(False)) == self.report_fingerprint

def build_report(*, session_id:str, checkpoints_examined:int, findings:Sequence[IntegrityFinding], repository_fingerprint:str, certified:bool, disposition:IntegrityDisposition):
    material={'certified':certified,'checkpoints_examined':checkpoints_examined,'disposition':disposition.value,'findings':[f.canonical_dict() for f in findings],'repository_fingerprint':repository_fingerprint,'session_id':session_id}
    return IntegrityReport(session_id,checkpoints_examined,tuple(findings),repository_fingerprint,certified,disposition,fingerprint(material))
