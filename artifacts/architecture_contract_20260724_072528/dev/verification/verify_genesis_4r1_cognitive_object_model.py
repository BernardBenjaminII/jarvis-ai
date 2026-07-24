#!/usr/bin/env python3
from __future__ import annotations
import importlib, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REQ=(ROOT/'core/cognition/common/object_model.py',ROOT/'core/cognition/common/cognitive_object.py',ROOT/'tests/cognition/test_genesis_4r1_cognitive_object_model.py',ROOT/'docs/architecture/cognition/01_cognitive_object_model.md',ROOT/'docs/decisions/ADR-0021-cognitive-object-model.md')
def fail(m): print(f'[FAIL] {m}'); raise SystemExit(1)
def main():
 print('='*70); print('JARVIS GENESIS IV-R1 — COGNITIVE OBJECT MODEL'); print('='*70)
 for p in REQ:
  if not p.is_file(): fail(f'Missing {p.relative_to(ROOT)}')
 print('[PASS] R1 package manifest')
 sys.path.insert(0,str(ROOT))
 a=importlib.import_module('core.cognition.common.object_model'); b=importlib.import_module('core.cognition.common.cognitive_object')
 if a.CognitiveObject is not b.CognitiveObject: fail('Compatibility identity')
 print('[PASS] Stable COM imports')
 for args,label in [([sys.executable,'-m','unittest','tests.cognition.test_genesis_4r1_cognitive_object_model'],'R1 unit tests'),([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests/cognition'),'-t',str(ROOT),'-p','test_*.py'],'Cognition regression suite')]:
  if subprocess.run(args,cwd=ROOT).returncode: fail(label)
  print(f'[PASS] {label}')
 print('-'*70); print('Checks failed  : 0'); print('Overall status : EXCELLENT'); return 0
if __name__=='__main__': raise SystemExit(main())
