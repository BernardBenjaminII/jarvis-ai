#!/usr/bin/env python3
from pathlib import Path
import importlib
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)) if str(ROOT) not in sys.path else None
FILES = (
    "core/src/routes/mission_control.py",
    "core/src/static/mission_control/index.html",
    "core/src/static/mission_control/styles.css",
    "core/src/static/mission_control/app.js",
    "tests/test_mc1002_commanders_bridge.py",
    "docs/architecture/commanders_bridge_foundation.md",
)

def report(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f": {detail}" if detail and not ok else ""))
    return 0 if ok else 1

def main():
    failed = 0
    print("=" * 70)
    print("JARVIS — MC-1002 COMMANDER'S BRIDGE FOUNDATION")
    print("=" * 70)
    missing = [x for x in FILES if not (ROOT / x).is_file()]
    failed += report("Canonical MC-1002 file set", not missing, ", ".join(missing))
    c = subprocess.run([sys.executable, "-m", "compileall", "-q", "core/src/routes/mission_control.py"], cwd=ROOT)
    failed += report("Mission Control compilation", c.returncode == 0)
    try:
        mod = importlib.import_module("core.src.routes.mission_control")
        ok, detail = hasattr(mod, "router"), ""
    except Exception as exc:
        ok, detail = False, f"{type(exc).__name__}: {exc}"
    failed += report("Mission Control route importability", ok, detail)
    main_text = (ROOT / "core/src/main.py").read_text()
    failed += report("Mission Control registered in FastAPI", "mission_control_router" in main_text and "/mission-control/static" in main_text)
    js = (ROOT / "core/src/static/mission_control/app.js").read_text()
    failed += report("Operations-only browser boundary", "/operations/status" in js and "/executive/" not in js)
    t = subprocess.run([sys.executable, "-m", "unittest", "-v", "tests.test_mc1002_commanders_bridge"], cwd=ROOT)
    failed += report("MC-1002 unit tests", t.returncode == 0)
    print("-" * 70)
    print(f"Checks failed : {failed}")
    print(f"Overall status: {'EXCELLENT' if failed == 0 else 'FAILED'}")
    print("=" * 70)
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
