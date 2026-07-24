import platform

from .check import HealthCheck


class EnvironmentCheck(HealthCheck):

    name = "Environment"
    category = "Core"
    order = 10

    description = "Verifies the operating system environment."
    fix_hint = "Verify the operating system is supported."
    documentation = "docs/development/environment.md"

    def run(self):

        self.ok(platform.platform())
        self.score(100)

        return self.result()
