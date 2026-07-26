from datetime import datetime,timezone
from hashlib import sha256
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
REQUIRED=("core/observation/__init__.py","core/observation/adapters.py","core/observation/audit.py","core/observation/contracts.py","core/observation/enums.py","core/observation/errors.py","core/observation/serialization.py","tests/test_genesis_iv_b3_canonical_observation_convergence.py","docs/architecture/convergence/genesis_iv_b3_canonical_observation_convergence.md","docs/decisions/ADR-0038-canonical-observation-convergence.md","standards/executive/OCS-0000.md")
def check(c,l):
    if not c: print("[FAIL]",l); raise SystemExit(1)
    print("[PASS]",l)
def main():
    check(all((ROOT/p).is_file() for p in REQUIRED),"Canonical IV-B3 file set")
    m=importlib.import_module("core.observation")
    public=("Observation","ObservationSource","ObservationContext","ObservationDomain","ObservationKind","RealityClass","SourceType","adapt_legacy_observation","audit_observation_definitions","canonical_json")
    check(all(hasattr(m,n) for n in public),"Stable canonical public imports")
    t=datetime(2026,7,26,8,tzinfo=timezone.utc)
    s=m.ObservationSource.create(reality_class="recorded",source_type="book",identifier="book:verification",producer="academy-reader",collector="document-extractor",authority="primary",segment_id="chapter-1")
    a=m.Observation.create(domain="knowledge",observation_type="knowledge.claim",kind="content",subject="verification",predicate="states",value="Recorded reality produces observations.",source=s,observed_at=t,recorded_at=t,confidence=.98)
    b=m.Observation.create(domain="knowledge",observation_type="knowledge.claim",kind="content",subject="verification",predicate="states",value="Recorded reality produces observations.",source=s,observed_at=t,recorded_at=t,confidence=.98)
    check(a.observation_id==b.observation_id,"Deterministic observation identity")
    check(a.source.source_type is m.SourceType.BOOK,"Books and files are first-class sources")
    report=m.audit_observation_definitions(ROOT)
    check(any(x.canonical for x in report.definitions),"Canonical definition discovered")
    check(not report.forbidden_duplicates,"No ungoverned Observation definitions")
    payload={"schema":m.SCHEMA_VERSION,"observation":a.to_canonical_data(),"definitions":[x.path for x in report.definitions]}
    print("[PASS] Deterministic IV-B3 fingerprint:",sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest())
if __name__=="__main__": main()
