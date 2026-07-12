"""
Canonical persistence operations for assimilated document content.

This service owns writes to:

- document_text
- chunks

It does not:

- open database connections
- begin transactions
- commit or roll back transactions
- update registry or queue states
- update attempt-journal records

The caller owns transaction boundaries.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class DocumentPersistenceResult:
    """Summary of one document persistence operation."""

    document_path: str
    text_chars: int
    chunk_count: int
    checksum: str
    extractor: str

    @property
    def persisted(self) -> bool:
        """Return whether document text and at least one chunk were stored."""

        return self.text_chars > 0 and self.chunk_count > 0


class DocumentPersistenceService:
    """Persist extracted document text and replace its chunk set."""

    DEFAULT_EXTRACTOR = "single_document_assimilation"

    def persist_document(
        self,
        *,
        conn: sqlite3.Connection,
        document_path: str,
        text: str,
        checksum: str,
        chunks: Sequence[str],
        extractor: str = DEFAULT_EXTRACTOR,
    ) -> DocumentPersistenceResult:
        """
        Upsert extracted text and replace all chunks for one document.

        The operation is transaction-neutral. The caller must commit or roll
        back the surrounding transaction.
        """

        normalized_text = text.strip()

        if not normalized_text:
            raise ValueError("text must contain non-whitespace content")

        normalized_chunks = [
            chunk.strip()
            for chunk in chunks
            if chunk and chunk.strip()
        ]

        if not normalized_chunks:
            raise ValueError("chunks must contain at least one usable chunk")

        if not document_path.strip():
            raise ValueError("document_path must not be empty")

        if not checksum.strip():
            raise ValueError("checksum must not be empty")

        if not extractor.strip():
            raise ValueError("extractor must not be empty")

        self.upsert_document_text(
            conn=conn,
            document_path=document_path,
            text=normalized_text,
            checksum=checksum,
            extractor=extractor,
        )

        self.replace_chunks(
            conn=conn,
            document_path=document_path,
            chunks=normalized_chunks,
        )

        return DocumentPersistenceResult(
            document_path=document_path,
            text_chars=len(normalized_text),
            chunk_count=len(normalized_chunks),
            checksum=checksum,
            extractor=extractor,
        )

    @staticmethod
    def upsert_document_text(
        *,
        conn: sqlite3.Connection,
        document_path: str,
        text: str,
        checksum: str,
        extractor: str,
    ) -> None:
        """Insert or refresh the extracted text record for one document."""

        conn.execute(
            """
            INSERT INTO document_text (
                document_path,
                extractor,
                text,
                checksum,
                status,
                error
            )
            VALUES (?, ?, ?, ?, 'extracted', NULL)
            ON CONFLICT(document_path) DO UPDATE SET
                extractor=excluded.extractor,
                text=excluded.text,
                checksum=excluded.checksum,
                status=excluded.status,
                error=NULL,
                extracted_at=CURRENT_TIMESTAMP
            """,
            (
                document_path,
                extractor,
                text,
                checksum,
            ),
        )

    @staticmethod
    def replace_chunks(
        *,
        conn: sqlite3.Connection,
        document_path: str,
        chunks: Sequence[str],
    ) -> None:
        """Replace the complete stored chunk set for one document."""

        conn.execute(
            """
            DELETE FROM chunks
            WHERE document_path=?
            """,
            (document_path,),
        )

        conn.executemany(
            """
            INSERT INTO chunks (
                document_path,
                chunk_index,
                text,
                source_page,
                structure_title
            )
            VALUES (?, ?, ?, NULL, NULL)
            """,
            [
                (
                    document_path,
                    index,
                    chunk,
                )
                for index, chunk in enumerate(chunks)
            ],
        )
