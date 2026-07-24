from __future__ import annotations

import importlib
from pathlib import Path

from .check import HealthCheck

ROOT = Path(__file__).resolve().parents[2]


class BootstrapCheck(HealthCheck):

    name = "Bootstrap"
    category = "Core"
    order = 15

    description = "Verifies the canonical bootstrap architecture."
    fix_hint = "Restore missing bootstrap modules."
    documentation = "docs/architecture/bootstrap_canonical.md"

    REQUIRED_PATHS = [
        "core/bootstrap/main.py",
        "core/bootstrap/runner.py",
        "core/bootstrap/preflight_runner.py",
        "core/bootstrap/lifecycle_runner.py",
        "core/bootstrap/discovery",
        "core/bootstrap/services",
        "core/bootstrap/lifecycle",
    ]

    REQUIRED_IMPORTS = [
        "core.bootstrap.main",
        "core.bootstrap.runner",
        "core.bootstrap.lifecycle_runner",
	"core.bootstrap.preflight_runner",
	"core.bootstrap.runner",
        "core.bootstrap.discovery.platform",
        "core.bootstrap.discovery.locator",
        "core.bootstrap.discovery.paths",
    ]

    def run(self):

        missing = []
        import_failures = 0

        #
        # Directory / file verification
        #
        for item in self.REQUIRED_PATHS:

            path = ROOT / item

            if path.exists():
                self.detail(f"✓ {item}")
            else:
                missing.append(item)

        #
        # Import verification
        #
        for module in self.REQUIRED_IMPORTS:

            try:
                importlib.import_module(module)
                self.detail(f"✓ import {module}")

            except Exception as exc:
                self.fail(f"{module}: {exc}")
                import_failures += 1

        #
        # Missing files
        #
        if missing:
            self.fail(
                "Missing: " + ", ".join(missing)
            )

        total = len(self.REQUIRED_PATHS) + len(self.REQUIRED_IMPORTS)
        passed = total - len(missing) - import_failures

        score = round((passed / total) * 100)

        self.score(score)

        return self.result()
