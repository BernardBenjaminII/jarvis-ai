#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "$PROJECT_ROOT"

[[ -d core/executive/persistence ]] || { echo '[FAIL] Missing VI-A6 persistence package'; exit 1; }
mkdir -p core/executive/persistence tests docs/architecture dev/verification

cat > core/executive/persistence/reports.py <<'PY'
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
PY

cat > core/executive/persistence/policies.py <<'PY'
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
PY

cat > core/executive/persistence/scanner.py <<'PY'
from __future__ import annotations
from dataclasses import asdict, is_dataclass
from hashlib import sha256
from typing import Any, Mapping, Protocol, Sequence
from .policies import IntegrityPolicy
from .reports import IntegrityCode, IntegrityObservation, canonical_json, fingerprint

class CheckpointRepositoryProtocol(Protocol):
    def history(self, session_id:str)->Sequence[Any]: ...

def read(obj,*names,default=None):
    for name in names:
        if isinstance(obj,Mapping) and name in obj: return obj[name]
        if hasattr(obj,name): return getattr(obj,name)
    return default

def mapping(obj):
    if isinstance(obj,Mapping): return dict(obj)
    if hasattr(obj,'canonical_dict'): return dict(obj.canonical_dict())
    if is_dataclass(obj): return asdict(obj)
    if hasattr(obj,'to_dict'): return dict(obj.to_dict())
    if hasattr(obj,'__dict__'): return dict(vars(obj))
    raise TypeError(f'Unsupported checkpoint: {type(obj)!r}')

def seq(c):
    raw=read(c,'sequence','sequence_number','ordinal','index')
    try: return int(raw)
    except (TypeError,ValueError): return None

def cid(c):
    raw=read(c,'checkpoint_id','id','record_id'); return None if raw is None else str(raw)
def cdigest(c):
    raw=read(c,'checkpoint_digest','digest','fingerprint','integrity_digest'); return None if raw is None else str(raw)
def parent(c):
    raw=read(c,'parent_digest','previous_digest','parent_checkpoint_digest','previous_checkpoint_digest'); return None if raw in (None,'') else str(raw)
def schema(c):
    raw=read(c,'schema','schema_name','schema_version'); return None if raw is None else str(raw)
def payload(c): return read(c,'payload','snapshot','state','serialized_snapshot')
def pdigest(c):
    raw=read(c,'payload_digest','snapshot_digest','payload_fingerprint'); return None if raw is None else str(raw)
def hash_payload(value):
    data=value if isinstance(value,bytes) else (value.encode() if isinstance(value,str) else canonical_json(value).encode())
    return sha256(data).hexdigest()
def hash_checkpoint(c):
    m=mapping(c)
    for key in ('checkpoint_digest','digest','fingerprint','integrity_digest'): m.pop(key,None)
    return sha256(canonical_json(m).encode()).hexdigest()

