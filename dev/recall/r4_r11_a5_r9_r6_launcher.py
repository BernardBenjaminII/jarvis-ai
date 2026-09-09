
from __future__ import annotations

import functools
import importlib
import inspect
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
    "r4_r11_a5_r9_r6_events.jsonl"
)

if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))


def safe(value, depth=0):
    if depth > 5:
        return repr(value)

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        if isinstance(value, str) and len(value) > 1400:
            return value[:1400] + "...<truncated>"
        return value

    if isinstance(value, pathlib.Path):
        return str(value)

    if isinstance(value, dict):
        return {
            str(k): safe(v, depth + 1)
            for k, v in list(value.items())[:100]
        }

    if isinstance(value, (list, tuple, set)):
        return [
            safe(v, depth + 1)
            for v in list(value)[:100]
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
                k: safe(v, depth + 1)
                for k, v in vars(value).items()
                if not str(k).startswith("_")
            }
        except Exception:
            pass

    return repr(value)


def emit(kind, **payload):
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


def wrap(name):
    original = getattr(
        qualified,
        name,
        None,
    )

    if not callable(original):
        return

    if inspect.iscoroutinefunction(original):

        @functools.wraps(original)
        async def async_wrapper(
            *args,
            __original=original,
            __name=name,
            **kwargs,
        ):
            emit(
                "qual_enter",
                function=__name,
                args=args,
                kwargs=kwargs,
            )

            try:
                result = await __original(
                    *args,
                    **kwargs,
                )
            except Exception as exc:
                emit(
                    "qual_exception",
                    function=__name,
                    exception=repr(exc),
                )
                raise

            emit(
                "qual_exit",
                function=__name,
                result=result,
            )

            return result

        setattr(
            qualified,
            name,
            async_wrapper,
        )

    else:

        @functools.wraps(original)
        def wrapper(
            *args,
            __original=original,
            __name=name,
            **kwargs,
        ):
            emit(
                "qual_enter",
                function=__name,
                args=args,
                kwargs=kwargs,
            )

            try:
                result = __original(
                    *args,
                    **kwargs,
                )
            except Exception as exc:
                emit(
                    "qual_exception",
                    function=__name,
                    exception=repr(exc),
                )
                raise

            emit(
                "qual_exit",
                function=__name,
                result=result,
            )

            return result

        setattr(
            qualified,
            name,
            wrapper,
        )


for name in (
    "candidate_from_row",
    "qualified_row",
    "qualify_rows",
    "_gate_repair_should_rescue",
    "_gate_repair_qualified_row",
    "_r2_identity_evidence_matches_query",
    "_r2_exact_document_identity_should_rescue",
    "search_qualified_catalog",
):
    wrap(name)


_original_build = (
    integration.build_runtime_request
)


@functools.wraps(_original_build)
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
