from __future__ import annotations

import argparse
import sys
from pathlib import Path


def locate_project_root() -> Path:
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


PROJECT_ROOT = locate_project_root()

from core.certification.runtime import CertificationRuntime


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/audits/certification_runtime"),
    )
    args = parser.parse_args()

    runtime = CertificationRuntime(start=args.root).bootstrap()
    report = runtime.certify()
    runtime.write_reports(report, args.output_dir)

    print("=" * 76)
    print("GENESIS IX-A4.1B PACK 3A.1 — CERTIFICATION RUNTIME BOOTSTRAP")
    print("=" * 76)
    print("Repository root :", report.repository_root)
    print("Python          :", report.python_executable)
    print("Effective CWD   :", report.effective_cwd)
    print("Catalog         :", report.catalog_database)
    print("Overall status  :", report.status)
    print("=" * 76)

    return 0 if report.status == "EXCELLENT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
