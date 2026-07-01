from dataclasses import dataclass


@dataclass
class IndexRecord:
    document_path: str
    filename: str
    extension: str
    category: str | None
    title: str | None
    author: str | None
    subject: str | None
    keywords: str | None
    pages: int | None
    toc_entries: int
    structure_terms: str | None
    language: str | None
    fingerprint: str
