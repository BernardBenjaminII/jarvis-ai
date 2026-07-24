#!/usr/bin/env python3
from __future__ import annotations
import ast, hashlib, importlib, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
REQ=("core/cognition/session.py","core/cognition/cycle.py","tests/test_genesis_vi_a5_executive_session.py","docs/architecture/cognition/genesis_vi_a5_executive_session.md")
FORBIDDEN=("openai","anthropic","ollama","transformers","langchain","llama_index","requests","httpx")
EXPECTED="90e804eba783406badfb3a4dbf0c7e69b43c008d40cdcf46be453a1d1489971b"
def result(ok,msg): print(f"[{'PASS' if ok else 'FAIL'}] {msg}"); return 0 if ok else 1
def unittest_check(module,label):
 r=subprocess.run([sys.executable,"-m","unittest","-v",module],cwd=ROOT,capture_output=True,text=True)
 return result(r.returncode==0,label if r.returncode==0 else (r.stdout+r.stderr).strip())
def fingerprint():
 from core.cognition import ExecutiveSession,CognitiveState,MemoryEntry,MemoryEntryKind
 class Clock:
  def __init__(self): self.v=datetime(2026,1,1,tzinfo=timezone.utc)
  def __call__(self): x=self.v; self.v += timedelta(seconds=1); return x
 s=ExecutiveSession(session_id="cert-session",mission_id="cert-mission",executive_id="jarvis",authority="commander",clock=Clock())
 s.create_cycle(cycle_id="cycle-b",goal="Second")
 s.create_cycle(cycle_id="cycle-a",goal="First")
 s.start_cycle("cycle-a",reason="Start")
 s.admit_memory("cycle-a",MemoryEntry(entry_id="goal",kind=MemoryEntryKind.GOAL,content="Certify",created_at=datetime(2026,1,1,tzinfo=timezone.utc)))
 for state in (CognitiveState.OBSERVING,CognitiveState.ATTENDING,CognitiveState.REASONING,CognitiveState.EVALUATING,CognitiveState.PLANNING,CognitiveState.EXECUTING,CognitiveState.REFLECTING): s.advance_cycle("cycle-a",state,reason=state.value)
 s.complete_cycle("cycle-a",reason="Done")
 snap=s.snapshot()
 payload="|".join([snap.session_id,snap.mission_id,snap.executive_id,snap.status.value,str(snap.active_cycle_id),",".join(c.context.cycle_id+":"+c.context.state.value for c in snap.cycles),",".join(f"{e.sequence}:{e.kind}:{e.cycle_id or '-'}" for e in snap.events)])
 return hashlib.sha256(payload.encode()).hexdigest()
def main():
 print("\n"+"="*72+"\nJARVIS — GENESIS VI-A5 EXECUTIVE SESSION\n"+"="*72); fails=0
 fails+=result(all((ROOT/p).is_file() for p in REQ),"Canonical Genesis VI-A5 file structure")
 r=subprocess.run([sys.executable,"-m","compileall","-q",str(ROOT/'core/cognition'),str(ROOT/'tests/test_genesis_vi_a5_executive_session.py')],cwd=ROOT)
 fails+=result(r.returncode==0,"Genesis VI-A5 package compilation")
 violations=[]
 for p in (ROOT/'core/cognition').glob('*.py'):
  tree=ast.parse(p.read_text())
  for n in ast.walk(tree):
   names=[]
   if isinstance(n,ast.Import): names=[a.name for a in n.names]
   elif isinstance(n,ast.ImportFrom) and n.module: names=[n.module]
   for name in names:
    if name.startswith(FORBIDDEN): violations.append(f"{p.name}->{name}")
 fails+=result(not violations,"Vendor, model, network, and retrieval isolation" if not violations else str(violations))
 m=importlib.import_module('core.cognition'); syms=('ExecutiveSession','ExecutiveSessionEvent','ExecutiveSessionSnapshot','ExecutiveSessionStatus')
 fails+=result(all(hasattr(m,x) and x in m.__all__ for x in syms),"Stable Genesis VI-A5 public imports")
 fails+=unittest_check('tests.test_genesis_vi_a5_executive_session','Genesis VI-A5 executive-session unit tests')
 fails+=unittest_check('tests.test_genesis_vi_a4_cognition_cycle_controller','Genesis VI-A4 regression')
 fails+=unittest_check('tests.test_genesis_vi_a3_cognitive_state_machine','Genesis VI-A3 regression')
 fails+=unittest_check('tests.test_genesis_vi_a2_working_memory','Genesis VI-A2 regression')
 fails+=unittest_check('tests.test_genesis_vi_a1_step1_foundation','Genesis VI-A1 Step 1 regression')
 actual=fingerprint(); fails+=result(actual==EXPECTED,"Deterministic executive-session fingerprint" if actual==EXPECTED else f"Fingerprint mismatch: {actual}")
 print("-"*72+f"\nChecks failed : {fails}\nOverall status: {'EXCELLENT' if fails==0 else 'FAILED'}\n"+"="*72)
 return 0 if fails==0 else 1
if __name__=='__main__': raise SystemExit(main())
