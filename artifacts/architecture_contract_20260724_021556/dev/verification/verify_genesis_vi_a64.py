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
