from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class OCRPolicy:
    dpi: int = 180
    max_pages: int = 80
    max_seconds_per_page: int = 45
    minimum_chars: int = 120
    minimum_quality: float = 0.45
    max_render_pixels: int = 18_000_000
    languages: str = "eng"

@dataclass(frozen=True, slots=True)
class OCRCandidateResult:
    candidate_id: str
    path: str
    status: str
    strategy: str
    detail: str
    text: str = ""
    chars: int = 0
    pages_total: int = 0
    pages_attempted: int = 0
    pages_recovered: int = 0
    quality_score: float = 0.0
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
