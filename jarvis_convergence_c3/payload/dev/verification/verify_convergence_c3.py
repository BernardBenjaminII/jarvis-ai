from pathlib import Path
import hashlib, py_compile, sys, unittest
ROOT=Path(__file__).resolve().parents[2]
checks=[]
def check(name, ok):
 print(f"[{'PASS' if ok else 'FAIL'}] {name}"); checks.append(bool(ok))
required=[ROOT/'core/executive/routing.py',ROOT/'core/executive/planner.py',ROOT/'tests/test_convergence_c3_capability_routing.py',ROOT/'docs/architecture/convergence_c3_capability_routing.md']
check('Canonical C-3 file set', all(p.is_file() for p in required))
try:
 for p in required:
  if p.suffix=='.py': py_compile.compile(str(p),doraise=True)
 check('Python compilation contract', True)
except Exception as exc: print(exc); check('Python compilation contract',False)
planner=(ROOT/'core/executive/planner.py').read_text()
router=(ROOT/'core/executive/routing.py').read_text()
check('Mission planner uses canonical CapabilityRouter', 'CapabilityRouter' in planner and 'DEFAULT_RULES' not in planner)
check('Routing remains deterministic and registry-backed', 'self.registry.select' in router and 'ollama' not in router.casefold())
loader=unittest.TestLoader(); suite=loader.loadTestsFromNames(['tests.test_convergence_c1_executive_conversation','tests.test_convergence_c1_http_contract','tests.test_convergence_c2_director_activation','tests.test_convergence_c2_http_contract','tests.test_convergence_c2a_certification_repair','tests.test_convergence_c3_capability_routing'])
result=unittest.TextTestRunner(verbosity=1).run(suite)
check('C-1 through C-3 deterministic tests', result.wasSuccessful())
fingerprint=hashlib.sha256('\n'.join(p.read_text() for p in required).encode()).hexdigest(); print(f'Architecture fingerprint: {fingerprint}')
failed=len(checks)-sum(checks); print('-'*72); print(f'Checks failed : {failed}'); print('Overall status: '+('EXCELLENT' if not failed else 'FAILED')); sys.exit(0 if not failed else 1)
