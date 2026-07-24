"""Deterministic first-pass compiler for operator requests."""
from __future__ import annotations

import re
from uuid import uuid4

from core.conversation.contracts import CompiledObjective


_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("knowledge", ("what do you know", "catalog", "source", "document", "explain", "compare")),
    ("reasoning", ("why", "reason", "evaluate", "assess", "infer", "conclusion")),
    ("planning", ("plan", "schedule", "roadmap", "prepare", "organize", "strategy")),
    ("engineering", ("code", "program", "python", "api", "debug", "implement", "architecture")),
    ("operations", ("status", "mission", "health", "runtime", "resource", "current activity")),
    ("acquisition", ("download", "research", "find sources", "ingest", "acquire")),
)


class ExecutiveRequestCompiler:
    """Split compound natural-language requests without claiming semantic certainty."""

    _separator = re.compile(
        r"(?:[;\n]+|(?<=[.!?])\s+|\s+(?:and then|then|also|as well as)\s+)",
        re.IGNORECASE,
    )

    def compile(self, operator_input: str) -> tuple[CompiledObjective, ...]:
        text = " ".join(operator_input.strip().split())
        if not text:
            raise ValueError("Operator input cannot be empty")

        candidates = [part.strip(" ,") for part in self._separator.split(text)]
        candidates = [part for part in candidates if part]
        if not candidates:
            candidates = [text]

        return tuple(
            CompiledObjective(
                objective_id=uuid4().hex,
                text=part,
                ordinal=index,
                routing_hints=self._routing_hints(part),
            )
            for index, part in enumerate(candidates, start=1)
        )

    @staticmethod
    def _routing_hints(text: str) -> tuple[str, ...]:
        lowered = text.lower()
        matched = [name for name, markers in _HINTS if any(marker in lowered for marker in markers)]
        return tuple(matched or ["executive"])
