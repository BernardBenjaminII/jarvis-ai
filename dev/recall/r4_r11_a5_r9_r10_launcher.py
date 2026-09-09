
from __future__ import annotations

import dataclasses
import functools
import importlib
import json
import pathlib
import sys
import time
from typing import Any


PROJECT = pathlib.Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

EVENTS = (
    PROJECT
    / "artifacts/genesis_recall/"
    "r4_r11_a5_r9_r10_events.jsonl"
)

if str(PROJECT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT),
    )


def safe(value: Any, depth: int = 0):
    if depth > 6:
        return repr(value)

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        if isinstance(value, str) and len(value) > 1600:
            return value[:1600] + "...<truncated>"
        return value

    if isinstance(value, pathlib.Path):
        return str(value)

    if dataclasses.is_dataclass(value):
        try:
            return {
                field.name:
                    safe(
                        getattr(value, field.name),
                        depth + 1,
                    )
                for field
                in dataclasses.fields(value)
            }
        except Exception:
            pass

    if isinstance(value, dict):
        return {
            str(k):
                safe(v, depth + 1)
            for k, v
            in list(value.items())[:200]
        }

    if isinstance(value, (list, tuple, set)):
        return [
            safe(v, depth + 1)
            for v in list(value)[:200]
        ]

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
            return {
                str(k):
                    safe(v, depth + 1)
                for k, v
                in vars(value).items()
                if not str(k).startswith("_")
            }
        except Exception:
            pass

    return repr(value)


def emit(kind: str, **payload):
    row = {
        "ts": time.time(),
        "kind": kind,
        **{
            key:
                safe(value)
            for key, value
            in payload.items()
        },
    }

    with EVENTS.open(
        "a",
        encoding="utf-8",
    ) as fp:
        fp.write(
            json.dumps(
                row,
                ensure_ascii=False,
            )
            + "\n"
        )


qualified = importlib.import_module(
    "core.knowledge_catalog.qualified_search"
)

runtime_search = importlib.import_module(
    "core.knowledge_catalog.materialization.search"
)

integration = importlib.import_module(
    "core.conversation.grounded_answer.integration"
)


# ------------------------------------------------------------
# Wrap search_runtime_knowledge()
# ------------------------------------------------------------

_original_runtime_search = (
    runtime_search.search_runtime_knowledge
)


@functools.wraps(
    _original_runtime_search
)
def search_runtime_knowledge_trace(
    *args,
    **kwargs,
):

    emit(
        "runtime_search_enter",
        args=args,
        kwargs=kwargs,
    )

    result = _original_runtime_search(
        *args,
        **kwargs,
    )

    emit(
        "runtime_search_exit",
        result=result,
    )

    return result


runtime_search.search_runtime_knowledge = (
    search_runtime_knowledge_trace
)


# Ensure qualified_search sees wrapped producer if it imported
# the callable directly into its module namespace.
if hasattr(
    qualified,
    "search_runtime_knowledge",
):
    qualified.search_runtime_knowledge = (
        search_runtime_knowledge_trace
    )


# ------------------------------------------------------------
# Wrap candidate_from_row()
# ------------------------------------------------------------

_original_candidate = (
    qualified.candidate_from_row
)


@functools.wraps(
    _original_candidate
)
def candidate_from_row_trace(
    row,
    *args,
    **kwargs,
):

    emit(
        "candidate_from_row_enter",
        row=row,
    )

    result = _original_candidate(
        row,
        *args,
        **kwargs,
    )

    emit(
        "candidate_from_row_exit",
        candidate=result,
    )

    return result


qualified.candidate_from_row = (
    candidate_from_row_trace
)


# ------------------------------------------------------------
# Wrap qualified_row()
# ------------------------------------------------------------

_original_qualified_row = getattr(
    qualified,
    "qualified_row",
    None,
)

if callable(
    _original_qualified_row
):

    @functools.wraps(
        _original_qualified_row
    )
    def qualified_row_trace(
        *args,
        **kwargs,
    ):

        emit(
            "qualified_row_enter",
            args=args,
            kwargs=kwargs,
        )

        result = _original_qualified_row(
            *args,
            **kwargs,
        )

        emit(
            "qualified_row_exit",
            result=result,
        )

        return result


    qualified.qualified_row = (
        qualified_row_trace
    )


# ------------------------------------------------------------
# Wrap qualify_rows()
# ------------------------------------------------------------

_original_qualify_rows = getattr(
    qualified,
    "qualify_rows",
    None,
)

if callable(
    _original_qualify_rows
):

    @functools.wraps(
        _original_qualify_rows
    )
    def qualify_rows_trace(
        *args,
        **kwargs,
    ):

        emit(
            "qualify_rows_enter",
            args=args,
            kwargs=kwargs,
        )

        result = _original_qualify_rows(
            *args,
            **kwargs,
        )

        emit(
            "qualify_rows_exit",
            result=result,
        )

        return result


    qualified.qualify_rows = (
        qualify_rows_trace
    )


# ------------------------------------------------------------
# Wrap search_qualified_catalog()
# ------------------------------------------------------------

_original_search_qualified = (
    qualified.search_qualified_catalog
)


@functools.wraps(
    _original_search_qualified
)
def search_qualified_catalog_trace(
    *args,
    **kwargs,
):

    emit(
        "search_qualified_enter",
        args=args,
        kwargs=kwargs,
    )

    result = _original_search_qualified(
        *args,
        **kwargs,
    )

    emit(
        "search_qualified_exit",
        result=result,
    )

    return result


qualified.search_qualified_catalog = (
    search_qualified_catalog_trace
)


# ------------------------------------------------------------
# Capture qualification entering grounded-answer runtime.
# ------------------------------------------------------------

_original_build = (
    integration.build_runtime_request
)


@functools.wraps(
    _original_build
)
def build_runtime_request_trace(
    context,
    qualification,
    *args,
    **kwargs,
):

    emit(
        "runtime_request_enter",
        operator_input=str(
            getattr(
                context,
                "operator_input",
                "",
            )
            or ""
        ),
        qualification=qualification,
    )

    result = _original_build(
        context,
        qualification,
        *args,
        **kwargs,
    )

    emit(
        "runtime_request_exit",
        result=result,
    )

    return result


integration.build_runtime_request = (
    build_runtime_request_trace
)


main = importlib.import_module(
    "core.src.main"
)

app = main.app

emit(
    "launcher_ready",
    app_type=
        f"{type(app).__module__}."
        f"{type(app).__name__}",
)
