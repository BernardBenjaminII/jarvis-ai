from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import numpy as np


FORMAT_VERSION = 1
DEFAULT_BLOCK_SIZE = 4096


@dataclass(frozen=True)
class SidecarPopulation:
    name: str
    count: int
    dimensions: int
    vectors_file: str
    metadata_file: str
    fingerprint: str


class ExactVectorSidecarBuilder:
    """
    R6.1 exact-vector sidecar builder.

    SQLite remains authoritative.

    Sidecar vectors are normalized float32 rows so exact cosine retrieval
    becomes a matrix/vector dot product against the normalized query.

    Construction is performed in a temporary directory and published only
    after all rows have been written and validated.
    """

    def __init__(
        self,
        *,
        semantic_db: Path,
        output_dir: Path,
        provider: str,
        model: str,
        expected_dimensions: int,
        block_size: int = DEFAULT_BLOCK_SIZE,
    ):
        self.semantic_db = Path(semantic_db)
        self.output_dir = Path(output_dir)
        self.provider = str(provider)
        self.model = str(model)
        self.expected_dimensions = int(expected_dimensions)
        self.block_size = max(64, int(block_size))

    def _connect(self):
        c = sqlite3.connect(
            f"file:{self.semantic_db.resolve()}?mode=ro",
            uri=True,
            timeout=30.0,
        )
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA query_only=ON")
        c.execute("PRAGMA busy_timeout=30000")
        return c

    @staticmethod
    def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
        matrix = np.asarray(matrix, dtype=np.float32)

        norms = np.linalg.norm(matrix, axis=1)

        if not np.all(np.isfinite(norms)):
            raise RuntimeError("non-finite vector norm encountered")

        if np.any(norms <= 0.0):
            raise RuntimeError("zero vector norm encountered")

        return matrix / norms[:, None]

    def _population_spec(self, name: str):
        if name == "canonical":
            return {
                "count_sql": """
                    SELECT COUNT(*)
                    FROM semantic_vectors
                    WHERE provider=? AND model=? AND dimensions=?
                """,
                "scan_sql": """
                    SELECT
                        runtime_chunk_id,
                        chunk_uuid,
                        NULL AS fragment_uuid,
                        NULL AS fragment_index,
                        vector_blob,
                        vector_sha256
                    FROM semantic_vectors
                    WHERE provider=? AND model=? AND dimensions=?
                    ORDER BY runtime_chunk_id
                """,
            }

        if name == "fragment":
            return {
                "count_sql": """
                    SELECT COUNT(*)
                    FROM semantic_fragment_vectors AS v
                    JOIN semantic_fragments AS f
                      ON f.fragment_uuid=v.fragment_uuid
                    WHERE
                        v.provider=?
                        AND v.model=?
                        AND v.dimensions=?
                        AND f.is_leaf=1
                        AND f.stage='COMPLETE'
                """,
                "scan_sql": """
                    SELECT
                        v.runtime_chunk_id,
                        b.chunk_uuid,
                        v.fragment_uuid,
                        v.fragment_index,
                        v.vector_blob,
                        v.vector_sha256
                    FROM semantic_fragment_vectors AS v
                    JOIN semantic_fragments AS f
                      ON f.fragment_uuid=v.fragment_uuid
                    JOIN chunk_identity_bridge AS b
                      ON b.runtime_chunk_id=v.runtime_chunk_id
                    WHERE
                        v.provider=?
                        AND v.model=?
                        AND v.dimensions=?
                        AND f.is_leaf=1
                        AND f.stage='COMPLETE'
                    ORDER BY
                        v.runtime_chunk_id,
                        v.fragment_index,
                        v.fragment_uuid
                """,
            }

        raise ValueError(f"unknown population: {name}")

    def _build_population(
        self,
        *,
        connection: sqlite3.Connection,
        temp_dir: Path,
        name: str,
    ) -> SidecarPopulation:
        spec = self._population_spec(name)
        params = (
            self.provider,
            self.model,
            self.expected_dimensions,
        )

        count = int(
            connection.execute(
                spec["count_sql"],
                params,
            ).fetchone()[0]
        )

        if count <= 0:
            raise RuntimeError(f"{name}: no eligible vectors")

        vectors_name = f"{name}.vectors.f32"
        metadata_name = f"{name}.metadata.jsonl"

        vectors_path = temp_dir / vectors_name
        metadata_path = temp_dir / metadata_name

        vectors = np.memmap(
            vectors_path,
            dtype=np.float32,
            mode="w+",
            shape=(count, self.expected_dimensions),
        )

        fingerprint = hashlib.sha256()
        written = 0

        cur = connection.execute(spec["scan_sql"], params)

        with metadata_path.open("w", encoding="utf-8") as metadata:
            while True:
                rows = cur.fetchmany(self.block_size)
                if not rows:
                    break

                raw = np.vstack(
                    [
                        np.frombuffer(
                            r["vector_blob"],
                            dtype=np.float32,
                        )
                        for r in rows
                    ]
                )

                if raw.shape != (
                    len(rows),
                    self.expected_dimensions,
                ):
                    raise RuntimeError(
                        f"{name}: vector matrix shape mismatch: "
                        f"{raw.shape}"
                    )

                normalized = self._normalize_rows(raw)

                end = written + len(rows)
                vectors[written:end] = normalized

                for row in rows:
                    record = {
                        "runtime_chunk_id": int(row["runtime_chunk_id"]),
                        "chunk_uuid": str(row["chunk_uuid"]),
                        "fragment_uuid": (
                            str(row["fragment_uuid"])
                            if row["fragment_uuid"] is not None
                            else None
                        ),
                        "fragment_index": (
                            int(row["fragment_index"])
                            if row["fragment_index"] is not None
                            else None
                        ),
                    }

                    metadata.write(
                        json.dumps(
                            record,
                            separators=(",", ":"),
                            sort_keys=True,
                        )
                        + "\n"
                    )

                    identity = (
                        f"{record['runtime_chunk_id']}\0"
                        f"{record['chunk_uuid']}\0"
                        f"{record['fragment_uuid'] or ''}\0"
                        f"{record['fragment_index'] if record['fragment_index'] is not None else ''}\0"
                        f"{row['vector_sha256']}\n"
                    )

                    fingerprint.update(identity.encode("utf-8"))

                written = end

        vectors.flush()
        del vectors

        if written != count:
            raise RuntimeError(
                f"{name}: row count changed during build: "
                f"expected={count} written={written}"
            )

        expected_bytes = (
            count
            * self.expected_dimensions
            * np.dtype(np.float32).itemsize
        )

        actual_bytes = vectors_path.stat().st_size

        if actual_bytes != expected_bytes:
            raise RuntimeError(
                f"{name}: vector file size mismatch: "
                f"expected={expected_bytes} actual={actual_bytes}"
            )

        return SidecarPopulation(
            name=name,
            count=count,
            dimensions=self.expected_dimensions,
            vectors_file=vectors_name,
            metadata_file=metadata_name,
            fingerprint=fingerprint.hexdigest(),
        )

    def build(self) -> dict:
        started = perf_counter()

        parent = self.output_dir.parent
        parent.mkdir(parents=True, exist_ok=True)

        temp_dir = Path(
            tempfile.mkdtemp(
                prefix=f".{self.output_dir.name}.build-",
                dir=parent,
            )
        )

        try:
            with self._connect() as c:
                canonical = self._build_population(
                    connection=c,
                    temp_dir=temp_dir,
                    name="canonical",
                )

                fragment = self._build_population(
                    connection=c,
                    temp_dir=temp_dir,
                    name="fragment",
                )

            manifest = {
                "format": "jarvis-exact-vector-sidecar",
                "format_version": FORMAT_VERSION,
                "semantic_db": str(self.semantic_db.resolve()),
                "provider": self.provider,
                "model": self.model,
                "dimensions": self.expected_dimensions,
                "normalization": "l2-float32",
                "populations": {
                    "canonical": canonical.__dict__,
                    "fragment": fragment.__dict__,
                },
            }

            manifest_bytes = json.dumps(
                manifest,
                indent=2,
                sort_keys=True,
            ).encode("utf-8")

            (temp_dir / "manifest.json").write_bytes(manifest_bytes)

            # Make sure directory contents reach the filesystem before publish.
            dir_fd = os.open(temp_dir, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)

            old_dir = None

            if self.output_dir.exists():
                old_dir = self.output_dir.with_name(
                    self.output_dir.name + ".previous"
                )

                if old_dir.exists():
                    shutil.rmtree(old_dir)

                os.replace(self.output_dir, old_dir)

            os.replace(temp_dir, self.output_dir)

            if old_dir is not None and old_dir.exists():
                shutil.rmtree(old_dir)

            elapsed_ms = round(
                (perf_counter() - started) * 1000.0,
                2,
            )

            return {
                "status": "BUILT",
                "output_dir": str(self.output_dir),
                "elapsed_ms": elapsed_ms,
                "canonical_rows": canonical.count,
                "fragment_rows": fragment.count,
                "canonical_fingerprint": canonical.fingerprint,
                "fragment_fingerprint": fragment.fingerprint,
            }

        except Exception:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise


