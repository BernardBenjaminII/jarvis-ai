from __future__ import annotations

from pathlib import Path


BOOTSTRAP = """from pathlib import Path
import sys


def _bootstrap_certification_runtime() -> Path:
    current = Path(__file__).resolve()

    for candidate in (current.parent, *current.parents):
        if all(
            (candidate / name).is_dir()
            for name in ("core", "dev", "docs")
        ):
            candidate_text = str(candidate)
            if candidate_text not in sys.path:
                sys.path.insert(0, candidate_text)
            return candidate

    raise RuntimeError("Unable to locate the JARVIS project root.")


PROJECT_ROOT = _bootstrap_certification_runtime()

"""


def main() -> int:
    target = (
        Path.cwd()
        / "dev/certification/certify_genesis_ix_a4_1b_pack3a_runtime.py"
    )

    if not target.is_file():
        print("[SKIP] Pack 3A certifier is absent.")
        return 0

    source = target.read_text(encoding="utf-8")

    if "PROJECT_ROOT = _bootstrap_certification_runtime()" in source:
        print("[PASS] Pack 3A bootstrap already installed.")
        return 0

    future_import = "from __future__ import annotations\n"

    if future_import not in source:
        raise RuntimeError("Pack 3A certifier lacks the expected future import.")

    repaired = source.replace(
        future_import,
        future_import + "\n" + BOOTSTRAP,
        1,
    )

    target.write_text(repaired, encoding="utf-8")
    print("[PASS] Pack 3A runtime bootstrap repaired.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
