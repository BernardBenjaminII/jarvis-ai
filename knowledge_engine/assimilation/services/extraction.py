"""
Canonical extraction and chunking service for JARVIS assimilation.

This service owns:

- validating a source-document path
- extracting text through the existing format-aware extractor
- normalizing extracted text
- generating a deterministic checksum
- generating document chunks

It does not:

- open database connections
- modify registry or queue state
- persist document text or chunks
- create or update attempt-journal rows
- commit or roll back transactions
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from knowledge_engine.assimilation.single_document import (
    checksum,
    chunk_text,
    read_text,
)


@dataclass(frozen=True)
class ExtractionResult:
    """Immutable output from one document extraction operation."""

    document_path: str
    extractor: str
    normalized_text: str
    checksum: str
    chunks: tuple[str, ...]

    @property
    def text_chars(self) -> int:
        return len(self.normalized_text)

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    @property
    def usable(self) -> bool:
        return self.text_chars > 0 and self.chunk_count > 0


class ExtractionService:
    """Extract and chunk one supported single-document source."""

    DEFAULT_EXTRACTOR = "single_document_assimilation"

    def __init__(
        self,
        *,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        extractor_name: str = DEFAULT_EXTRACTOR,
    ):
        if chunk_size < 1:
            raise ValueError("chunk_size must be at least 1")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must not be negative")

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size"
            )

        if not extractor_name.strip():
            raise ValueError("extractor_name must not be empty")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.extractor_name = extractor_name

    def extract(
        self,
        *,
        document_path: str,
    ) -> ExtractionResult:
        """Extract, normalize, checksum, and chunk one source document."""

        if not document_path.strip():
            raise ValueError("document_path must not be empty")

        path = Path(document_path).expanduser()

        self._validate_source_path(path)

        raw_text = read_text(path)
        normalized_text = self.normalize_text(raw_text)

        if not normalized_text:
            raise RuntimeError(
                f"Document extraction produced no usable text: {path}"
            )

        text_checksum = checksum(normalized_text)

        chunks = chunk_text(
            normalized_text,
            chunk_size=self.chunk_size,
            overlap=self.chunk_overlap,
        )

        normalized_chunks = tuple(
            chunk.strip()
            for chunk in chunks
            if chunk and chunk.strip()
        )

        if not normalized_chunks:
            raise RuntimeError(
                f"Document chunking produced no usable chunks: {path}"
            )

        return ExtractionResult(
            document_path=str(path),
            extractor=self.extractor_name,
            normalized_text=normalized_text,
            checksum=text_checksum,
            chunks=normalized_chunks,
        )

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Preserve current assimilation behavior.

        Existing document assimilation normalized extracted text by stripping
        leading and trailing whitespace. More advanced normalization can be
        introduced later behind this service without changing the runner.
        """

        return text.strip()

    @staticmethod
    def _validate_source_path(path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(
                f"Source document does not exist: {path}"
            )

        if not path.is_file():
            raise RuntimeError(
                f"Source document is not a regular file: {path}"
            )
