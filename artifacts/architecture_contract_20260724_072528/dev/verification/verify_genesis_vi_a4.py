#!/usr/bin/env python3
from __future__ import annotations
import ast,hashlib,importlib,subprocess,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
FILES=('core/cognition/cycle.py','core/cognition/state_machine.py','core/cognition/working_memory.py','tests/test_genesis_vi_a4_cognition_cycle_controller.py','docs/architecture/cognition/genesis_vi_a4_cognition_cycle_controller.md')
EXPECTED='a5e103f1fed34ed17e4b363fc86fe100f29a02076f160cddb5b87a7ea39d04c3'
def run(mod,label):
 r=subprocess.run([sys.executable,'-m','unittest','-v',mod],cwd=ROOT,capture_output=True,text=True); return (r.returncode==0,label if r.returncode==0 else r.stdout+r.stderr)
def smoke():
 from core.cognition import CognitionCycleController,CognitiveState,MemoryEntry,MemoryEntryKind
 class C:
  def __init__(self): self.v=datetime(2026,1,1,tzinfo=timezone.utc)
  def __call__(self): x=self.v; self.v+=timedelta(seconds=1); return x
 c=CognitionCycleController(cycle_id='cert-cycle',mission_id='cert-mission',goal='Certify Genesis VI-A4.',authority='commander',memory_capacity=3,clock=C()); c.start(reason='Begin certification.'); c.admit_memory(MemoryEntry(entry_id='goal',kind=MemoryEntryKind.GOAL,content='Certify cognition-cycle orchestration.',importance=1,confidence=1,created_at=datetime(2026,1,1,tzinfo=timezone.utc)))
 for s in (CognitiveState.OBSERVING,CognitiveState.ATTENDING,CognitiveState.REASONING,CognitiveState.EVALUATING,CognitiveState.PLANNING,CognitiveState.EXECUTING,CognitiveState.REFLECTING): c.advance(s,reason=f'Advance to {s.value}.')
 c.record_note('Certification reflection complete.'); c.complete(reason='Certification complete.'); q=c.snapshot(); p='|'.join([q.context.cycle_id,q.context.mission_id,q.context.state.value,q.context.status.value,','.join(e.entry_id for e in q.context.working_memory),','.join(f'{x.sequence}:{x.previous_state.value}>{x.next_state.value}' for x in q.context.transitions),','.join(f'{e.sequence}:{e.kind.value}:{e.state.value}' for e in q.context.events),','.join(q.context.notes)]); return hashlib.sha256(p.encode()).hexdigest()
def main():
 checks=[]; checks.append((all((ROOT/f).is_file() for f in FILES),'Canonical Genesis VI-A4 file structure'))
 r=subprocess.run([sys.executable,'-m','compileall','-q',str(ROOT/'core/cognition')],cwd=ROOT); checks.append((r.returncode==0,'Genesis VI-A4 package compilation'))
 bad=[]
 for p in (ROOT/'core/cognition').glob('*.py'):
  tree=ast.parse(p.read_text())
  for n in ast.walk(tree):
   names=[a.name for a in n.names] if isinstance(n,ast.Import) else ([n.module] if isinstance(n,ast.ImportFrom) and n.module else [])
   if any(x.startswith(('openai','anthropic','ollama','transformers','requests','httpx')) for x in names): bad.append(str(p))
 checks.append((not bad,'Vendor, model, network, and retrieval isolation'))
 m=importlib.import_module('core.cognition'); checks.append((all(hasattr(m,x) for x in ('CognitionCycleController','CognitionCycleSnapshot')),'Stable Genesis VI-A4 public imports'))
 checks += [run('tests.test_genesis_vi_a4_cognition_cycle_controller','Genesis VI-A4 cognition-cycle-controller unit tests'),run('tests.test_genesis_vi_a3_cognitive_state_machine','Genesis VI-A3 regression'),run('tests.test_genesis_vi_a2_working_memory','Genesis VI-A2 regression'),run('tests.test_genesis_vi_a1_step1_foundation','Genesis VI-A1 Step 1 regression')]
 checks.append((smoke()==EXPECTED,'Deterministic cognition-cycle aggregate fingerprint'))
 print('\n'+'='*72+'\nJARVIS — GENESIS VI-A4 COGNITION CYCLE CONTROLLER\n'+'='*72); fail=0
 for ok,msg in checks: print(f'[{"PASS" if ok else "FAIL"}] {msg}'); fail+=not ok
 print('-'*72+f'\nChecks failed : {fail}\nOverall status: {"EXCELLENT" if not fail else "FAILED"}\n'+'='*72); return int(bool(fail))
if __name__=='__main__': raise SystemExit(main())
