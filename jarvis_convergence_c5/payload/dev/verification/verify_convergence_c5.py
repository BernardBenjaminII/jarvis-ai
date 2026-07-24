from pathlib import Path
import py_compile, sys, unittest
ROOT=Path(__file__).resolve().parents[2]
required=[
"core/knowledge_awareness/__init__.py","core/knowledge_awareness/contracts.py",
"core/knowledge_awareness/service.py","core/conversation/orchestrator.py",
"tests/test_convergence_c5_executive_knowledge_awareness.py",
"docs/architecture/convergence_c5_executive_knowledge_awareness.md"]
print("="*72); print("JARVIS — CONVERGENCE C-5 EXECUTIVE KNOWLEDGE AWARENESS"); print("="*72)
failed=0
for rel in required:
    if not (ROOT/rel).exists(): print(f"[FAIL] Missing {rel}"); failed+=1
if not failed: print("[PASS] Canonical C-5 file set")
for rel in required:
    if rel.endswith('.py'):
        try: py_compile.compile(str(ROOT/rel),doraise=True)
        except Exception as exc: print(f"[FAIL] Compile {rel}: {exc}"); failed+=1
if not failed: print("[PASS] Python compilation contract")
text=(ROOT/'core/conversation/orchestrator.py').read_text()
for token in ('knowledge.awareness','executive_knowledge_state','executive_evidence_reasoning'):
    if token not in text: print(f"[FAIL] Missing integration token {token}"); failed+=1
if not failed: print("[PASS] Executive orchestration integration")
print("-"*72); print(f"Checks failed : {failed}"); print("Overall status:","EXCELLENT" if not failed else "FAILED")
if failed: raise SystemExit(1)
suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_convergence_c5_*.py')
result=unittest.TextTestRunner(verbosity=1).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
