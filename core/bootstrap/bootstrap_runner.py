from __future__ import annotations

from core.bootstrap.lifecycle.preflight import run as preflight

from core.bootstrap.lifecycle.startup import run as startup

from core.bootstrap.lifecycle.postflight import run as postflight

class BootstrapRunner:
    """
    Executes the complete JARVIS bootstrap sequence.

    Launcher.py should never know the details of startup.
    It should simply invoke BootstrapRunner.
    """

    def __init__(self, env: str, paths: dict):
        self.env = env
        self.paths = paths

    def run(self):

        print("========== PRE-FLIGHT ==========")
        preflight(self.env, self.paths)

        print("========== STARTUP ==========")
        startup(self.paths)

        print("========== POST-FLIGHT ==========")
        postflight()

        print("✓ Bootstrap complete")
