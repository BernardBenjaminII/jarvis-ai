from __future__ import annotations

import json
import os
import platform
import sqlite3
import sys
from pathlib import Path
from typing import Iterable

from .contracts import BootstrapCheck, BootstrapReport
from .discovery import (
    discover_knowledge_root,
    discover_repository_root,
    discover_runtime_root,
)
from .imports import DEFAULT_MODULES, resolve_modules


class CertificationRuntime:
    """Canonical runtime bootstrap for Genesis certification programs."""

    def __init__(
        self,
        *,
        start: str | Path | None = None,
        change_directory: bool = True,
    ) -> None:
        self.start = start
        self.change_directory = change_directory
        self.initial_cwd = Path.cwd().resolve()
        self.repository_root: Path | None = None
        self.runtime_root: Path | None = None
        self.knowledge_root: Path | None = None
        self.catalog_database: Path | None = None
        self._bootstrapped = False

    def bootstrap(self) -> "CertificationRuntime":
        root = discover_repository_root(self.start)
        self.repository_root = root

        root_text = str(root)

        if root_text not in sys.path:
            sys.path.insert(0, root_text)

        pythonpath = [
            item
            for item in os.environ.get("PYTHONPATH", "").split(os.pathsep)
            if item
        ]
        if root_text not in pythonpath:
            pythonpath.insert(0, root_text)
            os.environ["PYTHONPATH"] = os.pathsep.join(pythonpath)

        os.environ["JARVIS_PROJECT_ROOT"] = root_text

        if self.change_directory:
            os.chdir(root)

        self.runtime_root = discover_runtime_root(root)
        self.knowledge_root = discover_knowledge_root(root, self.runtime_root)

        try:
            from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
            self.catalog_database = Path(DEFAULT_CATALOG_DB).resolve()
        except Exception:
            if self.knowledge_root is not None:
                self.catalog_database = (
                    self.knowledge_root / "catalog.sqlite"
                ).resolve()

        self._bootstrapped = True
        return self

    def certify(
        self,
        *,
        modules: Iterable[str] = DEFAULT_MODULES,
        require_catalog: bool = True,
    ) -> BootstrapReport:
        if not self._bootstrapped:
            self.bootstrap()

        assert self.repository_root is not None

        root = self.repository_root
        checks: list[BootstrapCheck] = [
            BootstrapCheck(
                code="REPOSITORY",
                label="Repository root",
                status="PASS" if root.exists() else "FAIL",
                detail=str(root),
                actual=str(root),
            ),
            BootstrapCheck(
                code="SYS_PATH",
                label="Repository import path",
                status="PASS" if str(root) in sys.path else "FAIL",
                detail="Repository root must be present in sys.path.",
                actual=list(sys.path[:8]),
            ),
            BootstrapCheck(
                code="CWD",
                label="Effective working directory",
                status="PASS" if Path.cwd().resolve() == root else "FAIL",
                detail="Certification executes from the repository root.",
                actual=str(Path.cwd().resolve()),
            ),
        ]

        in_venv = bool(
            os.environ.get("VIRTUAL_ENV")
            or getattr(sys, "base_prefix", sys.prefix) != sys.prefix
        )
        checks.append(
            BootstrapCheck(
                code="VENV",
                label="Virtual environment",
                status="PASS" if in_venv else "FAIL",
                detail="Certification should execute in the JARVIS virtual environment.",
                actual=os.environ.get("VIRTUAL_ENV") or sys.prefix,
            )
        )

        for result in resolve_modules(tuple(modules)):
            checks.append(
                BootstrapCheck(
                    code=f"IMPORT:{result.module}",
                    label=f"Import {result.module}",
                    status="PASS" if result.imported else "FAIL",
                    detail=result.origin or result.error or "",
                    actual=result.origin,
                )
            )

        catalog_ok = False
        catalog_detail = "Catalog not found."

        if self.catalog_database and self.catalog_database.is_file():
            try:
                with sqlite3.connect(self.catalog_database) as connection:
                    connection.execute("SELECT 1").fetchone()
                catalog_ok = True
                catalog_detail = "SQLite catalog opened successfully."
            except Exception as exc:
                catalog_detail = f"{type(exc).__name__}: {exc}"

        checks.append(
            BootstrapCheck(
                code="CATALOG",
                label="Knowledge catalog",
                status="PASS" if catalog_ok or not require_catalog else "FAIL",
                detail=catalog_detail,
                actual=(
                    str(self.catalog_database)
                    if self.catalog_database is not None
                    else None
                ),
            )
        )

        return BootstrapReport(
            repository_root=str(root),
            python_executable=sys.executable,
            python_version=platform.python_version(),
            initial_cwd=str(self.initial_cwd),
            effective_cwd=str(Path.cwd().resolve()),
            virtual_environment=os.environ.get("VIRTUAL_ENV"),
            runtime_root=(
                str(self.runtime_root)
                if self.runtime_root is not None
                else None
            ),
            knowledge_root=(
                str(self.knowledge_root)
                if self.knowledge_root is not None
                else None
            ),
            catalog_database=(
                str(self.catalog_database)
                if self.catalog_database is not None
                else None
            ),
            checks=tuple(checks),
        )

    def write_reports(
        self,
        report: BootstrapReport,
        output_dir: str | Path,
    ) -> None:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        (output / "runtime_bootstrap.json").write_text(
            json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        lines = [
            "# Certification Runtime Bootstrap",
            "",
            f"**Status:** **{report.status}**",
            f"**Repository root:** `{report.repository_root}`",
            f"**Python:** `{report.python_executable}`",
            f"**Python version:** `{report.python_version}`",
            f"**Initial CWD:** `{report.initial_cwd}`",
            f"**Effective CWD:** `{report.effective_cwd}`",
            f"**Runtime root:** `{report.runtime_root}`",
            f"**Knowledge root:** `{report.knowledge_root}`",
            f"**Catalog:** `{report.catalog_database}`",
            "",
            "| Code | Check | Status | Detail |",
            "|---|---|---|---|",
        ]

        for item in report.checks:
            lines.append(
                f"| `{item.code}` | {item.label} | "
                f"**{item.status}** | {item.detail} |"
            )

        markdown = "\n".join(lines) + "\n"

        for name in (
            "runtime_environment.md",
            "module_resolution.md",
            "repository_layout.md",
            "bootstrap_trace.md",
        ):
            (output / name).write_text(markdown, encoding="utf-8")
