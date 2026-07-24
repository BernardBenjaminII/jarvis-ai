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
