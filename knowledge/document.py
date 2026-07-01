from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class DocumentRecord:
    path: Path
    root: Path
    filename: str
    extension: str
    size_bytes: int
    modified_time: float
    sha256: str
    category: Optional[str]
    status: str = "CATALOGED"

    @property
    def relative_path(self) -> str:
        return str(self.path.relative_to(self.root))
