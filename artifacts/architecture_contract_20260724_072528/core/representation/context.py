"""Deterministic bounded context assembly for articulated units."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .articulation import ArticulatedUnit


class ContextAssemblyError(ValueError):
    """Base context assembly failure."""


class EmptyContextError(ContextAssemblyError):
    """No units could be included."""


@dataclass(frozen=True, slots=True)
class ContextPolicy:
    maximum_characters: int = 8000
    maximum_units: int = 12
    include_titles: bool = True
    separator: str = "\n\n"

    def __post_init__(self) -> None:
        if self.maximum_characters < 128:
            raise ValueError("maximum_characters must be at least 128")
        if self.maximum_units < 1:
            raise ValueError("maximum_units must be positive")
        if not self.separator:
            raise ValueError("separator cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextEntry:
    unit_id: str
    sequence: int
    rendered_text: str
    source_segment_ids: tuple[str, ...]
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "sequence": self.sequence,
            "rendered_text": self.rendered_text,
            "source_segment_ids": list(self.source_segment_ids),
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class ContextWindow:
    context_id: str
    source_id: str
    text: str
    entries: tuple[ContextEntry, ...]
    omitted_unit_ids: tuple[str, ...]
    truncated: bool
    metadata: Mapping[str, Any] = field(default_factory=dict)
    fingerprint: str = ""

    def __post_init__(self) -> None:
        if not self.entries or not self.text.strip():
            raise ValueError("context must contain at least one entry")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
        calculated = _fingerprint({
            "context_id": self.context_id,
            "source_id": self.source_id,
            "text": self.text,
            "entries": [entry.to_dict() for entry in self.entries],
            "omitted_unit_ids": list(self.omitted_unit_ids),
            "truncated": self.truncated,
            "metadata": dict(self.metadata),
        })
        if self.fingerprint and self.fingerprint != calculated:
            raise ValueError("fingerprint does not match context")
        object.__setattr__(self, "fingerprint", calculated)

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "source_id": self.source_id,
            "text": self.text,
            "entries": [entry.to_dict() for entry in self.entries],
            "omitted_unit_ids": list(self.omitted_unit_ids),
            "truncated": self.truncated,
            "metadata": dict(self.metadata),
            "fingerprint": self.fingerprint,
        }


class ContextAssembler:
    """Assemble ordered units under explicit character and unit budgets."""

    def __init__(self, policy: ContextPolicy | None = None) -> None:
        self.policy = policy or ContextPolicy()

    def assemble(
        self,
        units: Iterable[ArticulatedUnit],
        *,
        source_id: str,
        context_label: str = "reasoning_context",
    ) -> ContextWindow:
        ordered = tuple(sorted(units, key=lambda item: (item.sequence, item.unit_id)))
        if not ordered:
            raise EmptyContextError("No articulated units were supplied")

        entries: list[ContextEntry] = []
        parts: list[str] = []
        omitted: list[str] = []

        for unit in ordered:
            rendered = (
                f"{unit.title}\n{unit.text}".strip()
                if self.policy.include_titles and unit.title
                else unit.text.strip()
            )
            projected = self.policy.separator.join((*parts, rendered))
            if (
                len(entries) >= self.policy.maximum_units
                or len(projected) > self.policy.maximum_characters
            ):
                omitted.append(unit.unit_id)
                continue

            entries.append(ContextEntry(
                unit_id=unit.unit_id,
                sequence=unit.sequence,
                rendered_text=rendered,
                source_segment_ids=unit.source_segment_ids,
                fingerprint=unit.fingerprint,
            ))
            parts.append(rendered)

        if not entries:
            raise EmptyContextError("Context policy excluded every unit")

        text = self.policy.separator.join(parts)
        context_id = "context_" + _fingerprint({
            "source_id": source_id,
            "context_label": context_label,
            "entries": [entry.fingerprint for entry in entries],
            "policy": {
                "maximum_characters": self.policy.maximum_characters,
                "maximum_units": self.policy.maximum_units,
                "include_titles": self.policy.include_titles,
                "separator": self.policy.separator,
            },
        })[:20]

        return ContextWindow(
            context_id=context_id,
            source_id=source_id,
            text=text,
            entries=tuple(entries),
            omitted_unit_ids=tuple(omitted),
            truncated=bool(omitted),
            metadata={
                "context_label": context_label,
                "included_units": len(entries),
                "omitted_units": len(omitted),
                "character_count": len(text),
            },
        )


def _fingerprint(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")).hexdigest()
