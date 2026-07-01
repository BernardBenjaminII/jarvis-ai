from pathlib import Path

import fitz

from .base import BaseInspector


class PDFInspector(BaseInspector):

    extensions = (".pdf",)

    def inspect(self, path: Path) -> dict:

        pdf = fitz.open(path)

        metadata = pdf.metadata or {}

        text_length = 0

        for page in pdf:
            text_length += len(page.get_text())

        return {

            "pages": pdf.page_count,

            "title": metadata.get("title"),

            "author": metadata.get("author"),

            "producer": metadata.get("producer"),

            "encrypted": pdf.is_encrypted,

            "text_length": text_length,

            "searchable": text_length > 0,
        }
