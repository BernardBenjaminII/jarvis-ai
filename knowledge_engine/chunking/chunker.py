from __future__ import annotations

import re
from dataclasses import dataclass

from knowledge_engine.chunking.strategies import chunk_text


@dataclass(frozen=True)
class ChunkingResult:
    chunks: list[str]
    strategy: str


class DocumentChunker:
    def __init__(
        self,
        max_chars: int = 2400,
        overlap: int = 250,
    ) -> None:
        self.max_chars = max_chars
        self.overlap = overlap

    def chunk(self, text: str, file_path: str | None = None) -> ChunkingResult:
        text = self._normalize(text)

        if not text:
            return ChunkingResult(chunks=[], strategy="empty")

        if self._looks_like_code(file_path, text):
            return ChunkingResult(
                chunks=self._chunk_code(text),
                strategy="code_blocks",
            )

        if self._looks_like_markdown(file_path, text):
            return ChunkingResult(
                chunks=self._chunk_markdown(text),
                strategy="markdown_heading",
            )

        return ChunkingResult(
            chunks=chunk_text(
                text,
                max_chars=self.max_chars,
                overlap=self.overlap,
            ),
            strategy="paragraph_window",
        )

    def _normalize(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _looks_like_markdown(self, file_path: str | None, text: str) -> bool:
        if file_path and file_path.lower().endswith((".md", ".markdown")):
            return True

        return bool(re.search(r"(?m)^#{1,6}\s+\S+", text))

    def _looks_like_code(self, file_path: str | None, text: str) -> bool:
        if file_path and file_path.lower().endswith(
            (
                ".py",
                ".js",
                ".ts",
                ".java",
                ".c",
                ".cpp",
                ".h",
                ".hpp",
                ".rs",
                ".go",
                ".sh",
                ".ps1",
                ".sql",
                ".html",
                ".css",
            )
        ):
            return True

        code_signals = [
            "def ",
            "class ",
            "import ",
            "#include",
            "function ",
            "public static",
            "SELECT ",
            "CREATE TABLE",
        ]

        return sum(signal in text for signal in code_signals) >= 2

    def _chunk_markdown(self, text: str) -> list[str]:
        sections: list[str] = []
        current: list[str] = []

        for line in text.splitlines():
            if re.match(r"^#{1,6}\s+\S+", line) and current:
                sections.append("\n".join(current).strip())
                current = [line]
            else:
                current.append(line)

        if current:
            sections.append("\n".join(current).strip())

        final_chunks: list[str] = []

        for section in sections:
            if len(section) <= self.max_chars:
                final_chunks.append(section)
            else:
                final_chunks.extend(
                    chunk_text(
                        section,
                        max_chars=self.max_chars,
                        overlap=self.overlap,
                    )
                )

        return [chunk for chunk in final_chunks if chunk.strip()]

    def _chunk_code(self, text: str) -> list[str]:
        lines = text.splitlines()
        chunks: list[str] = []
        current: list[str] = []
        current_len = 0

        boundary = re.compile(
            r"^\s*(def|class|function|public|private|protected|async def)\s+"
        )

        for line in lines:
            line_len = len(line) + 1

            if (
                current
                and boundary.match(line)
                and current_len >= self.max_chars // 2
            ):
                chunks.append("\n".join(current).strip())
                current = []
                current_len = 0

            if current_len + line_len > self.max_chars and current:
                chunks.append("\n".join(current).strip())
                overlap_lines = current[-8:] if self.overlap > 0 else []
                current = overlap_lines[:]
                current_len = sum(len(x) + 1 for x in current)

            current.append(line)
            current_len += line_len

        if current:
            chunks.append("\n".join(current).strip())

        return [chunk for chunk in chunks if chunk.strip()]
