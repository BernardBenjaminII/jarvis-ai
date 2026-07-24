"""Deterministic semantic articulation over Phase X-C1 segments."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any


class ArticulationKind(str, Enum):
    SECTION = "section"
    PARAGRAPH = "paragraph"
    LIST = "list"
    STATEMENT = "statement"


class ArticulationError(ValueError):
    """Base articulation failure."""


class EmptyArticulationInputError(ArticulationError):
    """No usable segments were supplied."""


@dataclass(frozen=True, slots=True)
class SegmentReference:
    segment_id: str
    ordinal: int
    kind: str
    text: str
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.segment_id.strip():
            raise ValueError("segment_id cannot be empty")
        if self.ordinal < 0:
            raise ValueError("ordinal cannot be negative")
        if not self.text.strip():
            raise ValueError("text cannot be empty")
        object.__setattr__(
            self,
            "provenance",
            MappingProxyType(dict(self.provenance)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "ordinal": self.ordinal,
            "kind": self.kind,
            "text": self.text,
            "provenance": dict(self.provenance),
        }


@dataclass(frozen=True, slots=True)
class ArticulatedUnit:
    unit_id: str
    kind: ArticulationKind
    title: str | None
    text: str
    segment_references: tuple[SegmentReference, ...]
    sequence: int
    metadata: Mapping[str, Any] = field(default_factory=dict)
    fingerprint: str = ""

    def __post_init__(self) -> None:
        if not self.unit_id.strip():
            raise ValueError("unit_id cannot be empty")
        if not self.text.strip():
            raise ValueError("text cannot be empty")
        if not self.segment_references:
            raise ValueError("segment_references cannot be empty")
        if self.sequence < 0:
            raise ValueError("sequence cannot be negative")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
        calculated = _fingerprint({
            "unit_id": self.unit_id,
            "kind": self.kind.value,
            "title": self.title,
            "text": self.text,
            "segment_references": [
                item.to_dict() for item in self.segment_references
            ],
            "sequence": self.sequence,
            "metadata": dict(self.metadata),
        })
        if self.fingerprint and self.fingerprint != calculated:
            raise ValueError("fingerprint does not match articulated unit")
        object.__setattr__(self, "fingerprint", calculated)

    @property
    def source_segment_ids(self) -> tuple[str, ...]:
        return tuple(item.segment_id for item in self.segment_references)

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "kind": self.kind.value,
            "title": self.title,
            "text": self.text,
            "segment_references": [
                item.to_dict() for item in self.segment_references
            ],
            "sequence": self.sequence,
            "metadata": dict(self.metadata),
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class ArticulationResult:
    source_id: str
    units: tuple[ArticulatedUnit, ...]
    rejected_segments: int
    fingerprint: str = ""

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id cannot be empty")
        if not self.units:
            raise ValueError("units cannot be empty")
        calculated = _fingerprint({
            "source_id": self.source_id,
            "units": [unit.to_dict() for unit in self.units],
            "rejected_segments": self.rejected_segments,
        })
        if self.fingerprint and self.fingerprint != calculated:
            raise ValueError("fingerprint does not match articulation result")
        object.__setattr__(self, "fingerprint", calculated)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "units": [unit.to_dict() for unit in self.units],
            "rejected_segments": self.rejected_segments,
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class ArticulationPolicy:
    max_unit_characters: int = 2400
    minimum_segment_characters: int = 1
    preserve_headings_as_titles: bool = True

    def __post_init__(self) -> None:
        if self.max_unit_characters < 64:
            raise ValueError("max_unit_characters must be at least 64")
        if self.minimum_segment_characters < 1:
            raise ValueError("minimum_segment_characters must be positive")


class SemanticArticulator:
    """Build coherent units while preserving segment identity and provenance."""

    HEADING_KINDS = {"heading", "header", "title", "section"}
    BULLET_KINDS = {"bullet", "list_item", "list-item", "item"}

    def __init__(self, policy: ArticulationPolicy | None = None) -> None:
        self.policy = policy or ArticulationPolicy()

    def articulate(
        self,
        segments: Iterable[Any],
        *,
        source_id: str | None = None,
    ) -> ArticulationResult:
        normalized, rejected = self._normalize(segments)
        if not normalized:
            raise EmptyArticulationInputError("No usable segments were supplied")

        resolved_source = (
            source_id.strip()
            if source_id and source_id.strip()
            else self._derive_source_id(normalized)
        )
        units: list[ArticulatedUnit] = []
        active_title: str | None = None
        buffer: list[SegmentReference] = []
        buffer_kind: ArticulationKind | None = None

        def flush() -> None:
            nonlocal buffer, buffer_kind
            if not buffer or buffer_kind is None:
                return
            units.extend(self._materialize(
                resolved_source,
                active_title,
                buffer_kind,
                buffer,
                len(units),
            ))
            buffer = []
            buffer_kind = None

        for reference in normalized:
            category = self._category(reference.kind)

            if category is ArticulationKind.SECTION:
                flush()
                active_title = reference.text
                if not self.policy.preserve_headings_as_titles:
                    units.append(self._build_unit(
                        resolved_source,
                        active_title,
                        ArticulationKind.SECTION,
                        (reference,),
                        reference.text,
                        len(units),
                    ))
                continue

            if category is ArticulationKind.LIST:
                if buffer and buffer_kind is not ArticulationKind.LIST:
                    flush()
                buffer_kind = ArticulationKind.LIST
                buffer.append(reference)
                continue

            if buffer and buffer_kind is ArticulationKind.LIST:
                flush()

            if buffer and self._exceeds(buffer, reference):
                flush()

            buffer_kind = (
                ArticulationKind.PARAGRAPH
                if category is ArticulationKind.PARAGRAPH
                else ArticulationKind.STATEMENT
            )
            buffer.append(reference)

        flush()

        if not units and active_title:
            heading = next(
                item for item in normalized if item.text == active_title
            )
            units.append(self._build_unit(
                resolved_source,
                active_title,
                ArticulationKind.SECTION,
                (heading,),
                heading.text,
                0,
            ))

        return ArticulationResult(
            source_id=resolved_source,
            units=tuple(units),
            rejected_segments=rejected,
        )

    def _normalize(
        self,
        segments: Iterable[Any],
    ) -> tuple[tuple[SegmentReference, ...], int]:
        accepted: list[SegmentReference] = []
        rejected = 0

        for fallback, raw in enumerate(segments):
            text = _text(raw)
            if len(text) < self.policy.minimum_segment_characters:
                rejected += 1
                continue
            kind = _kind(raw)
            ordinal = _ordinal(raw, fallback)
            segment_id = _identifier(raw, ordinal, kind, text)
            accepted.append(SegmentReference(
                segment_id=segment_id,
                ordinal=ordinal,
                kind=kind,
                text=text,
                provenance=_provenance(raw),
            ))

        accepted.sort(key=lambda item: (item.ordinal, item.segment_id))
        return tuple(accepted), rejected

    def _materialize(
        self,
        source_id: str,
        title: str | None,
        kind: ArticulationKind,
        references: Sequence[SegmentReference],
        start: int,
    ) -> list[ArticulatedUnit]:
        groups: list[list[SegmentReference]] = []
        current: list[SegmentReference] = []

        for reference in references:
            if current and self._exceeds(current, reference):
                groups.append(current)
                current = []
            current.append(reference)
        if current:
            groups.append(current)

        return [
            self._build_unit(
                source_id,
                title,
                kind,
                tuple(group),
                self._compose(kind, group),
                start + offset,
            )
            for offset, group in enumerate(groups)
        ]

    def _build_unit(
        self,
        source_id: str,
        title: str | None,
        kind: ArticulationKind,
        references: tuple[SegmentReference, ...],
        text: str,
        sequence: int,
    ) -> ArticulatedUnit:
        unit_id = "articulation_" + _fingerprint({
            "source_id": source_id,
            "sequence": sequence,
            "kind": kind.value,
            "segment_ids": [item.segment_id for item in references],
        })[:20]
        return ArticulatedUnit(
            unit_id=unit_id,
            kind=kind,
            title=title,
            text=text,
            segment_references=references,
            sequence=sequence,
            metadata={
                "source_id": source_id,
                "segment_count": len(references),
                "character_count": len(text),
            },
        )

    def _compose(
        self,
        kind: ArticulationKind,
        references: Sequence[SegmentReference],
    ) -> str:
        if kind is ArticulationKind.LIST:
            return "\n".join(
                item.text
                if item.text.startswith(("- ", "* ", "• "))
                else f"- {item.text}"
                for item in references
            )
        return " ".join(item.text for item in references).strip()

    def _exceeds(
        self,
        current: Sequence[SegmentReference],
        candidate: SegmentReference,
    ) -> bool:
        return (
            sum(len(item.text) for item in current)
            + len(current)
            + len(candidate.text)
            > self.policy.max_unit_characters
        )

    def _category(self, kind: str) -> ArticulationKind:
        normalized = kind.casefold().replace("-", "_")
        if normalized in {item.replace("-", "_") for item in self.HEADING_KINDS}:
            return ArticulationKind.SECTION
        if normalized in {item.replace("-", "_") for item in self.BULLET_KINDS}:
            return ArticulationKind.LIST
        if normalized in {
            "sentence", "paragraph", "text", "prose", "unknown"
        }:
            return ArticulationKind.PARAGRAPH
        return ArticulationKind.STATEMENT

    @staticmethod
    def _derive_source_id(
        references: Sequence[SegmentReference],
    ) -> str:
        for reference in references:
            for key in ("source_id", "document_id", "source", "path", "file_path"):
                value = reference.provenance.get(key)
                if value:
                    return str(value)
        return "source_" + _fingerprint(
            [item.to_dict() for item in references]
        )[:20]


def _read(value: Any, names: Sequence[str], default: Any) -> Any:
    if isinstance(value, Mapping):
        for name in names:
            if name in value:
                return value[name]
        return default
    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
    return default


def _text(value: Any) -> str:
    raw = _read(
        value,
        ("text", "content", "value", "body", "normalized_text"),
        "",
    )
    return " ".join(str(raw or "").split())


def _kind(value: Any) -> str:
    raw = _read(value, ("kind", "segment_kind", "type", "category"), "unknown")
    if isinstance(raw, Enum):
        raw = raw.value
    return str(raw or "unknown").strip().casefold()


def _ordinal(value: Any, fallback: int) -> int:
    raw = _read(
        value,
        ("ordinal", "sequence", "index", "position", "segment_index"),
        fallback,
    )
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return fallback


def _identifier(value: Any, ordinal: int, kind: str, text: str) -> str:
    raw = _read(
        value,
        ("segment_id", "id", "identifier", "representation_id"),
        "",
    )
    if raw:
        return str(raw)
    return "segment_" + _fingerprint({
        "ordinal": ordinal,
        "kind": kind,
        "text": text,
    })[:20]


def _provenance(value: Any) -> dict[str, Any]:
    raw = _read(value, ("provenance", "metadata", "source_metadata"), {})
    if hasattr(raw, "to_dict"):
        raw = raw.to_dict()
    elif hasattr(raw, "as_dict"):
        raw = raw.as_dict()
    return dict(raw) if isinstance(raw, Mapping) else {}


def _fingerprint(payload: Any) -> str:
    return hashlib.sha256(json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")).hexdigest()
