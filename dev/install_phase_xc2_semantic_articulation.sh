#!/usr/bin/env bash
set -Eeuo pipefail

# JARVIS PHASE X-C2 — SEMANTIC ARTICULATION AND CONTEXT ASSEMBLY

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
BACKUP_ROOT="${PROJECT_ROOT}/artifacts/backups/phase_xc2_$(date -u +%Y%m%dT%H%M%SZ)"

cd "${PROJECT_ROOT}"

echo
echo "======================================================================"
echo "JARVIS PHASE X-C2 — SEMANTIC ARTICULATION AND CONTEXT ASSEMBLY"
echo "======================================================================"
echo "Project root : ${PROJECT_ROOT}"
echo "Python       : ${PYTHON_BIN}"
echo "Backup root  : ${BACKUP_ROOT}"
echo "======================================================================"
echo

command -v "${PYTHON_BIN}" >/dev/null 2>&1 || {
    echo "[FAIL] Python executable not found: ${PYTHON_BIN}" >&2
    exit 1
}

for prerequisite in \
    core/representation/contracts.py \
    core/representation/segmentation.py
do
    [[ -f "${prerequisite}" ]] || {
        echo "[FAIL] Phase X-C1 prerequisite missing: ${prerequisite}" >&2
        exit 1
    }
done

mkdir -p core/representation dev/verification docs/architecture tests "${BACKUP_ROOT}"

backup_file() {
    local path="$1"
    if [[ -f "${path}" ]]; then
        mkdir -p "${BACKUP_ROOT}/$(dirname "${path}")"
        cp -a "${path}" "${BACKUP_ROOT}/${path}"
        echo "[BACKUP] ${path}"
    fi
}

for path in \
    core/representation/articulation.py \
    core/representation/context.py \
    tests/test_phase_xc2_semantic_articulation.py \
    dev/verification/verify_phase_xc2_semantic_articulation.py \
    dev/verify_phase_xc2.sh \
    docs/architecture/cognitive_semantic_articulation.md
do
    backup_file "${path}"
done

cat > core/representation/articulation.py <<'PYEOF'
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
PYEOF

cat > core/representation/context.py <<'PYEOF'
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
PYEOF

cat > tests/test_phase_xc2_semantic_articulation.py <<'PYEOF'
"""Phase X-C2 tests."""

from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from typing import Any

from core.representation.articulation import (
    ArticulationKind,
    ArticulationPolicy,
    EmptyArticulationInputError,
    SemanticArticulator,
)
from core.representation.context import (
    ContextAssembler,
    ContextPolicy,
    EmptyContextError,
)


@dataclass(frozen=True)
class Segment:
    segment_id: str
    ordinal: int
    kind: str
    text: str
    provenance: dict[str, Any] = field(default_factory=dict)


def segments() -> tuple[Segment, ...]:
    return (
        Segment("h", 0, "heading", "Operational Readiness",
                {"source_id": "xc2_fixture"}),
        Segment("s1", 1, "sentence",
                "JARVIS preserves deterministic representations.",
                {"source_id": "xc2_fixture"}),
        Segment("s2", 2, "sentence",
                "Every unit retains source identity.",
                {"source_id": "xc2_fixture"}),
        Segment("b1", 3, "bullet",
                "Reasoning consumes bounded context.",
                {"source_id": "xc2_fixture"}),
        Segment("b2", 4, "bullet",
                "Mission execution remains outside this phase.",
                {"source_id": "xc2_fixture"}),
    )


class ArticulationTests(unittest.TestCase):
    def test_groups_prose_and_lists(self) -> None:
        result = SemanticArticulator().articulate(segments())
        self.assertEqual(result.source_id, "xc2_fixture")
        self.assertEqual(len(result.units), 2)
        self.assertEqual(result.units[0].kind, ArticulationKind.PARAGRAPH)
        self.assertEqual(result.units[1].kind, ArticulationKind.LIST)
        self.assertEqual(result.units[0].title, "Operational Readiness")

    def test_preserves_traceability(self) -> None:
        result = SemanticArticulator().articulate(segments())
        self.assertEqual(result.units[0].source_segment_ids, ("s1", "s2"))
        self.assertEqual(result.units[1].source_segment_ids, ("b1", "b2"))

    def test_is_order_independent_after_ordinal_sort(self) -> None:
        first = SemanticArticulator().articulate(segments())
        second = SemanticArticulator().articulate(tuple(reversed(segments())))
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_provenance_is_immutable(self) -> None:
        result = SemanticArticulator().articulate(segments())
        with self.assertRaises(TypeError):
            result.units[0].segment_references[0].provenance["x"] = 1  # type: ignore[index]

    def test_character_budget_splits_units(self) -> None:
        result = SemanticArticulator(
            ArticulationPolicy(max_unit_characters=64)
        ).articulate(segments())
        self.assertGreaterEqual(len(result.units), 3)

    def test_accepts_mapping_segments(self) -> None:
        result = SemanticArticulator().articulate(({
            "id": "m1",
            "index": 0,
            "type": "sentence",
            "content": "Mapping-shaped segments remain compatible.",
            "metadata": {"source_id": "mapping"},
        },))
        self.assertEqual(result.source_id, "mapping")
        self.assertEqual(result.units[0].source_segment_ids, ("m1",))

    def test_empty_input_fails(self) -> None:
        with self.assertRaises(EmptyArticulationInputError):
            SemanticArticulator().articulate(())


