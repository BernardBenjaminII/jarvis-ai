from __future__ import annotations

import asyncio
import functools
import importlib
import inspect
import json
import os
import sqlite3
import time
import traceback
from pathlib import Path
from typing import Any

EVENTS = Path(
    os.environ.get(
        "JARVIS_R4_R11_A5_R5_EVENTS",
        "/tmp/r4_r11_a5_r5_events.jsonl",
    )
)

EVENTS.parent.mkdir(
    parents=True,
    exist_ok=True,
)


def safe(value: Any, depth: int = 0) -> Any:
    if depth > 4:
        return "<depth-limit>"

    if value is None or isinstance(
        value,
        (
            bool,
            int,
            float,
            str,
        ),
    ):
        if isinstance(value, str) and len(value) > 700:
            return value[:700] + "...<truncated>"
        return value

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, dict):
        out = {}
        for i, (k, v) in enumerate(value.items()):
            if i >= 40:
                out["<truncated>"] = True
                break

            key = str(k)

            if any(
                token in key.casefold()
                for token in (
                    "text",
                    "content",
                    "excerpt",
                    "metadata",
                    "raw",
                    "body",
                )
            ):
                sv = safe(v, depth + 1)

                if isinstance(sv, str) and len(sv) > 300:
                    sv = sv[:300] + "...<truncated>"

                out[key] = sv

            else:
                out[key] = safe(v, depth + 1)

        return out

    if isinstance(value, (list, tuple, set)):
        seq = list(value)
        return [
            safe(x, depth + 1)
            for x in seq[:20]
        ] + (
            ["<truncated>"]
            if len(seq) > 20
            else []
        )

    if hasattr(value, "to_dict"):
        try:
            return safe(
                value.to_dict(),
                depth + 1,
            )
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        try:
            return safe(
                vars(value),
                depth + 1,
            )
        except Exception:
            pass

    text = repr(value)

    if len(text) > 700:
        text = text[:700] + "...<truncated>"

    return text


def emit(kind: str, **payload: Any) -> None:
    row = {
        "ts": time.time(),
        "kind": kind,
        **{
            k: safe(v)
            for k, v in payload.items()
        },
    }

    with EVENTS.open(
        "a",
        encoding="utf-8",
    ) as fh:
        fh.write(
            json.dumps(
                row,
                ensure_ascii=False,
            )
            + "\n"
        )


def wrap_function(
    module_name: str,
    name: str,
) -> bool:

    try:
        module = importlib.import_module(
            module_name
        )
    except Exception as exc:
        emit(
            "wrap_import_fail",
            module=module_name,
            name=name,
            error=repr(exc),
        )
        return False

    original = getattr(
        module,
        name,
        None,
    )

    if original is None:
        return False

    if getattr(
        original,
        "__r4_r11_a5_r5_wrapped__",
        False,
    ):
        return True

    if inspect.iscoroutinefunction(original):

        @functools.wraps(original)
        async def async_wrapper(*args, **kwargs):
            emit(
                "call_enter",
                module=module_name,
                function=name,
                args=args,
                kwargs=kwargs,
            )

            try:
                result = await original(
                    *args,
                    **kwargs
                )
            except Exception as exc:
                emit(
                    "call_error",
                    module=module_name,
                    function=name,
                    error=repr(exc),
                    traceback=traceback.format_exc(),
                )
                raise

            emit(
                "call_exit",
                module=module_name,
                function=name,
                result=result,
            )
            return result

        async_wrapper.__r4_r11_a5_r5_wrapped__ = True
        setattr(
            module,
            name,
            async_wrapper,
        )

    else:

        @functools.wraps(original)
        def wrapper(*args, **kwargs):
            emit(
                "call_enter",
                module=module_name,
                function=name,
                args=args,
                kwargs=kwargs,
            )

            try:
                result = original(
                    *args,
                    **kwargs
                )
            except Exception as exc:
                emit(
                    "call_error",
                    module=module_name,
                    function=name,
                    error=repr(exc),
                    traceback=traceback.format_exc(),
                )
                raise

            emit(
                "call_exit",
                module=module_name,
                function=name,
                result=result,
            )
            return result

        wrapper.__r4_r11_a5_r5_wrapped__ = True
        setattr(
            module,
            name,
            wrapper,
        )

    emit(
        "wrapped",
        module=module_name,
        function=name,
    )

    return True


TARGETS = [
    (
        "core.knowledge_catalog.materialization.search",
        "search_runtime_knowledge",
    ),
    (
        "core.knowledge_catalog.qualified_search",
        "search_qualified_catalog",
    ),
    (
        "core.retrieval.semantic_index.service",
        "semantic_search",
    ),
    (
        "core.retrieval.vector_search.service",
        "search",
    ),
    (
        "core.retrieval.hybrid.service",
        "search",
    ),
    (
        "core.retrieval.hybrid_rerank.service",
        "search",
    ),
    (
        "core.retrieval.evidence_context.service",
        "build",
    ),
    (
        "core.retrieval.evidence_context.service",
        "search",
    ),
    (
        "core.retrieval.evidence_grounding.service",
        "ground",
    ),
    (
        "core.conversation.grounded_answer.service",
        "answer",
    ),
    (
        "core.conversation.grounded_answer.service",
        "generate",
    ),
]

for module_name, name in TARGETS:
    try:
        wrap_function(
            module_name,
            name,
        )
    except Exception as exc:
        emit(
            "wrap_failure",
            module=module_name,
            function=name,
            error=repr(exc),
        )


#
# Also trace sqlite catalog reads.
#

_real_connect = sqlite3.connect


def traced_connect(database, *args, **kwargs):
    text = str(database)

    if (
        "catalog.sqlite" in text
        or "semantic_index.sqlite" in text
    ):
        emit(
            "sqlite_connect",
            database=text,
        )

    return _real_connect(
        database,
        *args,
        **kwargs,
    )


sqlite3.connect = traced_connect


#
# Import real application only after instrumentation.
#

emit(
    "launcher_ready",
    event_file=str(EVENTS),
)

from core.src.main import app

emit(
    "app_loaded",
    app_type=type(app).__name__,
)
