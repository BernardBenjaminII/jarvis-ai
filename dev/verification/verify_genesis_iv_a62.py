from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[2]
REQUIRED=(
"core/cognition/coa/__init__.py","core/cognition/coa/contracts.py","core/cognition/coa/enums.py","core/cognition/coa/errors.py","core/cognition/coa/models.py","core/cognition/coa/generator.py","core/cognition/coa/repository.py","core/cognition/coa/service.py",
"tests/test_genesis_iv_a62_executive_alternative_generation.py","docs/architecture/genesis_iv_a62_executive_alternative_generation.md","docs/decisions/ADR-0032-executive-course-of-action-generation.md","dev/verify_genesis_4a62.sh")

def main():
    failed=0
    def check(ok,label):
        nonlocal failed; print(("[PASS] " if ok else "[FAIL] ")+label); failed += 0 if ok else 1
    check(all((ROOT/p).is_file() for p in REQUIRED),"Canonical IV-A6.2 file set")
    check((ROOT/"core/cognition/reasoner").is_dir() and (ROOT/"core/cognition/decision").is_dir(),"Genesis IV-A5 and IV-A6.1 prerequisite compatibility")
    try:
        for p in REQUIRED:
            if p.endswith('.py'): ast.parse((ROOT/p).read_text(encoding='utf-8'))
        check(True,"Python syntax structure")
    except Exception as e: print(e); check(False,"Python syntax structure")

    forbidden = (
        "core.executive.planning",
        "core.operations",
        "subprocess",
        "sqlite3",
        "requests",
    )

    source = "\n".join(
        (ROOT / p).read_text(encoding="utf-8")
        for p in REQUIRED
        if p.startswith("core/") and p.endswith(".py")
    )

    check(
        not any(token in source for token in forbidden),
        "Forward-only cognition boundary",
    )

    manifest=ROOT/"dev/verification/manifests/genesis.manifest"
    check(manifest.is_file() and "dev/verify_genesis_4a62.sh" in manifest.read_text(encoding='utf-8'),"Constitutional Genesis manifest registration")
    payload="".join((ROOT/p).read_text(encoding='utf-8') for p in sorted(REQUIRED) if (ROOT/p).is_file())
    print("[INFO] Architecture fingerprint: "+sha256(payload.encode()).hexdigest())
    print("-"*72); print(f"Checks failed : {failed}"); print("Overall status: "+("EXCELLENT" if failed==0 else "FAILED")); print("="*72)
    return 1 if failed else 0
if __name__=='__main__': raise SystemExit(main())
