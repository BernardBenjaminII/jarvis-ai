from __future__ import annotations

import importlib
import inspect
import pkgutil

from knowledge_engine.director.workflow import Workflow


PACKAGE = "knowledge_engine.director.workflows"


class WorkflowRegistry:

    def __init__(self):

        self._workflows = {}

        self.discover()

    def discover(self):

        package = importlib.import_module(PACKAGE)

        for module in pkgutil.iter_modules(package.__path__):

            mod = importlib.import_module(
                f"{PACKAGE}.{module.name}"
            )

            for _, obj in inspect.getmembers(
                mod,
                inspect.isclass,
            ):

                if (
                    issubclass(obj, Workflow)
                    and obj is not Workflow
                ):

                    workflow = obj()

                    self.register(
                        workflow.intent,
                        workflow,
                    )

    def register(
        self,
        intent,
        workflow,
    ):

        self._workflows[intent] = workflow

    def get(
        self,
        intent,
    ):

        return self._workflows.get(intent)

    def intents(self):

        return sorted(self._workflows)
