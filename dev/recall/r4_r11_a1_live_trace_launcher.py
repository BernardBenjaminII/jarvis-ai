from __future__ import annotations

import functools
import importlib
import inspect
import json
import os
import sqlite3
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Any

EVENT_PATH = Path(
    os.environ["JARVIS_A1_EVENTS"]
)

APP_SPEC = os.environ[
    "JARVIS_A1_APP_SPEC"
]

HOST = os.environ.get(
    "JARVIS_A1_HOST",
    "127.0.0.1",
)

PORT = int(
    os.environ.get(
        "JARVIS_A1_PORT",
        "8011",
    )
)

DB_PATH = os.environ.get(
    "JARVIS_A1_DB",
    "",
)

_lock = threading.Lock()


def compact(value: Any) -> Any:

    try:

        if value is None:
            return None

        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        ):
            text = str(value)

            if len(text) > 400:
                text = text[:400] + "..."

            return text

        if isinstance(
            value,
            dict,
        ):
            return {
                str(k): compact(v)
                for k, v
                in list(value.items())[:20]
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

            return {
                "type":
                    type(value).__name__,

                "length":
                    len(seq),

                "preview":
                    [
                        compact(x)
                        for x in seq[:5]
                    ],
            }

        return {
            "type":
                type(value).__name__,

            "repr":
                repr(value)[:400],
        }

    except Exception as exc:

        return {
            "serialization_error":
                repr(exc),
        }


def emit(event: str, **payload):

    record = {
        "ts":
            time.time(),

        "event":
            event,

        **payload,
    }

    with _lock:

        EVENT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with EVENT_PATH.open(
            "a",
            encoding="utf-8",
        ) as fh:

            fh.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    default=str,
                )
                +
                "\n"
            )


emit(
    "launcher_start",
    app_spec=APP_SPEC,
    pid=os.getpid(),
)


#
# ------------------------------------------------------------
# SQLite path observation.
#
# Pass-through only. The returned sqlite connection is the
# original object with no behavioral wrapper.
# ------------------------------------------------------------
#

_original_sqlite_connect = sqlite3.connect


@functools.wraps(
    _original_sqlite_connect
)
def traced_sqlite_connect(
    database,
    *args,
    **kwargs,
):

    db_string = str(
        database
    )

    interesting = (
        "catalog.sqlite"
        in db_string
        or
        (
            DB_PATH
            and
            DB_PATH
            in db_string
        )
    )

    if interesting:

        emit(
            "catalog_sqlite_connect",
            database=db_string,
            thread=threading.current_thread().name,
            stack=[
                f"{frame.filename}:{frame.lineno}:{frame.function}"
                for frame
                in inspect.stack()[1:9]
            ],
        )

    return _original_sqlite_connect(
        database,
        *args,
        **kwargs,
    )


sqlite3.connect = traced_sqlite_connect


#
# ------------------------------------------------------------
# Canonical retrieval wrappers.
#
# Modules are imported BEFORE the application so that
# "from module import function" performed during app import
# receives the wrapped callable.
# ------------------------------------------------------------
#

TARGET_MODULES = (
    "core.knowledge_catalog.search",
    "core.knowledge_catalog.materialization.search",
    "core.knowledge_catalog.qualified_search",
)

TARGET_NAME_HINTS = (
    "search",
    "retriev",
    "qualif",
    "ground",
)


def should_wrap(
    name: str,
) -> bool:

    low = name.lower()

    return any(
        token in low
        for token
        in TARGET_NAME_HINTS
    )


def result_count(
    value: Any,
):

    if value is None:
        return 0

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
            dict,
        ),
    ):
        return len(value)

    for attr in (
        "results",
        "candidates",
        "sources",
        "evidence",
        "items",
    ):

        child = getattr(
            value,
            attr,
            None,
        )

        if isinstance(
            child,
            (
                list,
                tuple,
                set,
                dict,
            ),
        ):
            return len(child)

    return None


