from __future__ import annotations

import dataclasses
import functools
import importlib
import inspect
import json
import os
from pathlib import Path
import sys
import threading
import time
import traceback
from typing import Any


PROJECT = Path(
    os.environ[
        "JARVIS_A5_PROJECT"
    ]
).resolve()

EVENTS = Path(
    os.environ[
        "JARVIS_A5_EVENTS"
    ]
)

PORT = int(
    os.environ.get(
        "JARVIS_A5_PORT",
        "8011",
    )
)


if str(PROJECT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT),
    )


EVENTS.parent.mkdir(
    parents=True,
    exist_ok=True,
)


LOCK = threading.Lock()
SEEN: set[
    tuple[
        int,
        str,
    ]
] = set()


COMPONENTS = (
    "lexical",
    "entity",
    "phrase",
    "semantic",
    "subject",
    "provenance",
)


INTERESTING_FUNCTION_TERMS = (
    "candidate_from_row",
    "qualified_row",
    "qualify_rows",
    "search_qualified_catalog",
    "gate_repair",
    "identity",
    "qualif",
    "score",
    "evidence",
)


BLOCKED_FIELDS = {
    "content",
    "excerpt",
    "text",
    "body",
    "raw",
    "raw_json",
    "payload",
    "document_text",
    "full_text",
}


def clean(
    value: Any,
    depth: int = 0,
) -> Any:

    if depth > 5:
        return (
            repr(
                value
            )[:500]
        )

    if value is None or isinstance(
        value,
        (
            bool,
            int,
            float,
        ),
    ):
        return value

    if isinstance(
        value,
        str,
    ):
        if len(value) > 500:
            return (
                value[:500]
                +
                "...<truncated>"
            )

        return value

    if dataclasses.is_dataclass(
        value
    ):

        output = {
            "__type__":
                type(
                    value
                ).__name__,
        }

        for field in dataclasses.fields(
            value
        ):

            name = field.name

            if name.lower() in BLOCKED_FIELDS:
                continue

            try:
                child = getattr(
                    value,
                    name,
                )

            except Exception:
                continue

            output[
                name
            ] = clean(
                child,
                depth + 1,
            )

        return output

    if isinstance(
        value,
        dict,
    ):

        result = {}

        for index, (
            key,
            child,
        ) in enumerate(
            value.items()
        ):

            if index >= 60:
                break

            if str(
                key
            ).lower() in BLOCKED_FIELDS:
                continue

            result[
                str(
                    key
                )
            ] = clean(
                child,
                depth + 1,
            )

        return result

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):

        values = list(
            value
        )

        return [
            clean(
                child,
                depth + 1,
            )
            for child in values[:60]
        ]

    if hasattr(
        value,
        "__dict__",
    ):

        try:

            result = {
                "__type__":
                    type(
                        value
                    ).__name__,
            }

            for key, child in list(
                vars(
                    value
                ).items()
            )[:60]:

                if str(
                    key
                ).lower() in BLOCKED_FIELDS:
                    continue

                result[
                    str(
                        key
                    )
                ] = clean(
                    child,
                    depth + 1,
                )

            return result

        except Exception:
            pass

    return repr(
        value
    )[:500]


def emit(
    event: str,
    **payload: Any,
) -> None:

    record = {
        "ts":
            time.time(),

        "event":
            event,

        **{
            key:
                clean(
                    value
                )
            for key, value
            in payload.items()
        },
    }

    with LOCK:

        with EVENTS.open(
            "a",
            encoding="utf-8",
        ) as fh:

            fh.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    sort_keys=True,
                    default=str,
                )
                +
                "\n"
            )


def interesting(
    module_name: str,
    name: str,
    value: Any,
) -> bool:

    if not (
        inspect.isfunction(
            value
        )
        or
        inspect.iscoroutinefunction(
            value
        )
    ):
        return False

    owner = getattr(
        value,
        "__module__",
        "",
    )

    if owner != module_name:
        return False

    combined = (
        module_name
        +
        "."
        +
        name
    ).lower()

    return any(
        term in combined
        for term
        in INTERESTING_FUNCTION_TERMS
    )


def frame_locals_snapshot() -> dict:
    """
    Capture the caller's local variables after a function
    has executed where possible.

    This is diagnostic only and intentionally bounded.
    """

    frame = inspect.currentframe()

    if frame is None:
        return {}

    caller = frame.f_back

    if caller is None:
        return {}

    caller = caller.f_back

    if caller is None:
        return {}

    locals_out = {}

    for key, value in list(
        caller.f_locals.items()
    )[:80]:

        lowered = str(
            key
        ).lower()

        if (
            any(
                component
                in lowered
                for component
                in COMPONENTS
            )
            or
            lowered
            in {
                "score",
                "final",
                "final_score",
                "threshold",
                "candidate",
                "row",
                "accepted",
                "rejected",
                "confidence",
            }
        ):

            locals_out[
                key
            ] = clean(
                value
            )

    return locals_out


