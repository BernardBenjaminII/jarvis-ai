from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .contracts import ActivityExecutor, ExecutionContext, ExecutionResult
from .errors import ExecutorUnavailableError


@dataclass
class CallableExecutor:
    capability: str
    handler: Callable[[ExecutionContext], ExecutionResult]

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        return self.handler(context)


class ExecutorRegistry:
    def __init__(self) -> None:
        self._executors: dict[str, ActivityExecutor] = {}

    def register(self, executor: ActivityExecutor) -> None:
        capability = executor.capability.strip()
        if not capability:
            raise ValueError("Executor capability is required.")
        self._executors[capability] = executor

    def resolve(self, capability: str) -> ActivityExecutor:
        key = capability.strip()
        if key not in self._executors:
            raise ExecutorUnavailableError(
                f"No executor is registered for capability {key!r}."
            )
        return self._executors[key]

    def capabilities(self) -> tuple[str, ...]:
        return tuple(sorted(self._executors))
