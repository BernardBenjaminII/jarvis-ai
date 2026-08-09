
from __future__ import annotations

import importlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Iterable

from .models import IntegrationAuditReport, IntegrationFinding, IntegrationStatus


class IntegrationAuditor:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

    def run(self) -> IntegrationAuditReport:
        findings = tuple(sorted(
            (
                *self._audit_executive(),
                *self._audit_mission_control(),
                *self._audit_knowledge(),
                *self._audit_acquisition(),
                *self._audit_runtime(),
                *self._audit_git(),
                *self._audit_ollama(),
                *self._audit_security(),
            ),
            key=lambda item: (item.domain, item.observable, item.finding_id),
        ))
        return IntegrationAuditReport("1.0.0", "Genesis VII-B0", findings)

    def _module_finding(
        self,
        finding_id: str,
        domain: str,
        observable: str,
        module_name: str,
        expected_symbols: Iterable[str] = (),
    ) -> IntegrationFinding:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            return IntegrationFinding(
                finding_id,
                domain,
                observable,
                IntegrationStatus.FAIL,
                f"Module import failed: {module_name}",
                (f"{type(exc).__name__}: {exc}",),
                (f"Restore importability of {module_name}.",),
            )
        missing = tuple(s for s in expected_symbols if not hasattr(module, s))
        if missing:
            return IntegrationFinding(
                finding_id,
                domain,
                observable,
                IntegrationStatus.PARTIAL,
                f"Public API incomplete: {module_name}",
                ("Missing: " + ", ".join(missing),),
                ("Restore the missing public exports.",),
            )
        return IntegrationFinding(
            finding_id,
            domain,
            observable,
            IntegrationStatus.PASS,
            f"Module available: {module_name}",
            tuple(expected_symbols),
        )

    def _path_finding(
        self,
        finding_id: str,
        domain: str,
        observable: str,
        relative_path: str,
        required: bool = True,
    ) -> IntegrationFinding:
        path = self.project_root / relative_path
        if path.exists():
            return IntegrationFinding(
                finding_id,
                domain,
                observable,
                IntegrationStatus.PASS,
                f"Path exists: {relative_path}",
                (path.as_posix(),),
            )
        return IntegrationFinding(
            finding_id,
            domain,
            observable,
            IntegrationStatus.FAIL if required else IntegrationStatus.PARTIAL,
            f"Path missing: {relative_path}",
            (),
            (f"Create or restore {relative_path}.",),
        )

    def _audit_executive(self):
        return (
            self._module_finding(
                "executive-director", "executive", "director",
                "core.executive.director", ("ExecutiveDirector",)
            ),
            self._module_finding(
                "executive-capabilities", "executive", "capabilities",
                "core.executive.capabilities",
                ("DirectorReadiness", "CapabilityOrchestrator", "CapabilityRegistry"),
            ),
            self._module_finding(
                "executive-routes", "executive", "operations_api",
                "core.src.routes.operations", ("router",)
            ),
        )

    def _audit_mission_control(self):
        return tuple(
            self._path_finding(fid, "mission_control", observable, path, required)
            for fid, observable, path, required in (
                ("mc-shell", "application_shell", "core/src/static/mission_control/index.html", True),
                ("mc-api", "api_client", "core/src/static/mission_control/api.js", True),
                ("mc-dashboard", "dashboard_projection", "core/src/static/mission_control/dashboard.js", False),
                ("mc-health", "health_projection", "core/src/static/mission_control/health_projection.js", False),
                ("mc-timeline", "timeline_projection", "core/src/static/mission_control/timeline_projection.js", False),
            )
        )

    def _audit_knowledge(self):
        candidates = ("knowledge", "core.knowledge", "core.knowledge_engine")
        discovered = None
        for candidate in candidates:
            try:
                importlib.import_module(candidate)
                discovered = candidate
                break
            except Exception:
                pass
        finding = IntegrationFinding(
            "knowledge-api",
            "knowledge",
            "public_api",
            IntegrationStatus.PASS if discovered else IntegrationStatus.PARTIAL,
            f"Knowledge API available through {discovered}."
            if discovered else "No canonical Knowledge public API discovered.",
            (discovered,) if discovered else ("Checked: " + ", ".join(candidates),),
            () if discovered else ("Expose one stable Knowledge public API.",),
        )
        return (
            finding,
            self._path_finding(
                "knowledge-verifier", "knowledge", "verification",
                "dev/verify_knowledge_all.sh", True
            ),
        )

    def _audit_acquisition(self):
        return (
            self._path_finding(
                "acquisition-verifier", "acquisition", "verification",
                "dev/verify_phase_7a8.sh", False
            ),
        )

    def _audit_runtime(self):
        return (
            self._module_finding(
                "fastapi-app", "runtime", "application",
                "core.src.main", ("app",)
            ),
            IntegrationFinding(
                "python-runtime", "runtime", "python",
                IntegrationStatus.PASS, "Python runtime available."
            ),
        )

    def _audit_git(self):
        git = shutil.which("git")
        if not git:
            return (IntegrationFinding(
                "git-cli", "git", "repository", IntegrationStatus.FAIL,
                "Git executable unavailable."
            ),)
        result = subprocess.run(
            [git, "rev-parse", "--is-inside-work-tree"],
            cwd=self.project_root, capture_output=True, text=True, check=False
        )
        status = IntegrationStatus.PASS if result.returncode == 0 else IntegrationStatus.PARTIAL
        return (IntegrationFinding(
            "git-repository", "git", "repository", status,
            "Git working tree available." if status is IntegrationStatus.PASS
            else "Project root is not recognized as a Git working tree.",
            (result.stdout.strip() or result.stderr.strip(),),
        ),)

    def _audit_ollama(self):
        executable = shutil.which("ollama")
        if not executable:
            return (IntegrationFinding(
                "ollama-cli", "ollama", "inference_provider",
                IntegrationStatus.PARTIAL, "Ollama CLI not on PATH.",
                (), ("Expose Ollama through the runtime environment.",)
            ),)
        try:
            result = subprocess.run(
                [executable, "list"], cwd=self.project_root,
                capture_output=True, text=True, timeout=10, check=False
            )
        except Exception as exc:
            return (IntegrationFinding(
                "ollama-list", "ollama", "inference_provider",
                IntegrationStatus.PARTIAL, "Ollama inventory unavailable.",
                (f"{type(exc).__name__}: {exc}",)
            ),)
        return (IntegrationFinding(
            "ollama-list", "ollama", "inference_provider",
            IntegrationStatus.PASS if result.returncode == 0 else IntegrationStatus.PARTIAL,
            "Ollama model inventory available."
            if result.returncode == 0 else "Ollama CLI exists but inventory failed.",
            (result.stderr.strip(),) if result.returncode else
            (f"inventory_lines={len([x for x in result.stdout.splitlines() if x.strip()])}",),
        ),)

    def _audit_security(self):
        candidates = (".env", "config/security", "secrets")
        existing = tuple(x for x in candidates if (self.project_root / x).exists())
        return (IntegrationFinding(
            "security-surface", "security", "configuration",
            IntegrationStatus.PARTIAL,
            "Security paths discovered but posture is not yet certified."
            if existing else "No canonical security posture surface discovered.",
            existing,
            ("Add a dedicated security posture verifier.",),
        ),)


def write_report(report: IntegrationAuditReport, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
