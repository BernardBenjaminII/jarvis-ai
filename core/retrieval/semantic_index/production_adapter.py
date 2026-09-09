"""
Genesis Recall R4-R11-A5-R7

Production adapter for the certified SemanticIndexService.

This module deliberately contains no persistence behavior.

Its responsibility is only:

    query
      -> SemanticIndexService.semantic_search()
      -> normalized production candidate dictionaries

No corpus mutation.
No semantic-index mutation.
No threshold manipulation.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .service import SemanticIndexService


DEFAULT_RUNTIME_CATALOG = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

DEFAULT_SEMANTIC_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/semantic_index.sqlite"
)


def _object_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)

    if is_dataclass(value):
        return asdict(value)

    if hasattr(value, "_asdict"):
        try:
            return dict(value._asdict())
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        return {
            k: v
            for k, v in vars(value).items()
            if not k.startswith("_")
        }

    return {"value": value}


def _first(
    data: Dict[str, Any],
    *names: str,
    default: Any = None,
) -> Any:
    for name in names:
        if name in data and data[name] is not None:
            return data[name]

    return default


def normalize_semantic_hit(
    hit: Any,
    *,
    rank: int,
) -> Dict[str, Any]:
    """
    Normalize semantic-index results without discarding their
    original fields.

    The adapter intentionally supplies several compatibility
    aliases because downstream retrieval generations have used
    different field names.
    """

    raw = _object_dict(hit)

    runtime_chunk_id = _first(
        raw,
        "runtime_chunk_id",
        "chunk_id",
        "id",
    )

    runtime_document_id = _first(
        raw,
        "runtime_document_id",
        "document_id",
        "doc_id",
    )

    score = _first(
        raw,
        "score",
        "similarity",
        "semantic_score",
        default=0.0,
    )

    text = _first(
        raw,
        "fragment_text",
        "chunk_text",
        "text",
        "content",
        "body",
        default="",
    )

    title = _first(
        raw,
        "title",
        "document_title",
        "source_title",
        default="",
    )

    path = _first(
        raw,
        "path",
        "source_path",
        "document_path",
        default="",
    )

    candidate = dict(raw)

    candidate.update({
        "runtime_chunk_id": runtime_chunk_id,
        "chunk_id": runtime_chunk_id,

        "runtime_document_id": runtime_document_id,
        "document_id": runtime_document_id,
        "doc_id": runtime_document_id,

        "score": score,
        "semantic_score": score,

        "text": text,
        "content": text,
        "chunk_text": text,

        "title": title,
        "path": path,

        "rank": rank,

        "retrieval_mode": "semantic_index",
        "retrieval_source": "SemanticIndexService",
    })

    return candidate


class ProductionSemanticAdapter:
    """
    Read-only production facade around SemanticIndexService.
    """

    def __init__(
        self,
        *,
        runtime_catalog: Path = DEFAULT_RUNTIME_CATALOG,
        semantic_db: Path = DEFAULT_SEMANTIC_DB,
        provider: str = "ollama",
        model: str = "mxbai-embed-large",
    ) -> None:

        kwargs = {
            "runtime_catalog": runtime_catalog,
            "semantic_db": semantic_db,
        }

        # SemanticIndexService constructor generations differ.
        # Add provider/model only when accepted.
        import inspect

        sig = inspect.signature(SemanticIndexService)

        if "provider" in sig.parameters:
            kwargs["provider"] = provider

        if "provider_name" in sig.parameters:
            kwargs["provider_name"] = provider

        if "model" in sig.parameters:
            kwargs["model"] = model

        self.service = SemanticIndexService(**kwargs)

    def search(
        self,
        query: str,
        *,
        limit: int = 20,
        scan_limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:

        hits = self.service.semantic_search(
            query,
            limit=limit,
            scan_limit=scan_limit,
        )

        return [
            normalize_semantic_hit(hit, rank=i)
            for i, hit in enumerate(hits, 1)
        ]


def production_semantic_search(
    query: str,
    *,
    limit: int = 20,
    scan_limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience entry point for production retrieval callers.
    """

    return ProductionSemanticAdapter().search(
        query,
        limit=limit,
        scan_limit=scan_limit,
    )
