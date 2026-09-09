
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
    "r4_r11_a5_r9_r12_events.jsonl"
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
        if isinstance(value, str) and len(value) > 2000:
            return value[:2000] + "...<truncated>"
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
            in list(value.items())[:250]
        }

    if isinstance(value, (list, tuple, set)):
        return [
            safe(v, depth + 1)
            for v in list(value)[:250]
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
        "ts":
            time.time(),

        "kind":
            kind,

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


search_mod = importlib.import_module(
    "core.knowledge_catalog.materialization.search"
)

qualified = importlib.import_module(
    "core.knowledge_catalog.qualified_search"
)

evidence_context = importlib.import_module(
    "core.retrieval.evidence_context.service"
)

evidence_grounding = importlib.import_module(
    "core.retrieval.evidence_grounding.service"
)

grounding = importlib.import_module(
    "core.conversation.grounding"
)

integration = importlib.import_module(
    "core.conversation.grounded_answer.integration"
)


# ------------------------------------------------------------
# Runtime search
# ------------------------------------------------------------

_original_search = (
    search_mod.search_runtime_knowledge
)


@functools.wraps(
    _original_search
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

    result = _original_search(
        *args,
        **kwargs,
    )

    emit(
        "runtime_search_exit",
        result=result,
    )

    return result


search_mod.search_runtime_knowledge = (
    search_runtime_knowledge_trace
)

if hasattr(
    qualified,
    "search_runtime_knowledge",
):
    qualified.search_runtime_knowledge = (
        search_runtime_knowledge_trace
    )


# ------------------------------------------------------------
# candidate_from_row
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
# search_qualified_catalog
# ------------------------------------------------------------

_original_qualified_search = (
    qualified.search_qualified_catalog
)


@functools.wraps(
    _original_qualified_search
)
def search_qualified_catalog_trace(
    *args,
    **kwargs,
):

    emit(
        "qualified_search_enter",
        args=args,
        kwargs=kwargs,
    )

    result = _original_qualified_search(
        *args,
        **kwargs,
    )

    emit(
        "qualified_search_exit",
        result=result,
    )

    return result


qualified.search_qualified_catalog = (
    search_qualified_catalog_trace
)


# ------------------------------------------------------------
# EvidenceContext public classes/methods
# ------------------------------------------------------------

for class_name, cls in list(
    vars(evidence_context).items()
):
    if not isinstance(cls, type):
        continue

    if cls.__module__ != (
        evidence_context.__name__
    ):
        continue

    for method_name in (
        "build",
        "assemble",
        "create",
        "search",
        "retrieve",
        "context",
    ):
        method = getattr(
            cls,
            method_name,
            None,
        )

        if not callable(method):
            continue

        original = method

        def make_wrapper(
            original,
            class_name,
            method_name,
        ):
            @functools.wraps(
                original
            )
            def wrapper(
                self,
                *args,
                **kwargs,
            ):
                emit(
                    "evidence_context_enter",
                    class_name=class_name,
                    method_name=method_name,
                    args=args,
                    kwargs=kwargs,
                )

                result = original(
                    self,
                    *args,
                    **kwargs,
                )

                emit(
                    "evidence_context_exit",
                    class_name=class_name,
                    method_name=method_name,
                    result=result,
                )

                return result

            return wrapper

        setattr(
            cls,
            method_name,
            make_wrapper(
                original,
                class_name,
                method_name,
            ),
        )


# ------------------------------------------------------------
# Evidence grounding public service methods
# ------------------------------------------------------------

for class_name, cls in list(
    vars(evidence_grounding).items()
):
    if not isinstance(cls, type):
        continue

    if cls.__module__ != (
        evidence_grounding.__name__
    ):
        continue

    for method_name in (
        "ground",
        "build",
        "assemble",
        "synthesize",
        "create",
    ):
        method = getattr(
            cls,
            method_name,
            None,
        )

        if not callable(method):
            continue

        original = method

        def make_wrapper(
            original,
            class_name,
            method_name,
        ):
            @functools.wraps(
                original
            )
            def wrapper(
                self,
                *args,
                **kwargs,
            ):
                emit(
                    "evidence_grounding_enter",
                    class_name=class_name,
                    method_name=method_name,
                    args=args,
                    kwargs=kwargs,
                )

                result = original(
                    self,
                    *args,
                    **kwargs,
                )

                emit(
                    "evidence_grounding_exit",
                    class_name=class_name,
                    method_name=method_name,
                    result=result,
                )

                return result

            return wrapper

        setattr(
            cls,
            method_name,
            make_wrapper(
                original,
                class_name,
                method_name,
            ),
        )


# ------------------------------------------------------------
# CatalogGroundingService
# ------------------------------------------------------------

CatalogGroundingService = getattr(
    grounding,
    "CatalogGroundingService",
    None,
)

if CatalogGroundingService is not None:
    method = getattr(
        CatalogGroundingService,
        "ground",
        None,
    )

    if callable(method):
        original = method

        @functools.wraps(
            original
        )
        def catalog_ground_trace(
            self,
            *args,
            **kwargs,
        ):
            emit(
                "catalog_grounding_enter",
                args=args,
                kwargs=kwargs,
            )

            result = original(
                self,
                *args,
                **kwargs,
            )

            emit(
                "catalog_grounding_exit",
                result=result,
            )

            return result

        CatalogGroundingService.ground = (
            catalog_ground_trace
        )


# ------------------------------------------------------------
# Grounded-answer runtime request
# ------------------------------------------------------------

_original_build_runtime_request = (
    integration.build_runtime_request
)


@functools.wraps(
    _original_build_runtime_request
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

    result = (
        _original_build_runtime_request(
            context,
            qualification,
            *args,
            **kwargs,
        )
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