class IntegrityScanner:
    def __init__(self, repository, *, policy=None):
        self.repository=repository; self.policy=policy or IntegrityPolicy()
    def scan_session(self, session_id):
        try: checkpoints=tuple(self.repository.history(session_id))
        except Exception as exc:
            obs=IntegrityObservation(IntegrityCode.REPOSITORY_ERROR,session_id,detail=f'{type(exc).__name__}: {exc}')
            return (), (obs,), fingerprint([])
        if not checkpoints:
            return (), (IntegrityObservation(IntegrityCode.EMPTY_SESSION,session_id,detail='No checkpoints found.'),), fingerprint([])
        observations=[]; indexed=[]
        for c in checkpoints:
            s=seq(c)
            if s is None:
                observations.append(IntegrityObservation(IntegrityCode.INVALID_SEQUENCE,session_id,cid(c),detail='Sequence missing or invalid.'))
            else: indexed.append((s,c))
        indexed.sort(key=lambda x:(x[0],cid(x[1]) or ''))
        expected=self.policy.sequence_origin; seen=set(); previous=None
        for s,c in indexed:
            if s in seen: observations.append(IntegrityObservation(IntegrityCode.DUPLICATE_SEQUENCE,session_id,cid(c),s,actual=s,detail='Duplicate sequence.'))
            seen.add(s)
            if s != expected:
                observations.append(IntegrityObservation(IntegrityCode.SEQUENCE_GAP,session_id,cid(c),s,expected,s,'Sequence discontinuity.'))
                expected=s
            expected += 1
            actual_parent=parent(c)
            if previous is None and actual_parent is not None:
                observations.append(IntegrityObservation(IntegrityCode.PARENT_MISMATCH,session_id,cid(c),s,None,actual_parent,'First checkpoint has a parent.'))
            elif previous is not None and actual_parent != previous:
                observations.append(IntegrityObservation(IntegrityCode.PARENT_MISMATCH,session_id,cid(c),s,previous,actual_parent,'Parent digest mismatch.'))
            if not self.policy.schema_supported(schema(c)):
                observations.append(IntegrityObservation(IntegrityCode.UNSUPPORTED_SCHEMA,session_id,cid(c),s,','.join(sorted(self.policy.supported_schemas)),schema(c),'Unsupported schema.'))
            p=payload(c); declared=pdigest(c)
            if p is not None and declared is not None:
                actual=hash_payload(p)
                if actual != declared: observations.append(IntegrityObservation(IntegrityCode.PAYLOAD_DIGEST_MISMATCH,session_id,cid(c),s,declared,actual,'Payload digest mismatch.'))
            declared_checkpoint=cdigest(c)
            if declared_checkpoint is not None:
                try: actual_checkpoint=hash_checkpoint(c)
                except Exception as exc: observations.append(IntegrityObservation(IntegrityCode.MALFORMED_CHECKPOINT,session_id,cid(c),s,detail=f'{type(exc).__name__}: {exc}'))
                else:
                    if actual_checkpoint != declared_checkpoint: observations.append(IntegrityObservation(IntegrityCode.CHECKPOINT_DIGEST_MISMATCH,session_id,cid(c),s,declared_checkpoint,actual_checkpoint,'Checkpoint digest mismatch.'))
            previous=declared_checkpoint
        items=[{'sequence':s,'checkpoint_id':cid(c),'checkpoint_digest':cdigest(c),'parent_digest':parent(c)} for s,c in indexed]
        return tuple(c for _,c in indexed), tuple(observations), fingerprint(items)
PY

cat > core/executive/persistence/evaluator.py <<'PY'
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
PY

cat > core/executive/persistence/integrity.py <<'PY'
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
PY

"$PYTHON_BIN" - <<'PY'
from pathlib import Path
path=Path('core/executive/persistence/__init__.py')
text=path.read_text() if path.exists() else ''
marker='# Genesis VI-A6.4 public API'
block='''\n# Genesis VI-A6.4 public API\nfrom .evaluator import IntegrityEvaluator\nfrom .integrity import ExecutiveIntegrityEngine, IntegrityEngine, verify_session\nfrom .policies import IntegrityPolicy\nfrom .reports import IntegrityCode, IntegrityDisposition, IntegrityFinding, IntegrityObservation, IntegrityReport, IntegritySeverity\nfrom .scanner import CheckpointRepositoryProtocol, IntegrityScanner\n'''
if marker not in text:
    path.write_text(text.rstrip()+block+'\n')
PY

cat > tests/test_genesis_vi_a64_integrity_engine.py <<'PY'
from dataclasses import dataclass, replace
from hashlib import sha256
import json, unittest
from core.executive.persistence import ExecutiveIntegrityEngine, IntegrityCode, IntegrityDisposition, IntegrityPolicy

def canon(v): return json.dumps(v,sort_keys=True,separators=(',',':'))
def hp(v): return sha256(canon(v).encode()).hexdigest()
@dataclass(frozen=True)
class CP:
    checkpoint_id:str; session_id:str; sequence:int; parent_digest:str|None; schema:str; payload:dict; payload_digest:str; checkpoint_digest:str
    def canonical_dict(self): return self.__dict__.copy()
