from __future__ import annotations

from core.bootstrap.preflight_runner import BootstrapRunner as PreflightRunner
from core.bootstrap.lifecycle_runner import BootstrapRunner as LifecycleRunner


class BootstrapRunner:
    """
    Canonical bootstrap orchestrator.

    Coordinates validation and lifecycle startup.
    """

    def __init__(self, env=None, paths=None):
        self.env = env
        self.paths = paths

    def run(self):

        #
        # Validation
        #

        if not PreflightRunner().run():
            return False

        #
        # Lifecycle
        #

        if self.env is not None and self.paths is not None:
            LifecycleRunner(self.env, self.paths).run()

        return True