class ExactVectorSidecar:
    """
    Read-only R6.1 sidecar.

    This class does not alter production retrieval.  It is initially used
    for shadow/parity certification against the existing SQLite scanner.
    """

    def __init__(self, root: Path):
        self.root = Path(root)

        manifest_path = self.root / "manifest.json"
        if not manifest_path.is_file():
            raise RuntimeError(
                f"sidecar manifest not found: {manifest_path}"
            )

        self.manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )

        if self.manifest.get("format") != "jarvis-exact-vector-sidecar":
            raise RuntimeError("unrecognized sidecar format")

        if int(self.manifest.get("format_version", -1)) != FORMAT_VERSION:
            raise RuntimeError("unsupported sidecar format version")

        self.dimensions = int(self.manifest["dimensions"])

        self._vectors = {}
        self._metadata = {}

        for name in ("canonical", "fragment"):
            spec = self.manifest["populations"][name]

            count = int(spec["count"])
            dimensions = int(spec["dimensions"])

            if dimensions != self.dimensions:
                raise RuntimeError(
                    f"{name}: inconsistent dimensions"
                )

            vector_path = self.root / spec["vectors_file"]
            metadata_path = self.root / spec["metadata_file"]

            expected_bytes = (
                count
                * dimensions
                * np.dtype(np.float32).itemsize
            )

            if vector_path.stat().st_size != expected_bytes:
                raise RuntimeError(
                    f"{name}: invalid vector sidecar size"
                )

            self._vectors[name] = np.memmap(
                vector_path,
                dtype=np.float32,
                mode="r",
                shape=(count, dimensions),
            )

            with metadata_path.open("r", encoding="utf-8") as fh:
                metadata = [
                    json.loads(line)
                    for line in fh
                    if line.strip()
                ]

            if len(metadata) != count:
                raise RuntimeError(
                    f"{name}: metadata count mismatch: "
                    f"expected={count} actual={len(metadata)}"
                )

            self._metadata[name] = metadata

    def count(self, population: str) -> int:
        return int(self._vectors[population].shape[0])

    def search(
        self,
        *,
        population: str,
        query: np.ndarray,
        top_k: int,
        block_rows: int = 131072,
    ) -> tuple[list[tuple[float, dict]], int]:
        matrix = self._vectors[population]

        q = np.asarray(query, dtype=np.float32)
        norm = float(np.linalg.norm(q))

        if not np.isfinite(norm) or norm <= 0.0:
            raise ValueError("zero or non-finite query norm")

        q = q / norm

        count = int(matrix.shape[0])
        k = min(max(1, int(top_k)), count)
        block_rows = max(1024, int(block_rows))

        best_scores = np.empty(0, dtype=np.float32)
        best_indices = np.empty(0, dtype=np.int64)

        for start in range(0, count, block_rows):
            end = min(start + block_rows, count)

            scores = np.asarray(
                matrix[start:end] @ q,
                dtype=np.float32,
            )

            local_k = min(k, scores.size)

            if local_k == scores.size:
                local_idx = np.arange(scores.size, dtype=np.int64)
            else:
                local_idx = np.argpartition(
                    scores,
                    scores.size - local_k,
                )[-local_k:]

            local_scores = scores[local_idx]
            local_indices = local_idx.astype(np.int64) + start

            if best_scores.size == 0:
                merged_scores = local_scores
                merged_indices = local_indices
            else:
                merged_scores = np.concatenate(
                    (best_scores, local_scores)
                )
                merged_indices = np.concatenate(
                    (best_indices, local_indices)
                )

            keep = min(k, merged_scores.size)

            if keep < merged_scores.size:
                selected = np.argpartition(
                    merged_scores,
                    merged_scores.size - keep,
                )[-keep:]

                best_scores = merged_scores[selected]
                best_indices = merged_indices[selected]
            else:
                best_scores = merged_scores
                best_indices = merged_indices

        order = np.argsort(-best_scores, kind="stable")

        results = []

        for pos in order[:k]:
            index = int(best_indices[pos])
            results.append(
                (
                    float(best_scores[pos]),
                    self._metadata[population][index],
                )
            )

        return results, count
