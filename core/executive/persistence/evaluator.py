from __future__ import annotations
from .policies import IntegrityPolicy
from .reports import IntegrityDisposition, IntegrityFinding, IntegritySeverity
RANK={IntegrityDisposition.TRUSTED:0,IntegrityDisposition.RECOVERABLE:1,IntegrityDisposition.REQUIRES_MIGRATION:2,IntegrityDisposition.QUARANTINE:3,IntegrityDisposition.UNRECOVERABLE:4}
class IntegrityEvaluator:
    def __init__(self, policy=None): self.policy=policy or IntegrityPolicy()
    def evaluate(self, observations):
        findings=tuple(IntegrityFinding(o,self.policy.severity_for(o.code),self.policy.disposition_for(o.code)) for o in observations)
        if not findings: return (),True,IntegrityDisposition.TRUSTED
        disposition=max((f.disposition for f in findings),key=RANK.get)
        blocking=any(f.severity in {IntegritySeverity.ERROR,IntegritySeverity.CRITICAL} for f in findings)
        empty_only=all(f.observation.code.value=='empty_session' for f in findings)
        return findings, (not blocking and (self.policy.allow_empty_session or not empty_only)), disposition
