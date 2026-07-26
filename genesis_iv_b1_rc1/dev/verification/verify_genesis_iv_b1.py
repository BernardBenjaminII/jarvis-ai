import hashlib, importlib, json, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
REQUIRED=('core/integration/__init__.py','core/integration/api.py','core/integration/audit.py','core/integration/catalog.py','core/integration/cli.py','core/integration/contracts.py','core/integration/enums.py','core/integration/errors.py','core/integration/knowledge.py','core/integration/projections.py','core/integration/registry.py','core/integration/serialization.py','core/integration/service.py','tests/test_genesis_iv_b1_executive_integration_visibility_fabric.py','docs/architecture/genesis_iv_b1_executive_integration_visibility_fabric.md','docs/decisions/ADR-0037-executive-integration-visibility-fabric.md')
def check(c,l):
    if not c: print('[FAIL]',l); raise SystemExit(1)
    print('[PASS]',l)
def main():
    check(all((ROOT/p).is_file() for p in REQUIRED),'Canonical IV-B1 file set')
    m=importlib.import_module('core.integration'); public=('CapabilityRegistry','ExecutiveIntegrationService','RepositoryIntegrationAuditor','KnowledgeReadiness','MissionControlProjection','build_genesis_iv_capability_registry','build_knowledge_readiness','to_canonical_data'); check(all(hasattr(m,n) for n in public),'Stable public imports')
    r=m.build_genesis_iv_capability_registry(); check({'mission_compiler','execution_orchestrator','executive_api','mission_control_ui'}.issubset(set(r.ids())),'Canonical Executive capability catalog')
    k=m.build_knowledge_readiness(query='verification',coverage=.75,known_domains=('architecture',),missing_domains=('deployment',),recommended_sources=('runtime inventory',)); check(k.can_proceed,'Knowledge readiness projection')
    with tempfile.TemporaryDirectory() as d:
        root=Path(d)
        for rel in ('core/cognition/mission_compiler','core/cognition/execution_orchestrator','core/src/routes','ui'): (root/rel).mkdir(parents=True,exist_ok=True)
        (root/'core/src/routes/operations.py').write_text('mission_compiler execution_orchestrator knowledge_catalog'); (root/'ui/mission_control.tsx').write_text('mission_compiler execution_orchestrator knowledge_catalog')
        service=m.ExecutiveIntegrationService(root); health=service.integration_health(); mc=service.mission_control(knowledge_readiness=k,active_missions=1,pending_approvals=1)
    check(bool(health.capabilities),'Integration health projection'); check(bool(health.links),'Capability connection projection'); check(bool(health.findings),'Explicit integration gap findings'); check(mc.commander_brief.active_missions==1,'Commander Brief projection'); check(mc.integration_health==health,'Mission Control health visibility')
    payload={'capabilities':[{'id':x.capability_id,'lifecycle':x.lifecycle.value,'runtime':x.runtime_visible,'api':x.api_visible,'ui':x.ui_visible} for x in health.capabilities],'links':[{'source':x.source_capability,'target':x.target_capability,'status':x.status.value} for x in health.links]}
    fp=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest(); print('[PASS] Deterministic IV-B1 fingerprint:',fp)
if __name__=='__main__': main()
