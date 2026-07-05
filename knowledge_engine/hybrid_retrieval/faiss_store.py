from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np


class FaissIndexStore:
    def __init__(self, index_dir: str | Path):
        self.index_dir = Path(index_dir)
        self.index_path = self.index_dir / "chunks.faiss"
        self.map_path = self.index_dir / "chunks_map.json"

    def ensure_dir(self) -> None:
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def save(self, index, chunk_uuids: list[str]) -> None:
        self.ensure_dir()
        faiss.write_index(index, str(self.index_path))
        self.map_path.write_text(
            json.dumps(chunk_uuids, indent=2),
            encoding="utf-8",
        )

    def load(self):
        if not self.index_path.exists() or not self.map_path.exists():
            raise FileNotFoundError(
                f"Missing FAISS index or map in {self.index_dir}"
            )

        index = faiss.read_index(str(self.index_path))
        chunk_uuids = json.loads(self.map_path.read_text(encoding="utf-8"))

        return index, chunk_uuids

    def exists(self) -> bool:
        return self.index_path.exists() and self.map_path.exists()


def build_hnsw_index(vectors: np.ndarray, m: int = 32):
    if vectors.dtype != np.float32:
        vectors = vectors.astype("float32")

    dim = vectors.shape[1]

    index = faiss.IndexHNSWFlat(dim, m, faiss.METRIC_INNER_PRODUCT)
    index.hnsw.efConstruction = 80
    index.hnsw.efSearch = 64
    index.add(vectors)

    return index
