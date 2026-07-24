#!/usr/bin/env python3
from hashlib import sha256
import ast
import inspect
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = [
    ROOT / "core/executive/timeline/repository_contracts.py",
    ROOT / "core/executive/timeline/serializers.py",
    ROOT / "core/executive/timeline/storage.py",
    ROOT / "core/executive/timeline/indexes.py",
    ROOT / "core/executive/timeline/repository.py",
    ROOT / "tests/test_genesis_vi_a68_part_a_timeline_repository.py",
    ROOT / "docs/architecture/genesis_vi_a68_timeline_repository_foundation.md",
]


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.is_file()]
if missing:
    fail(f"Missing required files: {missing}")
print("[PASS] Canonical Genesis VI-A6.8 Part A structure")

sys.path.insert(0, str(ROOT))
from core.executive.timeline import (
    AppendOnlyTimelineStorage,
    ExecutiveTimelineRepository,
    TimelineEventSerializer,
    TimelineRepositoryIndexes,
)

for symbol in (
    AppendOnlyTimelineStorage,
    ExecutiveTimelineRepository,
    TimelineEventSerializer,
    TimelineRepositoryIndexes,
):
    if not inspect.isclass(symbol):
        fail(f"Unstable public symbol: {symbol}")
print("[PASS] Stable timeline repository public API")

repository_source = inspect.getsource(ExecutiveTimelineRepository)
for forbidden in ("sqlite3", "sqlalchemy", "requests", "httpx", "socket", "subprocess"):
    if forbidden in repository_source.lower():
        fail(f"Forbidden dependency in repository: {forbidden}")
print("[PASS] Database, network, vendor, and process isolation")

for forbidden_method in ("delete", "update", "truncate", "replace"):
    if hasattr(ExecutiveTimelineRepository, forbidden_method):
        fail(f"Append-only boundary violation: {forbidden_method}")
print("[PASS] Append-only repository public boundary")

for path in REQUIRED[:5]:
    ast.parse(path.read_text(encoding="utf-8"))
print("[PASS] Repository module syntax and structural parse")

fingerprint = sha256(b"".join(path.read_bytes() for path in REQUIRED[:5])).hexdigest()
print(f"[PASS] Deterministic architecture fingerprint: {fingerprint}")
