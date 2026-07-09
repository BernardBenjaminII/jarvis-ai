from __future__ import annotations

import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

from knowledge_engine.processors.base import BaseProcessor, ProcessorResult


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "nav"}:
            self.skip = True

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "nav"}:
            self.skip = False

    def handle_data(self, data):
        if not self.skip:
            cleaned = data.strip()
            if cleaned:
                self.parts.append(cleaned)

    def text(self) -> str:
        return "\n".join(self.parts)


class DocumentProcessor(BaseProcessor):
    name = "document_processor"
    content_type = "document"

    extensions = {
        ".pdf",
        ".epub",
        ".docx",
        ".md",
        ".txt",
        ".rtf",
        ".html",
        ".htm",
        ".xhtml",
    }

    def process(self, path: Path) -> ProcessorResult:
        try:
            text = self._extract_text(path)

            return ProcessorResult(
                file_path=str(path),
                processor=self.name,
                content_type=self.content_type,
                text=text,
                metadata={
                    "extension": path.suffix.lower(),
                    "filename": path.name,
                },
                status="processed" if text.strip() else "empty",
                error=None if text.strip() else "no text extracted",
            )

        except Exception as exc:
            return ProcessorResult(
                file_path=str(path),
                processor=self.name,
                content_type=self.content_type,
                text="",
                metadata={
                    "extension": path.suffix.lower(),
                    "filename": path.name,
                },
                status="failed",
                error=str(exc),
            )

    def _extract_text(self, path: Path) -> str:
        ext = path.suffix.lower()

        if ext in {".txt", ".md"}:
            return path.read_text(encoding="utf-8", errors="ignore")

        if ext == ".rtf":
            return self._read_rtf(path)

        if ext in {".html", ".htm", ".xhtml"}:
            return self._read_html(path)

        if ext == ".docx":
            return self._read_docx(path)

        if ext == ".epub":
            return self._read_epub(path)

        if ext == ".pdf":
            return self._read_pdf(path)

        return ""

    def _read_rtf(self, path: Path) -> str:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        raw = re.sub(r"{\\.*?}|\\[a-z]+\d* ?", " ", raw)
        raw = raw.replace("{", " ").replace("}", " ")
        return re.sub(r"\s+", " ", raw).strip()

    def _read_html(self, path: Path) -> str:
        parser = _HTMLTextExtractor()
        parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
        return parser.text()

    def _read_docx(self, path: Path) -> str:
        texts: list[str] = []

        with zipfile.ZipFile(path) as zf:
            xml = zf.read("word/document.xml")

        root = ET.fromstring(xml)
        ns = {
            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        }

        for node in root.findall(".//w:t", ns):
            if node.text:
                texts.append(node.text)

        return "\n".join(texts)

    def _read_epub(self, path: Path) -> str:
        texts: list[str] = []

        with zipfile.ZipFile(path) as zf:
            names = sorted(
                name
                for name in zf.namelist()
                if name.lower().endswith((".html", ".htm", ".xhtml"))
            )

            for name in names:
                try:
                    raw = zf.read(name).decode("utf-8", errors="ignore")
                    parser = _HTMLTextExtractor()
                    parser.feed(raw)
                    chunk = parser.text()
                    if chunk:
                        texts.append(chunk)
                except Exception:
                    continue

        return "\n\n".join(texts)

    def _read_pdf(self, path: Path) -> str:
        """
        Preferred extraction path:
            1. PDFExtractor (PyMuPDF-based)
            2. pypdf fallback
        """

        try:
            from knowledge_engine.extraction.extractors.pdf import PDFExtractor

            pages = PDFExtractor().extract(path)
            text = "\n\n".join(str(page) for page in pages)

            if text.strip():
                return text

        except Exception:
            pass

        try:
            from pypdf import PdfReader
        except Exception as exc:
            raise RuntimeError(
                "No PDF extractor available. Install pypdf or fix PDFExtractor."
            ) from exc

        reader = PdfReader(str(path))

        pages = []

        for page in reader.pages:
            pages.append(page.extract_text() or "")

        return "\n\n".join(pages)
