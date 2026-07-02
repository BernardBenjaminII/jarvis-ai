from dataclasses import dataclass


@dataclass
class LibraryRecord:

    document_path: str

    filename: str

    extension: str

    category: str | None

    provider: str | None

    title: str | None

    subtitle: str | None

    author: str | None

    publisher: str | None

    publication_year: str | None

    edition: str | None

    isbn: str | None

    subject: str | None

    keywords: str | None

    language: str | None

    pages: int | None

    fingerprint: str