class ContextTests(unittest.TestCase):
    def test_builds_bounded_context(self) -> None:
        articulation = SemanticArticulator().articulate(segments())
        context = ContextAssembler().assemble(
            articulation.units,
            source_id=articulation.source_id,
        )
        self.assertFalse(context.truncated)
        self.assertEqual(len(context.entries), 2)
        self.assertIn("Operational Readiness", context.text)

    def test_context_preserves_segment_ids(self) -> None:
        articulation = SemanticArticulator().articulate(segments())
        context = ContextAssembler().assemble(
            articulation.units,
            source_id=articulation.source_id,
        )
        self.assertEqual(context.entries[0].source_segment_ids, ("s1", "s2"))

    def test_context_budget_records_omissions(self) -> None:
        articulation = SemanticArticulator().articulate(segments())
        context = ContextAssembler(ContextPolicy(
            maximum_characters=180,
            maximum_units=1,
        )).assemble(articulation.units, source_id=articulation.source_id)
        self.assertTrue(context.truncated)
        self.assertEqual(len(context.entries), 1)
        self.assertEqual(len(context.omitted_unit_ids), 1)

    def test_context_is_deterministic(self) -> None:
        articulation = SemanticArticulator().articulate(segments())
        assembler = ContextAssembler()
        first = assembler.assemble(
            articulation.units,
            source_id=articulation.source_id,
        )
        second = assembler.assemble(
            tuple(reversed(articulation.units)),
            source_id=articulation.source_id,
        )
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_empty_context_fails(self) -> None:
        with self.assertRaises(EmptyContextError):
            ContextAssembler().assemble((), source_id="empty")


if __name__ == "__main__":
    unittest.main()
PYEOF

cat > dev/verification/verify_phase_xc2_semantic_articulation.py <<'PYEOF'
#!/usr/bin/env python3
"""Verification for Phase X-C2."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PYTHON_BIN = os.environ.get("PYTHON_BIN") or sys.executable

FILES = (
    Path("core/representation/contracts.py"),
    Path("core/representation/segmentation.py"),
    Path("core/representation/articulation.py"),
    Path("core/representation/context.py"),
    Path("tests/test_phase_xc2_semantic_articulation.py"),
    Path("docs/architecture/cognitive_semantic_articulation.md"),
    Path("dev/verify_phase_xc2.sh"),
)

SYMBOLS = {
    Path("core/representation/articulation.py"): {
        "ArticulationKind", "SegmentReference", "ArticulatedUnit",
        "ArticulationResult", "ArticulationPolicy", "SemanticArticulator",
    },
    Path("core/representation/context.py"): {
        "ContextPolicy", "ContextEntry", "ContextWindow", "ContextAssembler",
    },
}


class Failure(RuntimeError):
    pass


def run(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT), "PYTHON_BIN": PYTHON_BIN},
        capture_output=True,
        text=True,
        check=False,
    )


def required_files() -> None:
    missing = [str(path) for path in FILES if not (ROOT / path).is_file()]
    if missing:
        raise Failure("Missing files: " + ", ".join(missing))


def syntax() -> None:
    for path in FILES:
        if path.suffix == ".py":
            ast.parse((ROOT / path).read_text(encoding="utf-8"), str(path))


def symbols() -> None:
    for path, expected in SYMBOLS.items():
        tree = ast.parse((ROOT / path).read_text(encoding="utf-8"), str(path))
        found = {
            node.name for node in tree.body
            if isinstance(node, (ast.ClassDef, ast.FunctionDef))
        }
        missing = expected - found
        if missing:
            raise Failure(f"{path} missing: {', '.join(sorted(missing))}")


def imports() -> None:
    completed = run(
        PYTHON_BIN,
        "-c",
        "from core.representation.articulation import SemanticArticulator; "
        "from core.representation.context import ContextAssembler",
    )
    if completed.returncode:
        raise Failure(completed.stdout + completed.stderr)


def unit_tests() -> None:
    completed = run(
        PYTHON_BIN,
        "-m",
        "unittest",
        "-v",
        "tests.test_phase_xc2_semantic_articulation",
    )
    if completed.returncode:
        raise Failure(completed.stdout + completed.stderr)


def deterministic_smoke() -> None:
    script = """
from dataclasses import dataclass
from core.representation.articulation import SemanticArticulator
from core.representation.context import ContextAssembler
@dataclass(frozen=True)
class S:
    segment_id: str
    ordinal: int
    kind: str
    text: str
    provenance: dict
