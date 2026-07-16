"""
Narrow adapter for the canonical Phase VI assimilation runner.

The adapter invokes the existing public execution method:

    AssimilationRunner.run_one_single_document(
        expected_object_uuid=...
    )

It contains no SQL, extraction logic, persistence logic, handler selection,
attempt journaling, or state transitions.
"""

from __future__ import annotations

from typing import Any

from knowledge_engine.assimilation.runner import (
    AssimilationRunner,
)


class PhaseVIRunnerExecutionAdapter:
    """Execute one already-registered object through Phase VI."""

    def __init__(
        self,
        runner: AssimilationRunner,
    ) -> None:
        if not isinstance(
            runner,
            AssimilationRunner,
        ):
            raise TypeError(
                "runner must be an AssimilationRunner"
            )

        self.runner = runner

    def execute_registered_object(
        self,
        *,
        object_uuid: str,
    ) -> dict[str, Any]:
        """Execute one canonical Knowledge Registry object."""

        normalized_object_uuid = object_uuid.strip()

        if not normalized_object_uuid:
            raise ValueError(
                "object_uuid must not be empty"
            )

        result = (
            self.runner.run_one_single_document(
                expected_object_uuid=(
                    normalized_object_uuid
                ),
            )
        )

        if not isinstance(result, dict):
            raise TypeError(
                "AssimilationRunner returned a non-dictionary result"
            )

        return dict(result)


__all__ = [
    "PhaseVIRunnerExecutionAdapter",
]
