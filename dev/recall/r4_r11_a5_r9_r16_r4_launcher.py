
from __future__ import annotations

import dataclasses
import functools
import importlib
import json
import pathlib
import re
import sys
import time


PROJECT = pathlib.Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
).resolve()

EVENTS = (
    PROJECT
    / "artifacts/genesis_recall/"
    "r4_r11_a5_r9_r16_r4_events.jsonl"
)

TARGET_PATH = "/api/knowledge/conversation"

if str(PROJECT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT),
    )


def safe(value, depth=0):

    if depth > 5:
        return repr(value)

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        if isinstance(value, str) and len(value) > 1500:
            return value[:1500] + "...<truncated>"

        return value

    if dataclasses.is_dataclass(value):
        try:
            return {
                f.name:
                    safe(
                        getattr(value, f.name),
                        depth + 1,
                    )
                for f in dataclasses.fields(value)
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

    if hasattr(value, "model_dump"):
        try:
            return safe(
                value.model_dump(),
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


def population(value):

    summary = {
        "evidence": 0,
        "accepted": 0,
        "sources": 0,
        "citations": 0,
    }

    seen = set()

    def walk(obj, depth=0):

        if obj is None or depth > 7:
            return

        try:
            identity = id(obj)

            if identity in seen:
                return

            seen.add(identity)

        except Exception:
            pass

        if isinstance(obj, str):
            summary["citations"] = max(
                summary["citations"],
                len(
                    re.findall(
                        r"\[C\d+",
                        obj,
                    )
                ),
            )
            return

        if isinstance(obj, dict):

            for key, child in obj.items():

                name = str(key).casefold()

                if isinstance(
                    child,
                    (list, tuple),
                ):

                    count = len(child)

                    if name in (
                        "evidence",
                        "evidence_items",
                    ):
                        summary["evidence"] = max(
                            summary["evidence"],
                            count,
                        )

                    elif name in (
                        "accepted",
                        "accepted_candidates",
                        "qualified",
                        "qualified_results",
                    ):
                        summary["accepted"] = max(
                            summary["accepted"],
                            count,
                        )

                    elif name in (
                        "sources",
                        "source_items",
                    ):
                        summary["sources"] = max(
                            summary["sources"],
                            count,
                        )

                walk(
                    child,
                    depth + 1,
                )

            return

        if isinstance(
            obj,
            (list, tuple, set),
        ):

            for child in obj:
                walk(
                    child,
                    depth + 1,
                )

            return

        if dataclasses.is_dataclass(obj):

            try:
                for f in dataclasses.fields(obj):
                    child = getattr(
                        obj,
                        f.name,
                    )

                    walk(
                        {
                            f.name:
                                child
                        },
                        depth + 1,
                    )

                return

            except Exception:
                pass

        if hasattr(obj, "model_dump"):

            try:
                walk(
                    obj.model_dump(),
                    depth + 1,
                )
                return
            except Exception:
                pass

        if hasattr(obj, "__dict__"):

            try:
                walk(
                    vars(obj),
                    depth + 1,
                )
            except Exception:
                pass

    walk(value)

    return summary


def typename(value):

    if value is None:
        return "None"

    return (
        f"{type(value).__module__}."
        f"{type(value).__name__}"
    )


SEQ = 0


def emit(kind, **data):

    global SEQ

    SEQ += 1

    record = {
        "seq": SEQ,
        "ts": time.time(),
        "kind": kind,
        **data,
    }

    with EVENTS.open(
        "a",
        encoding="utf-8",
    ) as fp:

        fp.write(
            json.dumps(
                record,
                ensure_ascii=False,
                default=str,
            )
            + "\n"
        )


# ------------------------------------------------------------
# Import first. NO global profiler during startup.
# ------------------------------------------------------------

main = importlib.import_module(
    "core.src.main"
)

app = main.app


# ------------------------------------------------------------
# Resolve from API routers, not app.routes.
# ------------------------------------------------------------

router_candidates = []

for name, value in vars(main).items():

    # GENESIS_RECALL_R4_R11_A5_R9_R16_R4_R1_ROUTE_GUARD
    routes = getattr(
        value,
        "routes",
        None,
    )

    if routes is None:
        continue

    # Some objects exported by core.src.main expose ``routes`` as
    # a class/property descriptor rather than a concrete route list.
    # Only inspect real iterable route collections.
    if isinstance(routes, property):
        continue

    try:
        route_list = list(routes)
    except TypeError:
        continue
    except Exception as exc:
        emit(
            "router_enumeration_skip",
            variable=name,
            routes_type=(
                f"{type(routes).__module__}."
                f"{type(routes).__name__}"
            ),
            error=repr(exc),
        )
        continue

    for route in route_list:

        path = str(
            getattr(
                route,
                "path",
                "",
            )
            or ""
        )

        methods = set(
            getattr(
                route,
                "methods",
                set(),
            )
            or set()
        )

        endpoint = getattr(
            route,
            "endpoint",
            None,
        )

        endpoint_module = str(
            getattr(
                endpoint,
                "__module__",
                "",
            )
            or ""
        )

        endpoint_name = str(
            getattr(
                endpoint,
                "__qualname__",
                getattr(
                    endpoint,
                    "__name__",
                    "",
                ),
            )
            or ""
        )

        emit(
            "router_route",
            router_variable=name,
            path=path,
            methods=sorted(methods),
            endpoint_module=endpoint_module,
            endpoint_name=endpoint_name,
        )

        if (
            path == TARGET_PATH
            and
            "POST" in methods
        ):
            router_candidates.append(
                (
                    name,
                    route,
                )
            )


emit(
    "target_candidate_count",
    count=len(router_candidates),
)


if len(router_candidates) != 1:

    emit(
        "route_resolution_fail",
        candidates=[
            {
                "router": name,
                "path":
                    getattr(
                        route,
                        "path",
                        None,
                    ),
            }
            for name, route
            in router_candidates
        ],
    )

    resolved_route = None

else:

    router_name, resolved_route = (
        router_candidates[0]
    )

    endpoint = getattr(
        resolved_route,
        "endpoint",
        None,
    )

    emit(
        "route_resolved",
        router=router_name,
        path=getattr(
            resolved_route,
            "path",
            None,
        ),
        endpoint_module=getattr(
            endpoint,
            "__module__",
            None,
        ),
        endpoint_name=getattr(
            endpoint,
            "__qualname__",
            getattr(
                endpoint,
                "__name__",
                None,
            ),
        ),
    )


# ------------------------------------------------------------
# Request-scoped wrapper.
#
# This is the key improvement over R16:
# no sys.setprofile() while JARVIS starts.
# ------------------------------------------------------------

if resolved_route is not None:

    original = (
        resolved_route.dependant.call
    )

    if original is None:
        original = (
            resolved_route.endpoint
        )

    import inspect

    async_callable = inspect.iscoroutinefunction(
        original
    )


    if async_callable:

        @functools.wraps(original)
        async def traced_route(
            *args,
            **kwargs,
        ):

            emit(
                "route_enter",
                function=getattr(
                    original,
                    "__qualname__",
                    repr(original),
                ),
            )

            # ----------------------------------------------
            # Install profiler ONLY for this request.
            # ----------------------------------------------

            def profiler(frame, event, arg):

                if event != "return":
                    return profiler

                filename = str(
                    frame.f_code.co_filename
                )

                if not filename.startswith(
                    str(PROJECT)
                ):
                    return profiler

                module = str(
                    frame.f_globals.get(
                        "__name__",
                        "",
                    )
                )

                fn = str(
                    frame.f_code.co_name
                )

                low = (
                    module
                    + "."
                    + fn
                ).casefold()

                if not any(
                    token in low
                    for token in (
                        "conversation",
                        "ground",
                        "answer",
                        "evidence",
                        "orchestr",
                        "qualif",
                        "response",
                        "runtime_request",
                        "service",
                    )
                ):
                    return profiler

                summary = population(arg)

                emit(
                    "function_return",
                    module=module,
                    function=fn,
                    return_type=typename(arg),
                    evidence=summary["evidence"],
                    accepted=summary["accepted"],
                    sources=summary["sources"],
                    citations=summary["citations"],
                )

                return profiler


            sys.setprofile(
                profiler
            )

            try:

                result = await original(
                    *args,
                    **kwargs,
                )

            finally:

                sys.setprofile(
                    None
                )


            summary = population(
                result
            )

            emit(
                "route_return",
                function=getattr(
                    original,
                    "__qualname__",
                    repr(original),
                ),
                return_type=typename(
                    result
                ),
                evidence=summary[
                    "evidence"
                ],
                accepted=summary[
                    "accepted"
                ],
                sources=summary[
                    "sources"
                ],
                citations=summary[
                    "citations"
                ],
                payload=safe(
                    result
                ),
            )

            return result


    else:

        @functools.wraps(original)
        def traced_route(
            *args,
            **kwargs,
        ):

            emit(
                "route_enter",
                function=getattr(
                    original,
                    "__qualname__",
                    repr(original),
                ),
            )


            def profiler(frame, event, arg):

                if event != "return":
                    return profiler

                filename = str(
                    frame.f_code.co_filename
                )

                if not filename.startswith(
                    str(PROJECT)
                ):
                    return profiler

                module = str(
                    frame.f_globals.get(
                        "__name__",
                        "",
                    )
                )

                fn = str(
                    frame.f_code.co_name
                )

                low = (
                    module
                    + "."
                    + fn
                ).casefold()

                if not any(
                    token in low
                    for token in (
                        "conversation",
                        "ground",
                        "answer",
                        "evidence",
                        "orchestr",
                        "qualif",
                        "response",
                        "runtime_request",
                        "service",
                    )
                ):
                    return profiler

                summary = population(arg)

                emit(
                    "function_return",
                    module=module,
                    function=fn,
                    return_type=typename(arg),
                    evidence=summary["evidence"],
                    accepted=summary["accepted"],
                    sources=summary["sources"],
                    citations=summary["citations"],
                )

                return profiler


            sys.setprofile(
                profiler
            )

            try:

                result = original(
                    *args,
                    **kwargs,
                )

            finally:

                sys.setprofile(
                    None
                )


            summary = population(
                result
            )

            emit(
                "route_return",
                function=getattr(
                    original,
                    "__qualname__",
                    repr(original),
                ),
                return_type=typename(
                    result
                ),
                evidence=summary[
                    "evidence"
                ],
                accepted=summary[
                    "accepted"
                ],
                sources=summary[
                    "sources"
                ],
                citations=summary[
                    "citations"
                ],
                payload=safe(
                    result
                ),
            )

            return result


    resolved_route.dependant.call = (
        traced_route
    )

    emit(
        "route_wrapped",
        path=TARGET_PATH,
    )


emit(
    "launcher_ready",
    route_found=(
        resolved_route
        is not None
    ),
)
