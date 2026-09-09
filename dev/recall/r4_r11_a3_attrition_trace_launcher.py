from __future__ import annotations

import argparse
import dataclasses
import functools
import inspect
import json
import os
import sqlite3
import sys
import threading
import time
import traceback
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

EVENTS = Path(os.environ["JARVIS_A3_EVENTS"])
EVENTS.parent.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()
_original_sqlite_connect = sqlite3.connect
_seen_wrappers: set[tuple[int, str]] = set()


def now() -> float:
    return time.time()


def safe_repr(value: Any, limit: int = 4000) -> str:
    try:
        text = repr(value)
    except Exception as exc:
        text = f"<repr-error {type(exc).__name__}: {exc}>"
    if len(text) > limit:
        return text[:limit] + "...<truncated>"
    return text


def primitive(value: Any, depth: int = 0) -> Any:
    if depth > 5:
        return safe_repr(value, 1000)

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Path):
        return str(value)

    if dataclasses.is_dataclass(value):
        try:
            return {
                str(k): primitive(v, depth + 1)
                for k, v in dataclasses.asdict(value).items()
            }
        except Exception:
            pass

    if isinstance(value, Mapping):
        out = {}
        for i, (k, v) in enumerate(value.items()):
            if i >= 50:
                out["__truncated__"] = True
                break
            out[str(k)] = primitive(v, depth + 1)
        return out

    if isinstance(value, (list, tuple, set, frozenset)):
        vals = list(value)
        out = [primitive(v, depth + 1) for v in vals[:50]]
        if len(vals) > 50:
            out.append({"__truncated__": len(vals) - 50})
        return out

    for method in ("model_dump", "dict"):
        fn = getattr(value, method, None)
        if callable(fn):
            try:
                return primitive(fn(), depth + 1)
            except Exception:
                pass

    if hasattr(value, "__dict__"):
        try:
            data = {
                k: primitive(v, depth + 1)
                for k, v in vars(value).items()
                if not k.startswith("__")
            }
            if data:
                return data
        except Exception:
            pass

    return safe_repr(value, 2000)


def emit(event: str, **payload: Any) -> None:
    record = {
        "ts": now(),
        "event": event,
        **{k: primitive(v) for k, v in payload.items()},
    }
    line = json.dumps(record, sort_keys=True, ensure_ascii=False)
    with _lock:
        with EVENTS.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
            fh.flush()


def count_population(value: Any) -> int | None:
    if value is None:
        return 0

    if isinstance(value, (str, bytes, bytearray)):
        return None

    if isinstance(value, Mapping):
        for key in (
            "results",
            "candidates",
            "evidence",
            "items",
            "rows",
            "documents",
            "matches",
            "qualified",
            "accepted",
            "sources",
        ):
            candidate = value.get(key)
            if isinstance(candidate, Sequence) and not isinstance(
                candidate, (str, bytes, bytearray)
            ):
                return len(candidate)
        return None

    if isinstance(value, Sequence):
        return len(value)

    for attr in (
        "results",
        "candidates",
        "evidence",
        "items",
        "rows",
        "documents",
        "matches",
        "qualified",
        "accepted",
        "sources",
    ):
        candidate = getattr(value, attr, None)
        if isinstance(candidate, Sequence) and not isinstance(
            candidate, (str, bytes, bytearray)
        ):
            return len(candidate)

    return None


def summarize_item(value: Any) -> dict[str, Any]:
    obj = primitive(value)

    if not isinstance(obj, Mapping):
        return {
            "type": type(value).__name__,
            "repr": safe_repr(value, 1500),
        }

    aliases = {
        "document_id": (
            "document_id",
            "doc_id",
            "source_document_id",
            "knowledge_document_id",
            "id",
        ),
        "chunk_id": (
            "chunk_id",
            "source_chunk_id",
            "knowledge_chunk_id",
        ),
        "title": (
            "title",
            "document_title",
            "source_title",
            "name",
        ),
        "score": (
            "score",
            "combined_score",
            "qualification_score",
            "confidence",
            "rank_score",
            "bm25_score",
        ),
        "decision": (
            "decision",
            "qualification_decision",
            "status",
            "accepted",
            "qualified",
        ),
        "reason": (
            "reason",
            "reasons",
            "diagnostic",
            "diagnostics",
            "explanation",
        ),
        "source": (
            "source",
            "source_path",
            "path",
            "uri",
        ),
    }

    out: dict[str, Any] = {
        "type": type(value).__name__,
    }

    for target, keys in aliases.items():
        for key in keys:
            if key in obj:
                out[target] = obj[key]
                break

    out["raw"] = obj
    return out


def population_items(value: Any) -> list[Any]:
    if value is None:
        return []

    if isinstance(value, Mapping):
        for key in (
            "results",
            "candidates",
            "evidence",
            "items",
            "rows",
            "documents",
            "matches",
            "qualified",
            "accepted",
            "sources",
        ):
            candidate = value.get(key)
            if isinstance(candidate, Sequence) and not isinstance(
                candidate, (str, bytes, bytearray)
            ):
                return list(candidate)
        return []

    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return list(value)

    for attr in (
        "results",
        "candidates",
        "evidence",
        "items",
        "rows",
        "documents",
        "matches",
        "qualified",
        "accepted",
        "sources",
    ):
        candidate = getattr(value, attr, None)
        if isinstance(candidate, Sequence) and not isinstance(
            candidate, (str, bytes, bytearray)
        ):
            return list(candidate)

    return []


