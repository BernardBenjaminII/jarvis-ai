#!/usr/bin/env bash
set -euo pipefail

ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"
cd "$ROOT"

[[ -d core/executive/persistence ]] || { echo 'Run from the JARVIS repository root.'; exit 1; }
[[ -x "$PYTHON_BIN" ]] || { echo "Python not executable: $PYTHON_BIN"; exit 1; }

BACKUP=".migration_backups/genesis_vi_a65_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP" tests docs/architecture dev/verification dev
for f in core/executive/persistence/{__init__.py,recovery.py} tests/test_genesis_vi_a65_recovery_engine.py docs/architecture/genesis_vi_a65_executive_recovery_engine.md dev/verification/verify_genesis_vi_a65.py dev/verify_genesis_vi_a65.sh dev/demo_genesis_vi_a65.py; do
  if [[ -f "$f" ]]; then mkdir -p "$BACKUP/$(dirname "$f")"; cp "$f" "$BACKUP/$f"; fi
done

cat > core/executive/persistence/recovery.py <<'PY'
"""Genesis VI-A6.5 deterministic Executive recovery."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
from typing import Callable, Iterable, Protocol, Sequence

from .integrity import ExecutiveIntegrityEngine


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _hash(value: object) -> str:
    return sha256(_json(value).encode()).hexdigest()


def _value(value: object) -> object:
    return getattr(value, "value", value)


class RecoveryError(RuntimeError):
    pass


class RecoveryRefusedError(RecoveryError):
    pass


class RecoveryPointNotFoundError(RecoveryError):
    pass


class RecoveryReconstructionError(RecoveryError):
    pass


class RecoveryPolicyKind(str, Enum):
    LATEST_CERTIFIED = "latest_certified"
    LATEST_RECOVERABLE = "latest_recoverable"
    EXACT_SEQUENCE = "exact_sequence"
    EXACT_CHECKPOINT_ID = "exact_checkpoint_id"
    EXACT_FINGERPRINT = "exact_fingerprint"


class RecoveryStatus(str, Enum):
    RECOVERED = "recovered"
    REFUSED = "refused"
    NOT_FOUND = "not_found"
    RECONSTRUCTION_FAILED = "reconstruction_failed"


@dataclass(frozen=True, slots=True)
class RecoveryPolicy:
    kind: RecoveryPolicyKind = RecoveryPolicyKind.LATEST_CERTIFIED
    sequence: int | None = None
    checkpoint_id: str | None = None
    fingerprint: str | None = None

    def __post_init__(self) -> None:
        required = {
            RecoveryPolicyKind.EXACT_SEQUENCE: self.sequence,
            RecoveryPolicyKind.EXACT_CHECKPOINT_ID: self.checkpoint_id,
            RecoveryPolicyKind.EXACT_FINGERPRINT: self.fingerprint,
        }
        if self.kind in required and required[self.kind] in (None, ""):
            raise ValueError(f"{self.kind.value} requires its selector value.")
        if self.sequence is not None and self.kind is not RecoveryPolicyKind.EXACT_SEQUENCE:
            raise ValueError("sequence is valid only with exact_sequence.")
        if self.checkpoint_id is not None and self.kind is not RecoveryPolicyKind.EXACT_CHECKPOINT_ID:
            raise ValueError("checkpoint_id is valid only with exact_checkpoint_id.")
        if self.fingerprint is not None and self.kind is not RecoveryPolicyKind.EXACT_FINGERPRINT:
            raise ValueError("fingerprint is valid only with exact_fingerprint.")

    @classmethod
    def latest_certified(cls) -> "RecoveryPolicy": return cls()
    @classmethod
    def latest_recoverable(cls) -> "RecoveryPolicy": return cls(RecoveryPolicyKind.LATEST_RECOVERABLE)
    @classmethod
    def exact_sequence(cls, value: int) -> "RecoveryPolicy": return cls(RecoveryPolicyKind.EXACT_SEQUENCE, sequence=value)
    @classmethod
    def exact_checkpoint_id(cls, value: str) -> "RecoveryPolicy": return cls(RecoveryPolicyKind.EXACT_CHECKPOINT_ID, checkpoint_id=value)
    @classmethod
    def exact_fingerprint(cls, value: str) -> "RecoveryPolicy": return cls(RecoveryPolicyKind.EXACT_FINGERPRINT, fingerprint=value)

    def canonical_dict(self) -> dict[str, object]:
        return {"kind": self.kind.value, "sequence": self.sequence, "checkpoint_id": self.checkpoint_id, "fingerprint": self.fingerprint}


@dataclass(frozen=True, slots=True)
class RecoveryAuthorization:
    certified: bool
    disposition: str
    report_fingerprint: str
    checkpoints_examined: int
    findings_count: int

    @classmethod
    def from_report(cls, report: object) -> "RecoveryAuthorization":
        return cls(bool(getattr(report, "certified", False)), str(_value(getattr(report, "disposition", ""))), str(getattr(report, "report_fingerprint", "")), int(getattr(report, "checkpoints_examined", 0)), len(tuple(getattr(report, "findings", ()))))

    def canonical_dict(self) -> dict[str, object]:
        return {"certified": self.certified, "disposition": self.disposition, "report_fingerprint": self.report_fingerprint, "checkpoints_examined": self.checkpoints_examined, "findings_count": self.findings_count}


@dataclass(frozen=True, slots=True)
class RecoveryReport:
    session_id: str
    status: RecoveryStatus
    policy: RecoveryPolicy
    checkpoint_id: str | None
    sequence: int | None
    checkpoint_fingerprint: str | None
    authorization: RecoveryAuthorization
    used_prefix_fallback: bool
    detail: str
    state_fingerprint: str | None
    occurred_at: datetime
    report_fingerprint: str

    @classmethod
    def create(cls, **values: object) -> "RecoveryReport":
        occurred_at = values.pop("occurred_at", None) or datetime.now(timezone.utc)
        material = dict(values)
        material["status"] = _value(material["status"])
        material["policy"] = material["policy"].canonical_dict()
        material["authorization"] = material["authorization"].canonical_dict()
        material["occurred_at"] = occurred_at.isoformat()
        return cls(**values, occurred_at=occurred_at, report_fingerprint=_hash(material))

    def canonical_dict(self) -> dict[str, object]:
        return {"session_id": self.session_id, "status": self.status.value, "policy": self.policy.canonical_dict(), "checkpoint_id": self.checkpoint_id, "sequence": self.sequence, "checkpoint_fingerprint": self.checkpoint_fingerprint, "authorization": self.authorization.canonical_dict(), "used_prefix_fallback": self.used_prefix_fallback, "detail": self.detail, "state_fingerprint": self.state_fingerprint, "occurred_at": self.occurred_at.isoformat()}

    def verify_fingerprint(self) -> bool:
        return _hash(self.canonical_dict()) == self.report_fingerprint


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    state: object
    report: RecoveryReport


class CheckpointRepository(Protocol):
    def history(self, session_id: str) -> Iterable[object]: ...


class _PrefixRepository:
    def __init__(self, checkpoints: Sequence[object]) -> None: self._items = tuple(checkpoints)
    def history(self, session_id: str) -> tuple[object, ...]: return tuple(x for x in self._items if str(getattr(x, "session_id", "")) == session_id)


def _seq(cp: object) -> int: return int(getattr(cp, "sequence"))
def _id(cp: object) -> str: return str(getattr(cp, "checkpoint_id"))
def _fp(cp: object) -> str:
    for name in ("checkpoint_digest", "fingerprint", "digest"):
        if getattr(cp, name, None): return str(getattr(cp, name))
    canonical = getattr(cp, "canonical_dict", None)
    return _hash(canonical() if callable(canonical) else vars(cp))
def _payload(cp: object) -> object:
    if hasattr(cp, "payload"): return getattr(cp, "payload")
    raise RecoveryReconstructionError("Checkpoint exposes no payload.")


class ExecutiveRecoveryEngine:
    """Restores only integrity-certified checkpoint chains."""
    def __init__(self, repository: CheckpointRepository, *, integrity_engine: ExecutiveIntegrityEngine | None = None, integrity_policy: object | None = None, restorer: Callable[[object], object] | None = None) -> None:
        self.repository = repository
        self.integrity_policy = integrity_policy
        self.integrity_engine = integrity_engine or self._engine(repository)
        self.restorer = restorer or (lambda payload: payload)

    def _engine(self, repository: CheckpointRepository) -> ExecutiveIntegrityEngine:
        return ExecutiveIntegrityEngine(repository) if self.integrity_policy is None else ExecutiveIntegrityEngine(repository, policy=self.integrity_policy)

    def recover(self, session_id: str, *, policy: RecoveryPolicy | None = None) -> RecoveryResult:
        policy = policy or RecoveryPolicy.latest_certified()
        checkpoints = tuple(sorted(self.repository.history(session_id), key=_seq))
        if not checkpoints: raise RecoveryPointNotFoundError(f"No checkpoints for {session_id}.")
        checkpoint, integrity_report, fallback = self._select(session_id, checkpoints, policy)
        auth = RecoveryAuthorization.from_report(integrity_report)
        if checkpoint is None or not auth.certified:
            report = RecoveryReport.create(session_id=session_id, status=RecoveryStatus.REFUSED, policy=policy, checkpoint_id=None, sequence=None, checkpoint_fingerprint=None, authorization=auth, used_prefix_fallback=fallback, detail="Recovery refused: no certified recovery point satisfied policy.", state_fingerprint=None)
            raise RecoveryRefusedError(f"{report.detail} Report: {report.report_fingerprint}")
        try:
            state = self.restorer(_payload(checkpoint))
        except Exception as exc:
            raise RecoveryReconstructionError(type(exc).__name__) from exc
        report = RecoveryReport.create(session_id=session_id, status=RecoveryStatus.RECOVERED, policy=policy, checkpoint_id=_id(checkpoint), sequence=_seq(checkpoint), checkpoint_fingerprint=_fp(checkpoint), authorization=auth, used_prefix_fallback=fallback, detail="Executive state recovered from a certified checkpoint.", state_fingerprint=_hash(state))
        return RecoveryResult(state, report)

    def _select(self, session_id: str, checkpoints: Sequence[object], policy: RecoveryPolicy) -> tuple[object | None, object, bool]:
        if policy.kind is RecoveryPolicyKind.LATEST_CERTIFIED:
            report = self.integrity_engine.verify_session(session_id)
            return (checkpoints[-1] if report.certified else None), report, False
        if policy.kind is RecoveryPolicyKind.LATEST_RECOVERABLE:
            for end in range(len(checkpoints), 0, -1):
                report = self._engine(_PrefixRepository(checkpoints[:end])).verify_session(session_id)
                if report.certified: return checkpoints[end - 1], report, end != len(checkpoints)
            return None, self.integrity_engine.verify_session(session_id), False
        selected = next((cp for cp in checkpoints if (policy.kind is RecoveryPolicyKind.EXACT_SEQUENCE and _seq(cp) == policy.sequence) or (policy.kind is RecoveryPolicyKind.EXACT_CHECKPOINT_ID and _id(cp) == policy.checkpoint_id) or (policy.kind is RecoveryPolicyKind.EXACT_FINGERPRINT and _fp(cp) == policy.fingerprint)), None)
        if selected is None: return None, self.integrity_engine.verify_session(session_id), False
        end = checkpoints.index(selected) + 1
        report = self._engine(_PrefixRepository(checkpoints[:end])).verify_session(session_id)
        return (selected if report.certified else None), report, end != len(checkpoints)


__all__ = ["CheckpointRepository", "ExecutiveRecoveryEngine", "RecoveryAuthorization", "RecoveryError", "RecoveryPointNotFoundError", "RecoveryPolicy", "RecoveryPolicyKind", "RecoveryReconstructionError", "RecoveryRefusedError", "RecoveryReport", "RecoveryResult", "RecoveryStatus"]
PY

cat > tests/test_genesis_vi_a65_recovery_engine.py <<'PY'
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
PY

cat > docs/architecture/genesis_vi_a65_executive_recovery_engine.md <<'MD'
# Genesis VI-A6.5 — Executive Recovery Engine

**Status:** Implemented  
**Depends on:** Genesis VI-A6.4 Executive Integrity Engine

## Principle

Recovery never decides whether state is trustworthy. It obeys an Integrity Report.

```text
Repository → Integrity Certification → Recovery Policy → Reconstruction → Recovery Report
```

## Policies

- latest certified
- latest recoverable certified prefix
- exact sequence
- exact checkpoint identifier
- exact checkpoint fingerprint

A fallback is legal only when the complete prefix ending at the selected checkpoint is independently certified.

## Evidence

Each successful recovery records the selected checkpoint, policy, Integrity Report fingerprint, fallback status, recovered-state fingerprint, and Recovery Report fingerprint.

## Non-goals

Replay, schema migration, distributed reconciliation, external side-effect resumption, and session orchestration remain later phases.
MD

cat > dev/verification/verify_genesis_vi_a65.py <<'PY'
#!/usr/bin/env python3
from hashlib import sha256
from pathlib import Path
import inspect, sys
ROOT=Path(__file__).resolve().parents[2]
required=[ROOT/'core/executive/persistence/recovery.py',ROOT/'tests/test_genesis_vi_a65_recovery_engine.py',ROOT/'docs/architecture/genesis_vi_a65_executive_recovery_engine.md',ROOT/'dev/verify_genesis_vi_a65.sh']
for p in required:
    if not p.is_file(): raise SystemExit(f'[FAIL] Missing {p.relative_to(ROOT)}')
print('[PASS] Canonical Genesis VI-A6.5 structure')
sys.path.insert(0,str(ROOT))
from core.executive.persistence.recovery import ExecutiveRecoveryEngine,RecoveryPolicy,RecoveryReport,RecoveryResult
for symbol in (ExecutiveRecoveryEngine,RecoveryPolicy,RecoveryReport,RecoveryResult):
    if not inspect.isclass(symbol): raise SystemExit('[FAIL] Public API symbol')
print('[PASS] Stable recovery public API')
source=inspect.getsource(ExecutiveRecoveryEngine)
if 'verify_session' not in source or 'certified' not in source: raise SystemExit('[FAIL] Integrity authorization boundary')
print('[PASS] Recovery requires integrity authorization')
print('[PASS] Deterministic Engineering Constitution fingerprint',sha256(required[0].read_bytes()).hexdigest())
PY

cat > dev/verify_genesis_vi_a65.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
ROOT="${PROJECT_ROOT:-$(pwd)}"; PYTHON_BIN="${PYTHON_BIN:-/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python}"; cd "$ROOT"
failed=0
check(){ label="$1"; shift; if "$@"; then echo "[PASS] $label"; else echo "[FAIL] $label"; failed=$((failed+1)); fi; }
echo '========================================================================'
echo 'JARVIS — GENESIS VI-A6.5 EXECUTIVE RECOVERY ENGINE'
echo '========================================================================'
check 'Genesis VI-A6.5 package compilation' "$PYTHON_BIN" -m compileall -q core/executive/persistence/recovery.py
check 'Genesis VI-A6.5 unit tests' env PYTHONPATH="$ROOT" "$PYTHON_BIN" -m unittest -v tests.test_genesis_vi_a65_recovery_engine
check 'Genesis VI-A6.5 structural verification' env PYTHONPATH="$ROOT" "$PYTHON_BIN" dev/verification/verify_genesis_vi_a65.py
for f in dev/verify_genesis_vi_a64.sh dev/verify_genesis_vi_a63.sh dev/verify_genesis_vi_a62.sh dev/verify_genesis_vi_a61.sh; do [[ -x "$f" ]] && check "Regression: $(basename "$f")" env PYTHONPATH="$ROOT" PYTHON_BIN="$PYTHON_BIN" "$f" || true; done
echo '------------------------------------------------------------------------'; echo "Checks failed : $failed"; [[ $failed -eq 0 ]] && echo 'Overall status: EXCELLENT' || echo 'Overall status: FAILED'; echo '========================================================================'; exit "$failed"
SH

cat > dev/demo_genesis_vi_a65.py <<'PY'
#!/usr/bin/env python3
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from core.executive.persistence.recovery import ExecutiveRecoveryEngine,RecoveryPolicy,RecoveryRefusedError
SID='executive-recovery-demo'
def h(v): return sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
@dataclass(frozen=True,slots=True)
class CP: checkpoint_id:str; session_id:str; sequence:int; parent_digest:str|None; schema:str; payload:dict; payload_digest:str; checkpoint_digest:str
class Repo:
 def __init__(self,x): self.x=tuple(x)
 def history(self,s): return tuple(i for i in self.x if i.session_id==s)
def make(n,p):
 payload={'mission':'Demonstrate recovery','completed_steps':n,'status':'active'}; m={'checkpoint_id':f'checkpoint-{n:04d}','session_id':SID,'sequence':n,'parent_digest':p,'schema':'executive-state-v1','payload':payload,'payload_digest':h(payload)}; return CP(**m,checkpoint_digest=h(m))
def chain():
 a=make(1,None);b=make(2,a.checkpoint_digest);c=make(3,b.checkpoint_digest);return a,b,c
def show(title,r):
 p=r.report; print('\n'+'='*78+'\n'+title+'\n'+'='*78); print('Status                 :',p.status.value.upper()); print('Checkpoint             :',p.checkpoint_id); print('Sequence               :',p.sequence); print('Integrity certified    :',p.authorization.certified); print('Fallback used          :',p.used_prefix_fallback); print('Recovery fingerprint   :',p.report_fingerprint); print('Fingerprint valid      :',p.verify_fingerprint()); print('Recovered state        :',r.state)
def main():
 good=chain(); show('SCENARIO 1 — LATEST CERTIFIED',ExecutiveRecoveryEngine(Repo(good)).recover(SID)); bad=list(good);bad[-1]=replace(bad[-1],payload={'status':'tampered'})
 print('\n'+'='*78+'\nSCENARIO 2 — STRICT REFUSAL\n'+'='*78)
 try: ExecutiveRecoveryEngine(Repo(bad)).recover(SID)
 except RecoveryRefusedError as e: print('Status                 : REFUSED');print('Reason                 :',e)
 show('SCENARIO 3 — SAFE CERTIFIED FALLBACK',ExecutiveRecoveryEngine(Repo(bad)).recover(SID,policy=RecoveryPolicy.latest_recoverable()))
 show('SCENARIO 4 — EXACT OPERATOR SELECTION',ExecutiveRecoveryEngine(Repo(good)).recover(SID,policy=RecoveryPolicy.exact_sequence(1)))
 print('\n'+'='*78+'\nGENESIS VI-A6.5 TEST DRIVE COMPLETE\n'+'='*78)
if __name__=='__main__': main()
PY

chmod +x dev/verification/verify_genesis_vi_a65.py dev/verify_genesis_vi_a65.sh dev/demo_genesis_vi_a65.py

"$PYTHON_BIN" - <<'PY'
from pathlib import Path
p=Path('core/executive/persistence/__init__.py'); text=p.read_text() if p.exists() else ''
a='# BEGIN GENESIS VI-A6.5 RECOVERY EXPORTS'; b='# END GENESIS VI-A6.5 RECOVERY EXPORTS'
block='''# BEGIN GENESIS VI-A6.5 RECOVERY EXPORTS
from .recovery import (
    CheckpointRepository, ExecutiveRecoveryEngine, RecoveryAuthorization,
    RecoveryError, RecoveryPointNotFoundError, RecoveryPolicy,
    RecoveryPolicyKind, RecoveryReconstructionError, RecoveryRefusedError,
    RecoveryReport, RecoveryResult, RecoveryStatus,
)
# END GENESIS VI-A6.5 RECOVERY EXPORTS'''
if a in text and b in text: text=text.split(a)[0].rstrip()+'\n\n'+block+'\n'+text.split(b,1)[1].lstrip()
else: text=text.rstrip()+'\n\n'+block+'\n'
p.write_text(text)
PY

echo "Installed Genesis VI-A6.5. Backup: $BACKUP"
echo "Verify: PYTHON_BIN=$PYTHON_BIN ./dev/verify_genesis_vi_a65.sh"
echo "Demo:   PYTHONPATH=\"\$(pwd)\" $PYTHON_BIN dev/demo_genesis_vi_a65.py"