def make(sequence,parent_digest=None,payload=None,schema='v1'):
    payload=payload or {'sequence':sequence}
    material={'checkpoint_id':f'cp-{sequence}','session_id':'s1','sequence':sequence,'parent_digest':parent_digest,'schema':schema,'payload':payload,'payload_digest':hp(payload)}
    return CP(**material,checkpoint_digest=sha256(canon(material).encode()).hexdigest())
def chain(n=3):
    out=[]; parent=None
    for i in range(1,n+1):
        c=make(i,parent); out.append(c); parent=c.checkpoint_digest
    return tuple(out)
class Repo:
    def __init__(self,items): self.items=tuple(items)
    def history(self,session_id): return tuple(x for x in self.items if x.session_id==session_id)
class Broken:
    def history(self,session_id): raise OSError('unavailable')
class Tests(unittest.TestCase):
    def report(self,items,policy=None): return ExecutiveIntegrityEngine(Repo(items),policy=policy).verify_session('s1')
    def test_valid_chain(self):
        r=self.report(chain()); self.assertTrue(r.certified); self.assertEqual(r.disposition,IntegrityDisposition.TRUSTED); self.assertTrue(r.verify_fingerprint())
    def test_gap(self):
        a,b,c=chain(); r=self.report((a,replace(c,sequence=4))); self.assertIn(IntegrityCode.SEQUENCE_GAP,{f.observation.code for f in r.findings})
    def test_duplicate(self):
        a,b,_=chain(); r=self.report((a,b,replace(b,checkpoint_id='dup'))); self.assertIn(IntegrityCode.DUPLICATE_SEQUENCE,{f.observation.code for f in r.findings})
    def test_parent(self):
        x=list(chain()); x[1]=replace(x[1],parent_digest='bad'); r=self.report(x); self.assertIn(IntegrityCode.PARENT_MISMATCH,{f.observation.code for f in r.findings})
    def test_payload(self):
        x=list(chain()); x[1]=replace(x[1],payload={'bad':True}); r=self.report(x); self.assertIn(IntegrityCode.PAYLOAD_DIGEST_MISMATCH,{f.observation.code for f in r.findings})
    def test_checkpoint(self):
        x=list(chain()); x[1]=replace(x[1],schema='changed'); r=self.report(x); self.assertIn(IntegrityCode.CHECKPOINT_DIGEST_MISMATCH,{f.observation.code for f in r.findings})
    def test_schema(self):
        r=self.report(chain(),IntegrityPolicy(supported_schemas=frozenset({'v2'}))); self.assertEqual(r.disposition,IntegrityDisposition.REQUIRES_MIGRATION)
    def test_empty_default(self): self.assertFalse(self.report(()).certified)
    def test_empty_allowed(self): self.assertTrue(self.report((),IntegrityPolicy(allow_empty_session=True)).certified)
    def test_repository_failure(self): self.assertEqual(ExecutiveIntegrityEngine(Broken()).verify_session('s1').disposition,IntegrityDisposition.UNRECOVERABLE)
    def test_deterministic_report(self):
        e=ExecutiveIntegrityEngine(Repo(chain())); self.assertEqual(e.verify_session('s1').report_fingerprint,e.verify_session('s1').report_fingerprint)
if __name__=='__main__': unittest.main()
PY

cat > docs/architecture/genesis_vi_a64_executive_integrity_engine.md <<'MD'
# Genesis VI-A6.4 — Executive Integrity Engine

**Status:** Implemented  
**Authority:** ADR-0023 — Executive Evidence and Trust Model

## Constitutional Law

> No executive state shall be restored, replayed, or acted upon unless its checkpoint history has been verified for integrity, ordering, provenance, and continuity.

## Architecture

```text
Checkpoint Repository
        ↓
Integrity Scanner
        ↓
Integrity Evaluator
        ↓
Immutable Integrity Report
        ↓
Recovery / Replay
```

The scanner records facts without policy judgments. The evaluator maps facts to severity and disposition. The report is immutable, deterministic evidence. The engine is the stable public façade.

## Verified Conditions

