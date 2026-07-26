import tempfile, unittest, subprocess, sys, json
from pathlib import Path
from dataclasses import FrozenInstanceError
from core.integration import *
class T(unittest.TestCase):
    def test_registry(self):
        r=build_genesis_iv_capability_registry(); self.assertIn('mission_compiler',r); self.assertIn('mission_control_ui',r)
    def test_duplicate(self):
        c=CapabilityDefinition('x','X','X','core.x',CapabilityLifecycle.IMPLEMENTED,HealthStatus.HEALTHY,visibility=(VisibilitySurface.RUNTIME,)); r=CapabilityRegistry((c,))
        with self.assertRaises(DuplicateCapabilityError): r.register(c)
    def test_knowledge(self):
        k=build_knowledge_readiness(query='q',coverage=.72,known_domains=('systems',)); self.assertTrue(k.can_proceed); self.assertEqual(k.status,KnowledgeCoverageStatus.SUFFICIENT)
    def test_audit(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'core/cognition/mission_compiler').mkdir(parents=True); (root/'core/cognition/execution_orchestrator').mkdir(parents=True); (root/'core/src/routes').mkdir(parents=True); (root/'ui').mkdir(parents=True)
            (root/'core/src/routes/operations.py').write_text('mission_compiler execution_orchestrator'); (root/'ui/mission.tsx').write_text('mission compiler execution orchestrator')
            p=RepositoryIntegrationAuditor().audit(root,build_genesis_iv_capability_registry()); self.assertTrue(p.capabilities); self.assertTrue(p.findings)
    def test_visibility(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'core/cognition/mission_compiler').mkdir(parents=True); (root/'core/src/routes').mkdir(parents=True); (root/'ui').mkdir(parents=True)
            (root/'core/src/routes/mission.py').write_text('mission_compiler'); (root/'ui/capabilities.tsx').write_text('mission_compiler')
            p=RepositoryIntegrationAuditor().audit(root,build_genesis_iv_capability_registry()); m=next(x for x in p.capabilities if x.capability_id=='mission_compiler'); self.assertTrue(m.api_visible); self.assertTrue(m.ui_visible)
    def test_service(self):
        with tempfile.TemporaryDirectory() as d:
            s=ExecutiveIntegrationService(Path(d)); p=s.mission_control(active_missions=2,pending_approvals=1); self.assertEqual(p.commander_brief.active_missions,2)
    def test_cli_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "audit.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "core.integration.cli",
                    "audit",
                    "--repository-root",
                    str(root),
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.is_file())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertIn("overall_health", payload)

    def test_immutable(self):
        c=build_genesis_iv_capability_registry().get('mission_compiler')
        with self.assertRaises(FrozenInstanceError): c.name='changed'
    def test_serialization(self):
        d=to_canonical_data(build_genesis_iv_capability_registry().get('execution_orchestrator')); self.assertEqual(d['lifecycle'],'implemented'); self.assertIn('runtime',d['visibility'])
if __name__=='__main__': unittest.main()