s = (
    S("h", 0, "heading", "Readiness", {"source_id": "smoke"}),
    S("a", 1, "sentence", "One statement.", {"source_id": "smoke"}),
    S("b", 2, "sentence", "Second statement.", {"source_id": "smoke"}),
)
a = SemanticArticulator().articulate(s)
b = SemanticArticulator().articulate(tuple(reversed(s)))
assert a.fingerprint == b.fingerprint
ca = ContextAssembler().assemble(a.units, source_id=a.source_id)
cb = ContextAssembler().assemble(b.units, source_id=b.source_id)
assert ca.fingerprint == cb.fingerprint
"""
    completed = run(PYTHON_BIN, "-c", script)
    if completed.returncode:
        raise Failure(completed.stdout + completed.stderr)


def boundaries() -> None:
    forbidden = (
        "core.executive", "core.mission", "core.planning",
        "knowledge_engine", "openai", "ollama", "requests", "httpx",
    )
    for path in (
        Path("core/representation/articulation.py"),
        Path("core/representation/context.py"),
    ):
        tree = ast.parse((ROOT / path).read_text(encoding="utf-8"), str(path))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        bad = [
            name for name in imported
            if any(name == root or name.startswith(root + ".") for root in forbidden)
        ]
        if bad:
            raise Failure(f"{path} boundary violations: {', '.join(bad)}")


def main() -> int:
    checks = (
        ("Phase X-C1 prerequisites and X-C2 files", required_files),
        ("Python syntax", syntax),
        ("Required symbols", symbols),
        ("Stable module imports", imports),
        ("Unit tests", unit_tests),
        ("Deterministic smoke test", deterministic_smoke),
        ("Forward-only boundaries", boundaries),
    )
    failures: list[str] = []

    print()
    print("=" * 70)
    print("JARVIS PHASE X-C2 — SEMANTIC ARTICULATION VERIFICATION")
    print("=" * 70)

    for label, check in checks:
        try:
            check()
            print(f"[PASS] {label}")
        except Exception as exc:
            failures.append(f"{label}: {exc}")
            print(f"[FAIL] {label}: {exc}")

    print("-" * 70)
    print(f"Checks executed : {len(checks)}")
    print(f"Checks failed   : {len(failures)}")
    print("Overall status  : " + ("EXCELLENT" if not failures else "FAILED"))
    print("=" * 70)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
PYEOF

cat > dev/verify_phase_xc2.sh <<'SHEOF'
#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "${PROJECT_ROOT}"
export PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
export PYTHON_BIN

"${PYTHON_BIN}" dev/verification/verify_phase_xc2_semantic_articulation.py
SHEOF

cat > docs/architecture/cognitive_semantic_articulation.md <<'MDEOF'
# Phase X-C2 — Semantic Articulation and Context Assembly

## Status

Implemented as an additive cognitive-representation milestone.

## Purpose

Phase X-C1 converts source material into immutable structural segments.
Phase X-C2 converts those segments into coherent semantic units and bounded
context packages suitable for later reasoning integration.

```text
source
  ↓
X-C1 segmentation
  ↓
X-C2 semantic articulation
  ↓
X-C2 context assembly
  ↓
future X-C3 cognitive interpretation
  ↓
reasoning
```

## Semantic articulation

`SemanticArticulator` applies deterministic grouping rules:

1. Headings establish active section titles.
2. Adjacent prose segments form paragraphs.
3. Adjacent bullet segments form lists.
4. List/prose transitions close the active unit.
5. Character limits split units deterministically.
6. Every unit retains all contributing segment identities and provenance.

The articulator accepts segment-like objects or mappings. This compatibility
boundary keeps X-C2 additive and avoids rewriting X-C1 contracts.

## Context assembly

`ContextAssembler` converts ordered articulated units into a `ContextWindow`
under explicit character and unit budgets.

The result records:

- included units;
- omitted units;
- truncation state;
- source segment identities;
- unit fingerprints;
- context fingerprint.

## Determinism

Equivalent input and policy produce identical unit ordering, identities,
fingerprints, context text, omissions, and context fingerprints. No timestamps,
network calls, database access, or model calls occur.

## Boundaries

Phase X-C2 does not retrieve knowledge, call an LLM, generate hypotheses,
change reasoning confidence, create missions, execute tools, authorize actions,
or change the API/UI.

## Next phase

Phase X-C3 should add deterministic cognitive interpretation over
`ContextWindow` objects: claims, questions, assumptions, constraints, entities,
relationships, and requested outcomes. Execution authority remains excluded.
MDEOF

chmod +x \
    dev/install_phase_xc2_semantic_articulation.sh \
    dev/verify_phase_xc2.sh \
    dev/verification/verify_phase_xc2_semantic_articulation.py

echo
echo "Created Phase X-C2 files:"
printf '  %s\n' \
    core/representation/articulation.py \
    core/representation/context.py \
    tests/test_phase_xc2_semantic_articulation.py \
    dev/verification/verify_phase_xc2_semantic_articulation.py \
    dev/verify_phase_xc2.sh \
    docs/architecture/cognitive_semantic_articulation.md

echo
echo "Running Phase X-C2 verification..."
"${PYTHON_BIN}" dev/verification/verify_phase_xc2_semantic_articulation.py

echo
echo "======================================================================"
echo "PHASE X-C2 INSTALLATION COMPLETE"
echo "======================================================================"
