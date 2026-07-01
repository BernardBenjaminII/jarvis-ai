from .runtime import RuntimeBootstrap
from .venv import VenvBootstrap
from .dependencies import DependencyBootstrap
from .ollama import OllamaBootstrap
from .models import ModelBootstrap
from .capabilities import CapabilityBootstrap
from .api import ApiBootstrap


class Bootstrap:
    """
    Coordinates all startup stages.
    """

    def run(self):

        runtime = RuntimeBootstrap()

        env, paths = runtime.prepare()

        VenvBootstrap().prepare(paths)

        DependencyBootstrap().prepare(env)

        OllamaBootstrap().prepare(paths)

        ModelBootstrap().prepare()

        CapabilityBootstrap().prepare()

        ApiBootstrap().launch(paths)
