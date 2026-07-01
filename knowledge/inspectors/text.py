from pathlib import Path

from .base import BaseInspector


class TextInspector(BaseInspector):

    extensions = (
        ".txt",
        ".log",
    )

    def inspect(self, path: Path):

        text = path.read_text(
            errors="ignore"
        )

        return {

            "lines": len(text.splitlines()),

            "words": len(text.split()),

            "characters": len(text),
        }
