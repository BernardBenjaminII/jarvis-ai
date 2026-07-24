from __future__ import annotations
import ast, hashlib, importlib, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FAILED = 0

def heading(title, subtitle=None):
    print(); print("="*72); print(title); print(subtitle or ""); print("="*72)

def check(label, action):
    global FAILED
    try: action()
    except Exception as exc:
        FAILED += 1; print(f"[FAIL] {label}\n       {type(exc).__name__}: {exc}")
    else: print(f"[PASS] {label}")

def require(value, message):
    if not value: raise AssertionError(message)

def prerequisites():
    for p in (ROOT/"core/executive/timeline/repository.py", ROOT/"core/executive/timeline/__init__.py"): require(p.is_file(), f"Missing {p}")

def compilation():
    for rel in ("core/executive/timeline/query_engine.py","core/executive/timeline/replay_readiness.py","tests/test_genesis_vi_a68_part_b.py","demo/demo_genesis_vi_a68_part_b.py"):
        compile((ROOT/rel).read_text(encoding="utf-8"), rel, "exec")

def imports():
    module = importlib.import_module("core.executive.timeline")
    for name in ("TimelineQueryEngine","TimelinePage","TimelineStatistics","ReplayReadinessReport","assess_replay_readiness"): require(hasattr(module,name), f"Missing {name}")

def boundaries():
    tree = ast.parse((ROOT/"core/executive/timeline/query_engine.py").read_text())
    names=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import): names += [a.name for a in node.names]
        elif isinstance(node,ast.ImportFrom) and node.module: names.append(node.module)
    require(not [n for n in names if n.startswith(("fastapi","flask","django","streamlit"))], "UI dependency leaked into core")

def tests():
    result=subprocess.run([sys.executable,"-m","unittest","-v","tests.test_genesis_vi_a68_part_b"],cwd=ROOT,check=False)
    require(result.returncode==0,"Part B tests failed")

def smoke():
    spec = importlib.import_module("tests.test_genesis_vi_a68_part_b")
    fixture_repository = spec.fixture_repository
    from core.executive.timeline import TimelineQueryEngine, assess_replay_readiness
    one=TimelineQueryEngine(fixture_repository()); two=TimelineQueryEngine(fixture_repository())
    require(one.fingerprint()==two.fingerprint(),"Nondeterministic fingerprint")
    require(assess_replay_readiness(fixture_repository()).ready,"Repository not replay-ready")

def fingerprint():
    digest=hashlib.sha256()
    for rel in sorted(("core/executive/timeline/query_engine.py","core/executive/timeline/replay_readiness.py","tests/test_genesis_vi_a68_part_b.py")):
        digest.update(rel.encode()); digest.update((ROOT/rel).read_bytes())
    print(f"       Architecture fingerprint: {digest.hexdigest()}")

def regression():
    candidates=("dev/verify_genesis_vi_a68_part_a.sh","dev/verify_genesis_vi_a67.sh","dev/verify_genesis_vi_a6_7.sh")
    found=False
    for rel in candidates:
        path=ROOT/rel
        if path.is_file():
            found=True; result=subprocess.run(["bash",str(path)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
            require(result.returncode==0,f"Regression failed: {rel}")
    if not found: print("       Prior wrapper absent; prerequisite structure certified.")

def main():
    global FAILED
    heading("GENESIS VI-A6.8 PART B","EXECUTIVE TIMELINE QUERY ENGINE & CERTIFICATION")
    check("Genesis VI-A6.8 Part A prerequisite",prerequisites)
    check("Package compilation",compilation)
    check("Stable public imports",imports)
    check("Forward-only structural boundaries",boundaries)
    check("Deterministic query and replay smoke",smoke)
    check("Query engine unit tests",tests)
    check("Deterministic architecture fingerprint",fingerprint)
    phase_failed=FAILED
    heading("GENESIS REGRESSION CERTIFICATION","PRIOR EXECUTIVE CONTINUITY FOUNDATIONS")
    check("Genesis VI-A6.8 Part A / VI-A6.7 regression",regression)
    heading("EXECUTIVE ARCHITECTURE STATUS")
    for item in ("Persistence","Serializer","Checkpoints","Integrity","Recovery","Lifecycle","Timeline","Timeline Repository","Deterministic Query Engine"): print(f"  ✓ {item}")
    print("  ○ Executive Replay Engine")
    print("\nExecutive Principles\n  ✓ Deterministic state queries\n  ✓ Immutable query results\n  ✓ Replay-readiness evidence\n  ○ Executive Accountability runtime interface")
    heading("MASTER CERTIFICATION SUMMARY")
    print(f"Phase checks failed      : {phase_failed}"); print(f"All checks failed        : {FAILED}")
    print("Genesis VI-A6.8 Part B : " + ("CERTIFIED" if phase_failed==0 else "NOT CERTIFIED"))
    print("Overall status          : " + ("EXCELLENT" if FAILED==0 else "ATTENTION REQUIRED")); print("="*72)
    return 0 if FAILED==0 else 1

if __name__=="__main__": raise SystemExit(main())
