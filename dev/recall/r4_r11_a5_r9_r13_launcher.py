
from __future__ import annotations

import dataclasses
import functools
import importlib
import json
import pathlib
import sys
import time


PROJECT = pathlib.Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

EVENTS = (
    PROJECT
    / "artifacts/genesis_recall/"
    "r4_r11_a5_r9_r13_events.jsonl"
)

TARGET_FUNCTIONS = ['_gate_repair_should_rescue', '_r2_exact_document_identity_should_rescue', 'search_qualified_catalog']

if str(PROJECT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT),
    )


def safe(value, depth=0):
    if depth > 6:
        return repr(value)

    if value is None or isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        if isinstance(value, str) and len(value) > 1800:
            return value[:1800] + "...<truncated>"
        return value

    if isinstance(value, pathlib.Path):
        return str(value)

    if dataclasses.is_dataclass(value):
        try:
            return {
                field.name:
                    safe(
                        getattr(
                            value,
                            field.name,
                        ),
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


def emit(kind, **payload):
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


qualified = importlib.import_module(
    "core.knowledge_catalog.qualified_search"
)

integration = importlib.import_module(
    "core.conversation.grounded_answer.integration"
)


# ------------------------------------------------------------
# Directly wrap located predicate functions.
# ------------------------------------------------------------

for function_name in TARGET_FUNCTIONS:

    original = getattr(
        qualified,
        function_name,
        None,
    )

    if not callable(original):
        emit(
            "predicate_missing",
            function=function_name,
        )
        continue

    def make_wrapper(
        original,
        function_name,
    ):

        @functools.wraps(original)
        def wrapper(*args, **kwargs):

            emit(
                "predicate_enter",
                function=function_name,
                args=args,
                kwargs=kwargs,
            )

            result = original(
                *args,
                **kwargs,
            )

            emit(
                "predicate_exit",
                function=function_name,
                result=result,
            )

            return result

        return wrapper

    setattr(
        qualified,
        function_name,
        make_wrapper(
            original,
            function_name,
        ),
    )

    emit(
        "predicate_wrapped",
        function=function_name,
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

    result = _original_candidate(
        row,
        *args,
        **kwargs,
    )

    emit(
        "candidate",
        row=row,
        candidate=result,
    )

    return result


qualified.candidate_from_row = (
    candidate_from_row_trace
)


# ------------------------------------------------------------
# search_qualified_catalog
# ------------------------------------------------------------

_original_search = (
    qualified.search_qualified_catalog
)


@functools.wraps(
    _original_search
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

    result = _original_search(
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
# qualification entering grounded-answer runtime
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
        "runtime_request",
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

    return _original_build(
        context,
        qualification,
        *args,
        **kwargs,
    )


integration.build_runtime_request = (
    build_runtime_request_trace
)


main = importlib.import_module(
    "core.src.main"
)

app = main.app
