from pathlib import Path

from .check import HealthCheck


class RuntimeCheck(HealthCheck):

    name = "Runtime"
    category = "Core"
    order = 20

    description = "Verifies the runtime storage."
    fix_hint = "Mount the runtime disk."
    documentation = "docs/development/runtime.md"

    def run(self):

        runtime = Path("/media/abdullah/JARVIS_RUNTIME_L")

        if runtime.exists():
            self.detail(str(runtime))
            self.score(100)
        else:
            self.fail("Runtime directory not found")
            self.score(0)

        return self.result()
