from __future__ import annotations

from dataclasses import dataclass
import re

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_LIST_PREFIX = re.compile(r"^\s*(?:[-*+] |\d+[.)] )")
_FENCE = re.compile(r"^\s*```")


@dataclass(frozen=True, slots=True)
class MarkdownUnit:
    text: str
    start_line: int
    end_line: int
    section_path: tuple[str, ...]


def extract_units(text: str) -> tuple[MarkdownUnit, ...]:
    lines = text.splitlines()
    sections: list[tuple[int, str]] = []
    units: list[MarkdownUnit] = []
    paragraph: list[str] = []
    paragraph_start = 0
    in_fence = False

    def flush(end_line: int) -> None:
        nonlocal paragraph, paragraph_start
        if not paragraph:
            return
        normalized = " ".join(part.strip() for part in paragraph if part.strip()).strip()
        if normalized:
            units.append(MarkdownUnit(normalized, paragraph_start, end_line, tuple(title for _, title in sections)))
        paragraph = []
        paragraph_start = 0

    for index, line in enumerate(lines, start=1):
        if _FENCE.match(line):
            flush(index - 1)
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        heading = _HEADING.match(line)
        if heading:
            flush(index - 1)
            level, title = len(heading.group(1)), heading.group(2).strip().strip("# ")
            sections = [(n, t) for n, t in sections if n < level]
            sections.append((level, title))
            continue
        if not line.strip():
            flush(index - 1)
            continue
        if _LIST_PREFIX.match(line):
            flush(index - 1)
            item = _LIST_PREFIX.sub("", line, count=1).strip()
            if item:
                units.append(MarkdownUnit(item, index, index, tuple(title for _, title in sections)))
            continue
        if not paragraph:
            paragraph_start = index
        paragraph.append(line)
    flush(len(lines))
    return tuple(units)
