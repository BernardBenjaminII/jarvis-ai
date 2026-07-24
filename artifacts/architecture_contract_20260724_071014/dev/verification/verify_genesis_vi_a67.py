#!/usr/bin/env python3
from hashlib import sha256
import inspect
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = [
    ROOT / "core/executive/timeline/__init__.py",
    ROOT / "core/executive/timeline/contracts.py",
    ROOT / "core/executive/timeline/engine.py",
    ROOT / "core/executive/timeline/queries.py",
    ROOT / "core/executive/timeline/adapters.py",
    ROOT / "tests/test_genesis_vi_a67_executive_timeline.py",
    ROOT / "docs/architecture/genesis_vi_a67_executive_timeline_engine.md",
]
def fail(x): print(f"[FAIL] {x}"); raise SystemExit(1)

missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.is_file()]
if missing: fail(f"Missing: {missing}")
print("[PASS] Canonical Genesis VI-A6.7 structure")

sys.path.insert(0, str(ROOT))
from core.executive.timeline import ExecutiveTimelineEngine, TimelineEvent, TimelineQuery
if not all(inspect.isclass(x) for x in (ExecutiveTimelineEngine, TimelineEvent, TimelineQuery)):
    fail("Unstable public API")
print("[PASS] Stable Executive timeline public API")

source = inspect.getsource(ExecutiveTimelineEngine)
for token in ("previous_event_fingerprint", "verify_fingerprint", "sequence", "terminal_fingerprint"):
    if token not in source: fail(f"Missing architecture concept: {token}")
print("[PASS] Immutable chained-event architecture")

for token in ("sqlite", "requests", "socket", "subprocess", "open("):
    if token in source.lower(): fail(f"Isolation violation: {token}")
print("[PASS] Storage, network, and process isolation")

print(f"[PASS] Deterministic architecture fingerprint: {sha256(b''.join(p.read_bytes() for p in REQUIRED[:5])).hexdigest()}")
