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
    os.environ["JARVIS_A5_R2_PROJECT"]
).resolve()

EVENTS = Path(
    os.environ["JARVIS_A5_R2_EVENTS"]
)

PORT = int(
    os.environ.get(
        "JARVIS_A5_R2_PORT",
        "8011",
    )
)

if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

EVENTS.parent.mkdir(
    parents=True,
    exist_ok=True,
)

LOCK = threading.Lock()


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


IMPORTANT_KEYS = {
    "document_id",
    "chunk_id",
    "source_id",
    "title",
    "subject",
    "backend",
    "confidence",
    "retrieval_score",
    "relevance_score",
    "semantic",
    "semantic_score",
    "hybrid_score",
    "similarity",
    "similarity_score",
    "vector_score",
    "qualification_score",
    "qualification_components",
    "accepted",
    "rejected",
    "score",
    "final",
}


def clean(value: Any, depth: int = 0) -> Any:

    if depth > 6:
        return repr(value)[:400]

    if value is None or isinstance(
        value,
        (bool, int, float),
    ):
        return value

    if isinstance(value, str):
        return (
            value
            if len(value) <= 400
            else value[:400] + "...<truncated>"
        )

    if dataclasses.is_dataclass(value):

        result = {
            "__type__": type(value).__name__,
        }

        for field in dataclasses.fields(value):

            name = field.name

            if name.lower() in BLOCKED_FIELDS:
                continue

            try:
                child = getattr(value, name)
            except Exception:
                continue

            result[name] = clean(
                child,
                depth + 1,
            )

        return result

    if isinstance(value, dict):

        result = {}

        for index, (key, child) in enumerate(
            value.items()
        ):

            if index >= 80:
                break

            key_text = str(key)

            if key_text.lower() in BLOCKED_FIELDS:
                continue

            result[key_text] = clean(
                child,
                depth + 1,
            )

        return result

    if isinstance(
        value,
        (list, tuple, set),
    ):

        return [
            clean(child, depth + 1)
            for child in list(value)[:80]
        ]

    if hasattr(value, "__dict__"):

        try:
            return clean(
                vars(value),
                depth + 1,
            )
        except Exception:
            pass

    return repr(value)[:400]


def emit(event: str, **payload: Any) -> None:

    record = {
        "ts": time.time(),
        "event": event,
        **{
            key: clean(value)
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
                    sort_keys=True,
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )


TARGET_FUNCTIONS = {
    "candidate_from_row",
    "qualified_row",
    "qualify_rows",
    "search_qualified_catalog",
}


TARGET_MODULES = {
    "core.knowledge_catalog.qualified_search",
    "core.knowledge_catalog.search",
    "core.knowledge_catalog.materialization.search",
}


wrapped_by_original_id = {}


def install_wrapper(module_name: str, function_name: str) -> None:

    module = importlib.import_module(
        module_name
    )

    original = getattr(
        module,
        function_name,
        None,
    )

    if original is None:
        return

    if not callable(original):
        return

    if getattr(
        original,
        "__jarvis_a5_r2_wrapped__",
        False,
    ):
        return


    if inspect.iscoroutinefunction(original):

        @functools.wraps(original)
        async def async_wrapper(*args, **kwargs):

            call_id = (
                f"{time.time_ns()}-"
                f"{threading.get_ident()}"
            )

            emit(
                "function_enter",
                call_id=call_id,
                module=module_name,
                function=function_name,
                args=args[:10],
                kwargs=dict(
                    list(kwargs.items())[:30]
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
                    function=function_name,
                    error=repr(exc),
                    traceback=traceback.format_exc(),
                )
                raise

            emit(
                "function_exit",
                call_id=call_id,
                module=module_name,
                function=function_name,
                result=result,
            )

            return result

        wrapper = async_wrapper

    else:

        @functools.wraps(original)
        def sync_wrapper(*args, **kwargs):

            call_id = (
                f"{time.time_ns()}-"
                f"{threading.get_ident()}"
            )

            emit(
                "function_enter",
                call_id=call_id,
                module=module_name,
                function=function_name,
                args=args[:10],
                kwargs=dict(
                    list(kwargs.items())[:30]
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
                    function=function_name,
                    error=repr(exc),
                    traceback=traceback.format_exc(),
                )
                raise

            emit(
                "function_exit",
                call_id=call_id,
                module=module_name,
                function=function_name,
                result=result,
            )

            return result

        wrapper = sync_wrapper


    wrapper.__jarvis_a5_r2_wrapped__ = True

    setattr(
        module,
        function_name,
        wrapper,
    )

    wrapped_by_original_id[
        id(original)
    ] = wrapper

    emit(
        "wrapper_installed",
        module=module_name,
        function=function_name,
    )


#
# Install qualification wrappers before application import.
#
qualified = importlib.import_module(
    "core.knowledge_catalog.qualified_search"
)

for function_name in TARGET_FUNCTIONS:
    if hasattr(qualified, function_name):
        install_wrapper(
            "core.knowledge_catalog.qualified_search",
            function_name,
        )


#
# Runtime knowledge retrieval.
#
runtime_search = importlib.import_module(
    "core.knowledge_catalog.materialization.search"
)

if hasattr(
    runtime_search,
    "search_runtime_knowledge",
):
    install_wrapper(
        "core.knowledge_catalog.materialization.search",
        "search_runtime_knowledge",
    )


#
# Import actual application.
#
main = importlib.import_module(
    "core.src.main"
)

app = main.app


#
# Patch by-value imports using identity only.
#
for module_name, module in list(
    sys.modules.items()
):

    if module is None:
        continue

    if not (
        module_name == "core"
        or module_name.startswith("core.")
    ):
        continue

    try:
        namespace = vars(module)
    except Exception:
        continue

    for symbol, value in list(
        namespace.items()
    ):

        replacement = wrapped_by_original_id.get(
            id(value)
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


@app.middleware("http")
async def trace_request(request, call_next):

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

    response = await call_next(request)

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
        project=str(PROJECT),
    )

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=PORT,
        log_level="warning",
        access_log=False,
    )
