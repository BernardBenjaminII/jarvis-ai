from __future__ import annotations

import re
from pathlib import Path

from .models import MarkdownDocument, MarkdownHeading, MarkdownLink, ParseDiagnostic, RepositoryFile


_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_DOC_ID = re.compile(r"(?im)^\s*(?:\*\*)?Document ID(?:\*\*)?\s*:\s*`?([^`\n]+?)`?\s*$")
_STATUS = re.compile(r"(?im)^\s*(?:\*\*)?Status(?:\*\*)?\s*:\s*([^\n]+?)\s*$")
_ADR_REF = re.compile(r"\bADR-\d{4,}\b", re.IGNORECASE)
_CONST_REF = re.compile(r"\b(?:KM|GOA|CON|CONST|SED|EVOL)-[A-Z0-9-]+\b", re.IGNORECASE)
_ARCH_REF = re.compile(r"\b(?:architecture|architectural)\b", re.IGNORECASE)


class DeterministicMarkdownParser:
    def parse(self, root: Path, file: RepositoryFile) -> MarkdownDocument:
        path = root / file.path
        diagnostics: list[ParseDiagnostic] = []
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            text = path.read_text(encoding="utf-8", errors="replace")
            diagnostics.append(ParseDiagnostic(file.path, "markdown", "Invalid UTF-8 replaced during parsing", exception_type=type(exc).__name__))

        headings: list[MarkdownHeading] = []
        links: list[MarkdownLink] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            heading_match = _HEADING.match(line)
            if heading_match:
                title = heading_match.group(2).strip().strip("#").strip()
                headings.append(MarkdownHeading(len(heading_match.group(1)), title, line_number, _slugify(title)))
            for match in _LINK.finditer(line):
                links.append(MarkdownLink(match.group(1).strip(), match.group(2).strip(), line_number))

        title = next((heading.title for heading in headings if heading.level == 1), None)
        document_id = _first_group(_DOC_ID, text)
        status = _clean_inline(_first_group(_STATUS, text))
        adr_refs = tuple(sorted({item.upper() for item in _ADR_REF.findall(text)}))
        const_refs = tuple(sorted({item.upper() for item in _CONST_REF.findall(text)}))
        arch_refs = tuple(sorted({heading.title for heading in headings if _ARCH_REF.search(heading.title)}))
        return MarkdownDocument(
            repository_id=file.repository_id,
            path=file.path,
            title=title,
            document_id=_clean_inline(document_id),
            status=status,
            headings=tuple(headings),
            links=tuple(links),
            adr_references=adr_refs,
            constitutional_references=const_refs,
            architecture_references=arch_refs,
            diagnostics=tuple(diagnostics),
        )


def _first_group(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def _clean_inline(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().strip("`*_ ") or None


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9\s-]", "", value.lower())
    slug = re.sub(r"[\s-]+", "-", slug).strip("-")
    return slug
