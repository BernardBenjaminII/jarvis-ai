from core.bootstrap.dependencies import DependencyBootstrap
from core.bootstrap.services.runtime import ensure_runtime
from core.bootstrap.services.venv import ensure_venv


def run(env, paths):
    """
    Execute all preflight bootstrap tasks.
    """

    ensure_runtime(paths)

    ensure_venv(paths)

    DependencyBootstrap().prepare(env)