def wrap_callable(
    module_name: str,
    name: str,
    fn,
):

    if inspect.iscoroutinefunction(
        fn
    ):

        @functools.wraps(fn)
        async def async_wrapper(
            *args,
            **kwargs,
        ):

            emit(
                "retrieval_enter",
                module=module_name,
                function=name,
                args=compact(args),
                kwargs=compact(kwargs),
            )

            started = time.time()

            try:

                result = await fn(
                    *args,
                    **kwargs,
                )

            except Exception as exc:

                emit(
                    "retrieval_error",
                    module=module_name,
                    function=name,
                    elapsed_ms=(
                        time.time()
                        -
                        started
                    )
                    *
                    1000,
                    error=repr(exc),
                    traceback=traceback.format_exc(),
                )

                raise

            emit(
                "retrieval_exit",
                module=module_name,
                function=name,
                elapsed_ms=(
                    time.time()
                    -
                    started
                )
                *
                1000,
                result_count=result_count(
                    result
                ),
                result=compact(
                    result
                ),
            )

            return result

        return async_wrapper

    @functools.wraps(fn)
    def sync_wrapper(
        *args,
        **kwargs,
    ):

        emit(
            "retrieval_enter",
            module=module_name,
            function=name,
            args=compact(args),
            kwargs=compact(kwargs),
        )

        started = time.time()

        try:

            result = fn(
                *args,
                **kwargs,
            )

        except Exception as exc:

            emit(
                "retrieval_error",
                module=module_name,
                function=name,
                elapsed_ms=(
                    time.time()
                    -
                    started
                )
                *
                1000,
                error=repr(exc),
                traceback=traceback.format_exc(),
            )

            raise

        emit(
            "retrieval_exit",
            module=module_name,
            function=name,
            elapsed_ms=(
                time.time()
                -
                started
            )
            *
            1000,
            result_count=result_count(
                result
            ),
            result=compact(
                result
            ),
        )

        return result

    return sync_wrapper


wrapped = []


for module_name in TARGET_MODULES:

    try:

        module = importlib.import_module(
            module_name
        )

    except Exception as exc:

        emit(
            "retrieval_module_import_error",
            module=module_name,
            error=repr(exc),
        )

        continue

    for name, value in list(
        vars(module).items()
    ):

        if name.startswith("_"):
            continue

        if not callable(value):
            continue

        if not should_wrap(name):
            continue

        #
        # Avoid wrapping imported classes or unrelated
        # third-party callables.
        #
        owner_module = getattr(
            value,
            "__module__",
            "",
        )

        if owner_module != module_name:
            continue

        replacement = wrap_callable(
            module_name,
            name,
            value,
        )

        setattr(
            module,
            name,
            replacement,
        )

        wrapped.append(
            f"{module_name}.{name}"
        )


emit(
    "retrieval_wrappers_installed",
    functions=wrapped,
)


#
# ------------------------------------------------------------
# Import real ASGI application only after tracing wrappers.
# ------------------------------------------------------------
#

module_name, attr_name = APP_SPEC.split(
    ":",
    1,
)

app_module = importlib.import_module(
    module_name
)

app = getattr(
    app_module,
    attr_name,
)


#
# Lightweight ASGI request/response envelope tracer.
#

original_app = app


class TraceASGI:

    def __init__(
        self,
        inner,
    ):
        self.inner = inner

    async def __call__(
        self,
        scope,
        receive,
        send,
    ):

        if scope.get(
            "type"
        ) != "http":

            return await self.inner(
                scope,
                receive,
                send,
            )

        path = scope.get(
            "path",
            "",
        )

        method = scope.get(
            "method",
            "",
        )

        emit(
            "http_request_enter",
            method=method,
            path=path,
        )

        status = None

        async def traced_send(
            message,
        ):

            nonlocal status

            if message.get(
                "type"
            ) == "http.response.start":

                status = message.get(
                    "status"
                )

            return await send(
                message
            )

        try:

            return await self.inner(
                scope,
                receive,
                traced_send,
            )

        finally:

            emit(
                "http_request_exit",
                method=method,
                path=path,
                status=status,
            )


app = TraceASGI(
    original_app
)


if __name__ == "__main__":

    import uvicorn

    emit(
        "uvicorn_start",
        host=HOST,
        port=PORT,
    )

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="warning",
    )
