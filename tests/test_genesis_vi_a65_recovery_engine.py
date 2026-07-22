from dataclasses import dataclass, replace
from hashlib import sha256
import json, unittest
from core.executive.persistence.recovery import ExecutiveRecoveryEngine, RecoveryPolicy, RecoveryRefusedError, RecoveryStatus

SID = "recovery-session"
def h(v): return sha256(json.dumps(v, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
@dataclass(frozen=True, slots=True)
class CP:
    checkpoint_id: str; session_id: str; sequence: int; parent_digest: str | None; schema: str; payload: dict; payload_digest: str; checkpoint_digest: str
class Repo:
    def __init__(self, items): self.items = tuple(items)
    def history(self, sid): return tuple(x for x in self.items if x.session_id == sid)
def cp(n, parent):
    payload = {"mission": "resume", "step": n}
    material = {"checkpoint_id": f"cp-{n}", "session_id": SID, "sequence": n, "parent_digest": parent, "schema": "executive-state-v1", "payload": payload, "payload_digest": h(payload)}
    return CP(**material, checkpoint_digest=h(material))
def chain():
    a=cp(1,None); b=cp(2,a.checkpoint_digest); c=cp(3,b.checkpoint_digest); return a,b,c

class Tests(unittest.TestCase):
    def test_latest(self):
        r=ExecutiveRecoveryEngine(Repo(chain())).recover(SID); self.assertEqual(r.state["step"],3); self.assertEqual(r.report.status,RecoveryStatus.RECOVERED); self.assertTrue(r.report.verify_fingerprint())
    def test_exact_sequence(self): self.assertEqual(ExecutiveRecoveryEngine(Repo(chain())).recover(SID,policy=RecoveryPolicy.exact_sequence(2)).state["step"],2)
    def test_exact_id(self): self.assertEqual(ExecutiveRecoveryEngine(Repo(chain())).recover(SID,policy=RecoveryPolicy.exact_checkpoint_id("cp-1")).state["step"],1)
    def test_exact_fingerprint(self):
        items=chain(); self.assertEqual(ExecutiveRecoveryEngine(Repo(items)).recover(SID,policy=RecoveryPolicy.exact_fingerprint(items[1].checkpoint_digest)).state["step"],2)
    def test_strict_refuses_tamper(self):
        items=list(chain()); items[-1]=replace(items[-1],payload={"step":999})
        with self.assertRaises(RecoveryRefusedError): ExecutiveRecoveryEngine(Repo(items)).recover(SID)
    def test_safe_fallback(self):
        items=list(chain()); items[-1]=replace(items[-1],payload={"step":999}); r=ExecutiveRecoveryEngine(Repo(items)).recover(SID,policy=RecoveryPolicy.latest_recoverable()); self.assertEqual(r.state["step"],2); self.assertTrue(r.report.used_prefix_fallback)
    def test_broken_middle_falls_to_first(self):
        items=list(chain()); items[1]=replace(items[1],parent_digest="bad"); r=ExecutiveRecoveryEngine(Repo(items)).recover(SID,policy=RecoveryPolicy.latest_recoverable()); self.assertEqual(r.state["step"],1)
    def test_restorer(self): self.assertEqual(ExecutiveRecoveryEngine(Repo(chain()),restorer=lambda p:(p["mission"],p["step"])).recover(SID).state,("resume",3))
    def test_deterministic_state_fingerprint(self):
        a=ExecutiveRecoveryEngine(Repo(chain())).recover(SID); b=ExecutiveRecoveryEngine(Repo(chain())).recover(SID); self.assertEqual(a.report.state_fingerprint,b.report.state_fingerprint)
    def test_policy_validation(self):
        with self.assertRaises(ValueError): RecoveryPolicy.exact_checkpoint_id("")
    def test_authorization_recorded(self): self.assertTrue(ExecutiveRecoveryEngine(Repo(chain())).recover(SID).report.authorization.certified)
if __name__ == "__main__": unittest.main()