- sequence continuity and uniqueness
- parent-chain continuity
- payload digest integrity
- checkpoint digest integrity
- schema compatibility
- repository accessibility
- deterministic report and repository fingerprints

## Dispositions

`TRUSTED`, `RECOVERABLE`, `REQUIRES_MIGRATION`, `QUARANTINE`, and `UNRECOVERABLE`.

## Non-Responsibilities

This phase never deletes, moves, restores, replays, or migrates persisted evidence. Those actions belong to later phases.
MD

cat > dev/verification/verify_genesis_vi_a64.py <<'PY'
#!/usr/bin/env python3
from hashlib import sha256
from pathlib import Path
import importlib, json, sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
files=('core/executive/persistence/reports.py','core/executive/persistence/policies.py','core/executive/persistence/scanner.py','core/executive/persistence/evaluator.py','core/executive/persistence/integrity.py','tests/test_genesis_vi_a64_integrity_engine.py','docs/architecture/genesis_vi_a64_executive_integrity_engine.md')
missing=[x for x in files if not (ROOT/x).is_file()]
if missing: print('[FAIL] Missing:',*missing); raise SystemExit(1)
print('[PASS] Canonical VI-A6.4 structure')
pkg=importlib.import_module('core.executive.persistence')
symbols=('ExecutiveIntegrityEngine','IntegrityEngine','verify_session','IntegrityScanner','IntegrityEvaluator','IntegrityPolicy','IntegrityObservation','IntegrityFinding','IntegrityReport','IntegrityCode','IntegritySeverity','IntegrityDisposition')
missing=[x for x in symbols if not hasattr(pkg,x)]
if missing: print('[FAIL] Missing public symbols:',*missing); raise SystemExit(1)
print('[PASS] Stable VI-A6.4 public imports')
evaluator=(ROOT/'core/executive/persistence/evaluator.py').read_text()
if 'repository' in evaluator.lower(): print('[FAIL] Evaluator depends on repository'); raise SystemExit(1)
print('[PASS] Scanner/evaluator separation')
materials=[{'path':x,'sha256':sha256((ROOT/x).read_bytes()).hexdigest()} for x in files[:5]]
print('[PASS] Deterministic architecture fingerprint:',sha256(json.dumps(materials,sort_keys=True,separators=(',',':')).encode()).hexdigest())
PY
chmod +x dev/verification/verify_genesis_vi_a64.py

cat > dev/verify_genesis_vi_a64.sh <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"
export PROJECT_ROOT PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
cd "$PROJECT_ROOT"
failed=0
run(){ local label="$1"; shift; if "$@"; then echo "[PASS] $label"; else echo "[FAIL] $label"; failed=$((failed+1)); fi; }
echo '======================================================================'
echo 'JARVIS — GENESIS VI-A6.4 EXECUTIVE INTEGRITY ENGINE'
echo '======================================================================'
run 'VI-A6.4 package compilation' "$PYTHON_BIN" -m compileall -q core/executive/persistence
run 'VI-A6.4 unit tests' "$PYTHON_BIN" -m unittest -v tests.test_genesis_vi_a64_integrity_engine
run 'VI-A6.4 structural verification' "$PYTHON_BIN" dev/verification/verify_genesis_vi_a64.py
for script in dev/verify_genesis_vi_a63.sh dev/verify_genesis_vi_a62.sh dev/verify_genesis_vi_a61.sh; do
  if [[ -f "$script" ]]; then run "$(basename "$script") regression" bash "$script"; else echo "[SKIP] $(basename "$script") not present"; fi
done
echo '----------------------------------------------------------------------'
echo "Checks failed : $failed"
if [[ $failed -eq 0 ]]; then echo 'Overall status: EXCELLENT'; exit 0; fi
echo 'Overall status: FAILED'; exit 1
SH
chmod +x dev/verify_genesis_vi_a64.sh

echo '======================================================================'
echo 'Genesis VI-A6.4 installed; certification begins now.'
echo '======================================================================'
PYTHON_BIN="$PYTHON_BIN" PROJECT_ROOT="$PROJECT_ROOT" ./dev/verify_genesis_vi_a64.sh
