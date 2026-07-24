from __future__ import annotations

import re
import unicodedata


class ObservationNormalizer:
    """Deterministically normalize observation text."""

    _whitespace = re.compile(r"\s+")

    def normalize(self, content: str) -> str:
        normalized = unicodedata.normalize("NFKC", content)
        normalized = self._whitespace.sub(" ", normalized).strip()
        return normalized


__all__ = ("ObservationNormalizer",)
