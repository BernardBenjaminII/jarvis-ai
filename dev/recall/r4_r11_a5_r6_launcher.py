from __future__ import annotations

import functools
import importlib
import inspect
import json
import os
import pathlib
import time
import traceback

EVENTS = pathlib.Path(
    os.environ[
        "JARVIS_R4_R11_A5_R6_EVENTS"
    ]
)


def safe(value, depth=0):

    if depth > 5:
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

        if (
            isinstance(value, str)
            and len(value) > 1000
        ):
            return (
                value[:1000]
                +
                "...<truncated>"
            )

        return value

    if isinstance(value, dict):

        return {
            str(k): safe(
                v,
                depth + 1,
            )
            for k, v
            in list(
                value.items()
            )[:50]
        }

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):

        seq = list(value)

        return [
            safe(
                x,
                depth + 1,
            )
            for x in seq[:25]
        ]

    if hasattr(
        value,
        "to_dict",
    ):
        try:
            return safe(
                value.to_dict(),
                depth + 1,
            )
        except Exception:
            pass

    if hasattr(
        value,
        "__dict__",
    ):
        try:
            return safe(
                vars(value),
                depth + 1,
            )
        except Exception:
            pass

    return repr(value)


def emit(kind, **payload):

    EVENTS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    row = {
        "ts":
            time.time(),

        "kind":
            kind,

        **{
            k: safe(v)
            for k, v
            in payload.items()
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
            +
            "\n"
        )


def wrap(module_name, function_name):

    try:
        module = importlib.import_module(
            module_name
        )
    except Exception as exc:

        emit(
            "wrap_import_fail",
            module=module_name,
            function=function_name,
            error=repr(exc),
        )

        return

    original = getattr(
        module,
        function_name,
        None,
    )

    if original is None:
        return

    if inspect.iscoroutinefunction(
        original
    ):

        @functools.wraps(original)
        async def aw(*args, **kwargs):

            emit(
                "enter",
                module=module_name,
                function=function_name,
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
                    "error",
                    module=module_name,
                    function=function_name,
                    error=repr(exc),
                    traceback=traceback.format_exc(),
                )

                raise

            emit(
                "exit",
                module=module_name,
                function=function_name,
                result=result,
            )

            return result

        setattr(
            module,
            function_name,
            aw,
        )

    else:

        @functools.wraps(original)
        def sw(*args, **kwargs):

            emit(
                "enter",
                module=module_name,
                function=function_name,
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
                    "error",
                    module=module_name,
                    function=function_name,
                    error=repr(exc),
                    traceback=traceback.format_exc(),
                )

                raise

            emit(
                "exit",
                module=module_name,
                function=function_name,
                result=result,
            )

            return result

        setattr(
            module,
            function_name,
            sw,
        )


TARGETS = [
    (
        "core.knowledge_catalog.qualified_search",
        "search_qualified_catalog",
    ),
    (
        "core.knowledge_catalog.materialization.search",
        "search_runtime_knowledge",
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


for target in TARGETS:
    wrap(*target)


emit(
    "launcher_ready"
)

from core.src.main import app

emit(
    "app_loaded",
    app_type=type(app).__name__,
)