def snapshot(value: Any) -> dict[str, Any]:
    items = population_items(value)

    return {
        "type": type(value).__name__,
        "population": count_population(value),
        "items": [summarize_item(item) for item in items[:25]],
        "value": primitive(value),
    }


def classification(module: str, function: str) -> str | None:
    m = module.lower()
    f = function.lower()
    joined = f"{m}.{f}"

    if (
        "normalize_conversational_query" in f
        or ("normalize" in f and "query" in f)
    ):
        return "normalized_query"

    if (
        "search_runtime_knowledge" in f
        or "search_qualified_catalog" in f
        or "_search_catalog" in f
        or (
            "knowledge_catalog" in m
            and "search" in f
        )
    ):
        return "retrieval"

    if (
        "qualification" in joined
        or "qualif" in f
        or f in {"evaluate", "score_candidate", "from_evidence"}
    ):
        return "qualification"

    if (
        "grounding" in joined
        and f not in {"<module>", "__init__"}
    ):
        return "grounding"

    if (
        "evidence" in joined
        and f not in {"<module>", "__init__"}
    ):
        return "evidence"

    return None


def wrap_callable(module: Any, name: str, stage: str) -> bool:
    try:
        original = getattr(module, name)
    except Exception:
        return False

    if not callable(original):
        return False

    key = (id(module), name)
    if key in _seen_wrappers:
        return False

    if getattr(original, "__jarvis_a3_wrapped__", False):
        return False

    if inspect.isclass(original):
        return False

    module_name = getattr(original, "__module__", getattr(module, "__name__", ""))
    qualname = getattr(original, "__qualname__", name)

    @functools.wraps(original)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        call_id = f"{time.time_ns()}-{threading.get_ident()}"

        emit(
            "stage_enter",
            call_id=call_id,
            stage=stage,
            module=module_name,
            function=name,
            qualname=qualname,
            args=[primitive(v) for v in args[:8]],
            kwargs={k: primitive(v) for k, v in list(kwargs.items())[:20]},
        )

        try:
            result = original(*args, **kwargs)
        except Exception as exc:
            emit(
                "stage_error",
                call_id=call_id,
                stage=stage,
                module=module_name,
                function=name,
                error=f"{type(exc).__name__}: {exc}",
                traceback=traceback.format_exc(),
            )
            raise

        emit(
            "stage_exit",
            call_id=call_id,
            stage=stage,
            module=module_name,
            function=name,
            result=snapshot(result),
        )

        return result

    wrapper.__jarvis_a3_wrapped__ = True
    setattr(module, name, wrapper)
    _seen_wrappers.add(key)

    emit(
        "wrapper_installed",
        stage=stage,
        module=getattr(module, "__name__", ""),
        function=name,
    )

    return True


def instrument_module(module: Any) -> int:
    module_name = getattr(module, "__name__", "")

    if not module_name.startswith("core."):
        return 0

    installed = 0

    try:
        members = list(vars(module).items())
    except Exception:
        return 0

    for name, value in members:
        if name.startswith("__"):
            continue

        if not callable(value):
            continue

        owner = getattr(value, "__module__", "")
        if owner and owner != module_name:
            continue

        stage = classification(module_name, name)
        if stage is None:
            continue

        try:
            if wrap_callable(module, name, stage):
                installed += 1
        except Exception as exc:
            emit(
                "wrapper_install_error",
                module=module_name,
                function=name,
                error=f"{type(exc).__name__}: {exc}",
            )

    return installed


class InstrumentingFinder:
    """
    Lightweight post-import instrumentation is handled by the periodic
    sweeper below. This class intentionally does not alter import semantics.
    """
    pass


def sweep_modules() -> int:
    total = 0

    for module_name, module in list(sys.modules.items()):
        if module is None:
            continue

        if not module_name.startswith("core."):
            continue

        try:
            total += instrument_module(module)
        except Exception as exc:
            emit(
                "module_instrument_error",
                module=module_name,
                error=f"{type(exc).__name__}: {exc}",
            )

    return total


def instrumentation_worker() -> None:
    for _ in range(120):
        sweep_modules()
        time.sleep(0.25)


def traced_connect(database: Any, *args: Any, **kwargs: Any):
    caller = inspect.stack()[1]

    emit(
        "sqlite_connect",
        database=str(database),
        caller_module=caller.frame.f_globals.get("__name__", ""),
        caller_function=caller.function,
        caller_file=caller.filename,
        caller_line=caller.lineno,
    )

    return _original_sqlite_connect(database, *args, **kwargs)


sqlite3.connect = traced_connect


def install_http_middleware(app: Any) -> None:
    @app.middleware("http")
    async def a3_http_trace(request, call_next):
        body = await request.body()

        emit(
            "http_request",
            method=request.method,
            path=request.url.path,
            body=body.decode("utf-8", errors="replace"),
        )

        response = await call_next(request)

        emit(
            "http_response",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
        )

        return response


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8011)
    args = parser.parse_args()

    project = os.environ["JARVIS_A3_PROJECT"]
    if project not in sys.path:
        sys.path.insert(0, project)

    emit(
        "launcher_start",
        sys_executable=sys.executable,
        project=project,
    )

    import core.src.main

    app = core.src.main.app

    sweep_modules()

    worker = threading.Thread(
        target=instrumentation_worker,
        name="jarvis-a3-instrumentation",
        daemon=True,
    )
    worker.start()

    install_http_middleware(app)

    emit(
        "application_ready",
        app_type=type(app).__name__,
    )

    import uvicorn

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="warning",
        access_log=False,
    )


if __name__ == "__main__":
    main()
