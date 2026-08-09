
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any


class IntegrationStatus(str, Enum):
    PASS = "pass"
    PARTIAL = "partial"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class IntegrationFinding:
    finding_id: str
    domain: str
    observable: str
    status: IntegrationStatus
    summary: str
    evidence: tuple[str, ...] = ()
    remediation: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


@dataclass(frozen=True, slots=True)
class IntegrationAuditReport:
    schema_version: str
    pack: str
    findings: tuple[IntegrationFinding, ...]
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        payload = {
            "schema_version": self.schema_version,
            "pack": self.pack,
            "findings": [finding.to_dict() for finding in self.findings],
        }
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        object.__setattr__(self, "fingerprint", sha256(encoded).hexdigest())

    @property
    def counts(self) -> dict[str, int]:
        counts = {status.value: 0 for status in IntegrationStatus}
        for finding in self.findings:
            counts[finding.status.value] += 1
        return counts

    @property
    def overall_status(self) -> IntegrationStatus:
        if self.counts["fail"]:
            return IntegrationStatus.FAIL
        if self.counts["partial"]:
            return IntegrationStatus.PARTIAL
        return IntegrationStatus.PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "pack": self.pack,
            "overall_status": self.overall_status.value,
            "counts": self.counts,
            "findings": [finding.to_dict() for finding in self.findings],
            "fingerprint": self.fingerprint,
        }
