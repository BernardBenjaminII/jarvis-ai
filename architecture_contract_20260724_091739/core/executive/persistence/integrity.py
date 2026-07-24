from __future__ import annotations
from .evaluator import IntegrityEvaluator
from .policies import IntegrityPolicy
from .reports import build_report
from .scanner import IntegrityScanner
class ExecutiveIntegrityEngine:
    def __init__(self, repository, *, policy=None):
        self.policy=policy or IntegrityPolicy(); self.scanner=IntegrityScanner(repository,policy=self.policy); self.evaluator=IntegrityEvaluator(self.policy)
    def verify_session(self, session_id):
        checkpoints,observations,repo_fingerprint=self.scanner.scan_session(session_id)
        findings,certified,disposition=self.evaluator.evaluate(observations)
        return build_report(session_id=session_id,checkpoints_examined=len(checkpoints),findings=findings,repository_fingerprint=repo_fingerprint,certified=certified,disposition=disposition)
IntegrityEngine=ExecutiveIntegrityEngine
def verify_session(repository,session_id,*,policy=None): return ExecutiveIntegrityEngine(repository,policy=policy).verify_session(session_id)
