from __future__ import annotations

import numpy as np


def decode_vector(blob: bytes, dimensions: int) -> np.ndarray:
    v = np.frombuffer(blob, dtype=np.float32)
    if v.size != int(dimensions):
        raise ValueError(f"vector dimension mismatch: expected={dimensions} actual={v.size}")
    return v


def normalized(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float32)
    norm = float(np.linalg.norm(v))
    if not np.isfinite(norm) or norm <= 0.0:
        raise ValueError("zero or non-finite vector norm")
    return v / norm


def cosine_scores(matrix: np.ndarray, query: np.ndarray) -> np.ndarray:
    if matrix.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    q = normalized(query)
    norms = np.linalg.norm(matrix, axis=1)
    valid = norms > 0.0
    scores = np.full(matrix.shape[0], -1.0, dtype=np.float32)
    if valid.any():
        scores[valid] = (matrix[valid] @ q) / norms[valid]
    return scores
