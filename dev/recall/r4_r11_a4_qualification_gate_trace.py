from __future__ import annotations

import dataclasses
import functools
import importlib
import inspect
import json
import os
from pathlib import Path
import sys
import traceback
from typing import Any


PROJECT = Path(
    os.environ.get(
        "JARVIS_A4_PROJECT",
        "/media/abdullah/JARVISDATA/Projects/jarvis-ai",
    )
)

EVENT_PATH = Path(
    os.environ["JARVIS_A4_EVENTS"]
)

if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))


def safe_value(value: Any, depth: int = 0) -> Any:
    if depth > 5:
        return repr(value)[:2000]

    if value is None or isinstance(
        value,
        (
            bool,
            int,
            float,
            str,
        ),
    ):
        if isinstance(value, str):
            return value[:12000]
        return value

    if dataclasses.is_dataclass(value):
        try:
            return {
                "__type__": type(value).__name__,
                **{
                    field.name: safe_value(
                        getattr(value, field.name),
                        depth + 1,
                    )
                    for field in dataclasses.fields(value)
                },
            }
        except Exception:
            pass

    if isinstance(value, dict):
        return {
            str(k): safe_value(v, depth + 1)
            for k, v in list(value.items())[:100]
        }

    if isinstance(value, (list, tuple, set)):
        return [
            safe_value(v, depth + 1)
            for v in list(value)[:100]
        ]

    if hasattr(value, "__dict__"):
        try:
            return {
                "__type__": type(value).__name__,
                **{
                    str(k): safe_value(v, depth + 1)
                    for k, v in vars(value).items()
                    if not str(k).startswith("__")
                },
            }
        except Exception:
            pass

    return repr(value)[:12000]


def emit(event: str, **payload: Any) -> None:
    EVENT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    record = {
        "event": event,
        **{
            key: safe_value(value)
            for key, value in payload.items()
        },
    }

    with EVENT_PATH.open(
        "a",
        encoding="utf-8",
    ) as fh:
        fh.write(
            json.dumps(
                record,
                sort_keys=True,
                default=str,
            )
            + "\n"
        )


def result_contract(value: Any) -> dict[str, Any]:
    contract = {
        "type": type(value).__name__,
    }

    for name in (
        "accepted",
        "rejected",
        "candidates",
        "evidence",
        "sources",
        "reason",
        "decision",
        "score",
        "confidence",
        "threshold",
    ):
        if hasattr(value, name):
            try:
                item = getattr(value, name)
                contract[name] = safe_value(item)

                if name in (
                    "accepted",
                    "rejected",
                    "candidates",
                    "evidence",
                    "sources",
                ):
                    try:
                        contract[name + "_count"] = len(item)
                    except Exception:
                        pass
            except Exception:
                pass

    return contract


def should_wrap(
    module_name: str,
    name: str,
    obj: Any,
) -> bool:
    if not (
        inspect.isfunction(obj)
        or inspect.iscoroutinefunction(obj)
    ):
        return False

    if getattr(obj, "__jarvis_a4_wrapped__", False):
        return False

    text = (
        module_name
        + "."
        + name
    ).lower()

    keywords = (
        "qualif",
        "evidence",
        "ground",
        "candidate",
        "search",
        "retriev",
    )

    return any(
        keyword in text
        for keyword in keywords
    )


def install_wrapper(
    module_name: str,
    module: Any,
    name: str,
    original: Any,
) -> None:

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
                    **kwargs,
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
                contract=result_contract(result),
            )
            return result

        async_wrapper.__jarvis_a4_wrapped__ = True
        setattr(module, name, async_wrapper)

    else:

        @functools.wraps(original)
        def sync_wrapper(*args, **kwargs):
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
                    **kwargs,
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
                contract=result_contract(result),
            )
            return result

        sync_wrapper.__jarvis_a4_wrapped__ = True
        setattr(module, name, sync_wrapper)


MODULES = [
    "core.knowledge_catalog.search",
    "core.knowledge_catalog.materialization.search",
    "core.knowledge_catalog.qualified_search",
]

loaded_modules = {}

for module_name in MODULES:
    try:
        module = importlib.import_module(
            module_name
        )
        loaded_modules[module_name] = module
        emit(
            "module_loaded",
            module=module_name,
            file=getattr(module, "__file__", None),
        )
    except Exception as exc:
        emit(
            "module_load_error",
            module=module_name,
            error=repr(exc),
        )


for module_name, module in loaded_modules.items():
    for name, obj in list(vars(module).items()):
        if should_wrap(
            module_name,
            name,
            obj,
        ):
            install_wrapper(
                module_name,
                module,
                name,
                obj,
            )
            emit(
                "wrapper_installed",
                module=module_name,
                function=name,
            )


#
# Patch imported references in already-imported core modules.
#
originals = {}

for module_name, module in loaded_modules.items():
    for name, obj in vars(module).items():
        if getattr(
            obj,
            "__jarvis_a4_wrapped__",
            False,
        ):
            original = getattr(
                obj,
                "__wrapped__",
                None,
            )
            if original is not None:
                originals[id(original)] = obj


for name, module in list(sys.modules.items()):
    if module is None:
        continue

    if not (
        name == "core"
        or name.startswith("core.")
    ):
        continue

    try:
        namespace = vars(module)
    except Exception:
        continue

    for symbol, value in list(namespace.items()):
        replacement = originals.get(id(value))

        if replacement is None:
            continue

        try:
            setattr(
                module,
                symbol,
                replacement,
            )
            emit(
                "imported_reference_patched",
                module=name,
                symbol=symbol,
                wrapped_module=getattr(
                    replacement,
                    "__module__",
                    None,
                ),
                wrapped_function=getattr(
                    replacement,
                    "__name__",
                    None,
                ),
            )
        except Exception:
            pass


#
# Import application AFTER wrappers are installed.
#
main = importlib.import_module(
    "core.src.main"
)

app = main.app

emit(
    "app_ready",
    app_type=type(app).__name__,
)


#
# HTTP request/response observation.
#
@app.middleware("http")
async def jarvis_a4_http_trace(request, call_next):
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
        status_code=response.status_code,
    )

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(
            os.environ.get(
                "JARVIS_A4_PORT",
                "8011",
            )
        ),
        log_level="warning",
    )
