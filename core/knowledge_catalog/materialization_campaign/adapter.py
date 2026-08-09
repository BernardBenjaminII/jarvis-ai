from __future__ import annotations

import inspect
import sqlite3
from pathlib import Path
from typing import Any

from .contracts import Candidate


class MaterializerAdapter:
    def __init__(
        self,
        *,
        runtime_catalog: Path,
    ) -> None:
        self.runtime_catalog = runtime_catalog
        self.service = self._build_service()

    def _build_service(self):
        from core.knowledge_catalog.materialization.engine import (
            RuntimeKnowledgeMaterializer,
        )

        signature = inspect.signature(RuntimeKnowledgeMaterializer)
        kwargs: dict[str, Any] = {}

        for name in signature.parameters:
            if name in {"database_path", "db_path", "catalog_path"}:
                kwargs[name] = self.runtime_catalog

        try:
            return RuntimeKnowledgeMaterializer(**kwargs)
        except TypeError:
            return RuntimeKnowledgeMaterializer(self.runtime_catalog)

    def table_counts(self) -> dict[str, int]:
        connection = sqlite3.connect(
            f"file:{self.runtime_catalog.resolve()}?mode=ro",
            uri=True,
        )
        try:
            result = {}
            for table in (
                "runtime_documents",
                "runtime_chunks",
                "runtime_chunks_fts",
            ):
                exists = connection.execute(
                    """
                    SELECT 1
                    FROM sqlite_master
                    WHERE type='table' AND name=?
                    """,
                    (table,),
                ).fetchone()
                result[table] = (
                    0
                    if exists is None
                    else int(
                        connection.execute(
                            f'SELECT COUNT(*) FROM "{table}"'
                        ).fetchone()[0]
                    )
                )
            return result
        finally:
            connection.close()

    def materialize(self, candidate: Candidate) -> Any:
        methods = (
            "materialize_path",
            "materialize_file",
            "materialize_candidate",
            "materialize",
        )

        last_error = None

        for method_name in methods:
            method = getattr(self.service, method_name, None)
            if not callable(method):
                continue

            signature = inspect.signature(method)
            parameters = list(signature.parameters.values())
            attempts = []

            if not parameters:
                attempts.append(((), {}))
            else:
                kwargs = {}
                args = []

                for parameter in parameters:
                    name = parameter.name

                    if name in {"path", "file_path", "source_path"}:
                        kwargs[name] = Path(candidate.path)
                    elif name in {"candidate"}:
                        kwargs[name] = candidate
                    elif name in {"title"}:
                        kwargs[name] = candidate.title
                    elif name in {"category", "subject", "domain"}:
                        kwargs[name] = candidate.category
                    elif name in {"sha256"}:
                        kwargs[name] = candidate.sha256
                    elif parameter.default is inspect._empty:
                        args.append(Path(candidate.path))

                attempts.append((tuple(args), kwargs))
                attempts.append(((Path(candidate.path),), {}))
                attempts.append(((candidate.path,), {}))

            for args, kwargs in attempts:
                try:
                    return method(*args, **kwargs)
                except TypeError as exc:
                    last_error = exc
                    continue

        if last_error is not None:
            raise RuntimeError(
                "No compatible materializer method signature was found"
            ) from last_error

        raise RuntimeError(
            "RuntimeKnowledgeMaterializer exposes no supported materialization method"
        )
