"""Deterministic semantic segmentation for Cognitive Representation."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Iterator

from .contracts import (
    ArtifactKind,
    ArtifactReference,
    SegmentKind,
    SegmentationRequest,
    SegmentationResult,
    SemanticSegment,
    SourceSpan,
)

SEGMENTATION_VERSION = "xc1-deterministic-v1"
_BULLET = re.compile(r"^(?:[-*+]\s+|\d+[.)]\s+|[A-Za-z][.)]\s+)")
_KEY_VALUE = re.compile(r"^[^:\n]{1,80}:\s+\S")
_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
_ABBREVIATIONS = frozenset({
    "dr.", "e.g.", "etc.", "i.e.", "jr.", "mr.", "mrs.", "ms.",
    "prof.", "sr.", "st.", "vs.", "u.s.", "u.k.",
})


@dataclass(frozen=True, slots=True)
class _Candidate:
    kind: SegmentKind
    text: str
    start: int
    end: int


class DeterministicSemanticSegmenter:
    version = SEGMENTATION_VERSION

    def segment(self, request: SegmentationRequest) -> SegmentationResult:
        candidates = tuple(self._collect(request.text))
        segments = tuple(
            SemanticSegment(
                segment_id=self._segment_id(request.artifact.artifact_id, candidate),
                artifact=request.artifact,
                ordinal=index,
                kind=candidate.kind,
                text=candidate.text,
                span=SourceSpan(candidate.start, candidate.end),
                metadata={
                    **dict(request.metadata),
                    "segmentation_version": self.version,
                },
            )
            for index, candidate in enumerate(candidates)
        )
        return SegmentationResult(
            artifact=request.artifact,
            segments=segments,
            source_length=len(request.text),
            segmentation_version=self.version,
        )

    def _collect(self, text: str) -> Iterator[_Candidate]:
        for block_start, block_end in self._blocks(text):
            block = text[block_start:block_end]
            if self._is_code(block):
                yield _Candidate(SegmentKind.CODE, block, block_start, block_end)
                continue

            lines = tuple(self._lines(text, block_start, block_end))
            if not lines:
                continue

            if all(self._is_bullet(text[s:e]) for s, e in lines):
                for start, end in lines:
                    yield _Candidate(SegmentKind.BULLET, text[start:end], start, end)
                continue

            if all(self._is_table_row(text[s:e]) for s, e in lines):
                for start, end in lines:
                    yield _Candidate(SegmentKind.TABLE_ROW, text[start:end], start, end)
                continue

            if all(self._is_key_value(text[s:e]) for s, e in lines):
                for start, end in lines:
                    yield _Candidate(SegmentKind.KEY_VALUE, text[start:end], start, end)
                continue

            if len(lines) == 1 and self._is_heading(block):
                yield _Candidate(SegmentKind.HEADING, block, block_start, block_end)
                continue

            for start, end in self._sentences(text, block_start, block_end):
                yield _Candidate(SegmentKind.SENTENCE, text[start:end], start, end)

    @staticmethod
    def _blocks(text: str) -> Iterator[tuple[int, int]]:
        cursor = 0
        for separator in re.finditer(r"(?:\r?\n[ \t]*){2,}", text):
            start, end = DeterministicSemanticSegmenter._trim(text, cursor, separator.start())
            if start < end:
                yield start, end
            cursor = separator.end()
        start, end = DeterministicSemanticSegmenter._trim(text, cursor, len(text))
        if start < end:
            yield start, end

    @staticmethod
    def _lines(text: str, start: int, end: int) -> Iterator[tuple[int, int]]:
        cursor = start
        while cursor < end:
            newline = text.find("\n", cursor, end)
            line_end = end if newline == -1 else newline
            next_cursor = end if newline == -1 else newline + 1
            trimmed = DeterministicSemanticSegmenter._trim(text, cursor, line_end)
            if trimmed[0] < trimmed[1]:
                yield trimmed
            cursor = next_cursor

    def _sentences(self, text: str, start: int, end: int) -> Iterator[tuple[int, int]]:
        sentence_start = start
        index = start
        while index < end:
            if text[index] in ".!?" and self._is_boundary(text, index, sentence_start, end):
                sentence_end = index + 1
                while sentence_end < end and text[sentence_end] in "\"')]}”":
                    sentence_end += 1
                trimmed = self._trim(text, sentence_start, sentence_end)
                if trimmed[0] < trimmed[1]:
                    yield trimmed
                sentence_start = sentence_end
                while sentence_start < end and text[sentence_start].isspace():
                    sentence_start += 1
                index = sentence_start
                continue
            index += 1

        trimmed = self._trim(text, sentence_start, end)
        if trimmed[0] < trimmed[1]:
            yield trimmed

    def _is_boundary(self, text: str, index: int, sentence_start: int, block_end: int) -> bool:
        if text[index] == ".":
            if (
                index > sentence_start
                and index + 1 < block_end
                and text[index - 1].isdigit()
                and text[index + 1].isdigit()
            ):
                return False

            token_start = index
            while token_start > sentence_start and not text[token_start - 1].isspace():
                token_start -= 1
            token = text[token_start:index + 1].lower()
            if token in _ABBREVIATIONS:
                return False
            if len(token) == 2 and token[0].isalpha() and token.endswith("."):
                return False

        lookahead = index + 1
        while lookahead < block_end and text[lookahead] in "\"')]}”":
            lookahead += 1
        return lookahead >= block_end or text[lookahead].isspace()

    @staticmethod
    def _is_bullet(text: str) -> bool:
        return bool(_BULLET.match(text.strip()))

    @staticmethod
    def _is_table_row(text: str) -> bool:
        return bool(_TABLE_ROW.match(text))

    @staticmethod
    def _is_key_value(text: str) -> bool:
        return bool(_KEY_VALUE.match(text.strip()))

    @staticmethod
    def _is_code(text: str) -> bool:
        stripped = text.strip()
        return stripped.startswith("```") and stripped.endswith("```") and len(stripped) >= 6

    @staticmethod
    def _is_heading(text: str) -> bool:
        stripped = text.strip()
        if not stripped:
            return False
        if stripped.startswith("#"):
            return True
        if "\n" in stripped or len(stripped) > 120 or stripped[-1:] in ".!?;,":
            return False
        words = stripped.split()
        if not words or len(words) > 14:
            return False
        letters = [c for c in stripped if c.isalpha()]
        if letters and all(c.isupper() for c in letters):
            return True
        significant = [w for w in words if any(c.isalpha() for c in w)]
        return bool(significant) and sum(w[0].isupper() for w in significant) / len(significant) >= 0.75

    @staticmethod
    def _trim(text: str, start: int, end: int) -> tuple[int, int]:
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        return start, end

    @staticmethod
    def _segment_id(artifact_id: str, candidate: _Candidate) -> str:
        normalized = " ".join(candidate.text.split())
        material = (
            f"{artifact_id}\x1f{candidate.kind.value}\x1f"
            f"{candidate.start}\x1f{candidate.end}\x1f{normalized}"
        )
        return "seg_" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]


def segment_text(
    *,
    artifact_id: str,
    text: str,
    artifact_kind: ArtifactKind = ArtifactKind.TEXT,
) -> SegmentationResult:
    artifact = ArtifactReference(artifact_id=artifact_id, kind=artifact_kind)
    return DeterministicSemanticSegmenter().segment(
        SegmentationRequest(artifact=artifact, text=text)
    )
