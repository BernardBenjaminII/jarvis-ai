from __future__ import annotations

from core.bootstrap.dependencies import DependencyBootstrap
from core.bootstrap.services.capabilities import verify_capabilities
from core.bootstrap.services.models import ensure_models
from core.bootstrap.services.ollama import ensure_ollama
from core.bootstrap.services.runtime import ensure_runtime
from core.bootstrap.services.venv import ensure_venv


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
        #
        # Runtime
        #

        ensure_runtime(self.paths)

        #
        # Virtual Environment
        #

        ensure_venv(self.paths)

        #
        # Dependencies
        #

        DependencyBootstrap().prepare(self.env)

        #
        # Services
        #

        ensure_ollama(self.paths)

        ensure_models()

        verify_capabilities()

        print("✓ Bootstrap complete")