def wrap(
    module_name: str,
    module: Any,
    name: str,
    original: Any,
) -> None:

    key = (
        id(
            module
        ),
        name,
    )

    if key in SEEN:
        return

    if getattr(
        original,
        "__jarvis_a5_wrapped__",
        False,
    ):
        return


    if inspect.iscoroutinefunction(
        original
    ):

        @functools.wraps(
            original
        )
        async def async_wrapper(
            *args,
            **kwargs,
        ):

            call_id = (
                f"{time.time_ns()}-"
                f"{threading.get_ident()}"
            )

            emit(
                "function_enter",
                call_id=call_id,
                module=module_name,
                function=name,
                args=args[:8],
                kwargs=dict(
                    list(
                        kwargs.items()
                    )[:30]
                ),
            )

            try:

                result = await original(
                    *args,
                    **kwargs,
                )

            except Exception as exc:

                emit(
                    "function_error",
                    call_id=call_id,
                    module=module_name,
                    function=name,
                    error=repr(
                        exc
                    ),
                    traceback=traceback.format_exc(),
                )

                raise


            emit(
                "function_exit",
                call_id=call_id,
                module=module_name,
                function=name,
                result=result,
                local_surface=(
                    frame_locals_snapshot()
                ),
            )

            return result


        async_wrapper.__jarvis_a5_wrapped__ = True

        setattr(
            module,
            name,
            async_wrapper,
        )


    else:

        @functools.wraps(
            original
        )
        def sync_wrapper(
            *args,
            **kwargs,
        ):

            call_id = (
                f"{time.time_ns()}-"
                f"{threading.get_ident()}"
            )

            emit(
                "function_enter",
                call_id=call_id,
                module=module_name,
                function=name,
                args=args[:8],
                kwargs=dict(
                    list(
                        kwargs.items()
                    )[:30]
                ),
            )

            try:

                result = original(
                    *args,
                    **kwargs,
                )

            except Exception as exc:

                emit(
                    "function_error",
                    call_id=call_id,
                    module=module_name,
                    function=name,
                    error=repr(
                        exc
                    ),
                    traceback=traceback.format_exc(),
                )

                raise


            emit(
                "function_exit",
                call_id=call_id,
                module=module_name,
                function=name,
                result=result,
                local_surface=(
                    frame_locals_snapshot()
                ),
            )

            return result


        sync_wrapper.__jarvis_a5_wrapped__ = True

        setattr(
            module,
            name,
            sync_wrapper,
        )


    SEEN.add(
        key
    )


def install_module(
    module_name: str,
) -> None:

    try:

        module = importlib.import_module(
            module_name
        )

    except Exception as exc:

        emit(
            "module_import_error",
            module=module_name,
            error=repr(
                exc
            ),
        )

        return


    for name, value in list(
        vars(
            module
        ).items()
    ):

        if not interesting(
            module_name,
            name,
            value,
        ):
            continue

        wrap(
            module_name,
            module,
            name,
            value,
        )

        emit(
            "wrapper_installed",
            module=module_name,
            function=name,
        )


TARGET_MODULES = (
    "core.knowledge_catalog.qualified_search",
    "core.knowledge_catalog.search",
    "core.knowledge_catalog.materialization.search",
)


for module_name in TARGET_MODULES:

    install_module(
        module_name
    )


#
# Import real app after qualified-search instrumentation.
#

main = importlib.import_module(
    "core.src.main"
)

app = main.app


#
# Patch references imported by value elsewhere in core.*
# using hash-safe object identity.
#

wrapped_by_original_id = {}


for module_name in TARGET_MODULES:

    module = sys.modules.get(
        module_name
    )

    if module is None:
        continue

    for _, value in vars(
        module
    ).items():

        original = getattr(
            value,
            "__wrapped__",
            None,
        )

        if original is not None:

            wrapped_by_original_id[
                id(
                    original
                )
            ] = value


for module_name, module in list(
    sys.modules.items()
):

    if module is None:
        continue

    if not (
        module_name == "core"
        or
        module_name.startswith(
            "core."
        )
    ):
        continue

    try:

        namespace = vars(
            module
        )

    except Exception:

        continue

    for symbol, value in list(
        namespace.items()
    ):

        replacement = (
            wrapped_by_original_id.get(
                id(
                    value
                )
            )
        )

        if replacement is None:
            continue

        try:

            setattr(
                module,
                symbol,
                replacement,
            )

            emit(
                "import_reference_patched",
                module=module_name,
                symbol=symbol,
            )

        except Exception:

            pass


@app.middleware(
    "http"
)
async def a5_http_trace(
    request,
    call_next,
):

    body = await request.body()

    emit(
        "http_request",
        method=request.method,
        path=request.url.path,
        body=body.decode(
            "utf-8",
            errors="replace",
        ),
    )

    response = await call_next(
        request
    )

    emit(
        "http_response",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
    )

    return response


if __name__ == "__main__":

    import uvicorn

    emit(
        "launcher_ready",
        executable=sys.executable,
        project=str(
            PROJECT
        ),
    )

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=PORT,
        log_level="warning",
        access_log=False,
    )
