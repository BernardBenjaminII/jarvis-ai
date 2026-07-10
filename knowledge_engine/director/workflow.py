from __future__ import annotations

from abc import ABC, abstractmethod


class Workflow(ABC):

    name = "Unnamed Workflow"

    @abstractmethod
    def run(self, request):
        ...
