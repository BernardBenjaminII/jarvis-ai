
from __future__ import annotations

import dataclasses
import functools
import importlib
import itertools
import json
import pathlib
import re
import sys
import threading
import time


PROJECT = pathlib.Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
).resolve()

EVENTS = (
    PROJECT
    / "artifacts"
    / "genesis_recall"
    / "r4_r11_a5_r9_r16_events.jsonl"
)

# GENESIS_RECALL_R4_R11_A5_R9_R16_R2_DURABLE
TARGET_ROUTE = None

SEQ = itertools.count(
    1
)

LOCK = threading.Lock()


if str(PROJECT) not in sys.path:

    sys.path.insert(
        0,
        str(PROJECT),
    )


# ================================================================
# SUMMARY HELPERS
# ================================================================

FIELD_KEYS = {
    "evidence",
    "evidence_items",
    "accepted",
    "accepted_candidates",
    "qualified",
    "qualified_results",
    "sources",
    "source_items",
}


def safe(
    value,
    depth=0,
):

    if depth > 4:
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

        if (
            isinstance(
                value,
                str,
            )
            and
            len(value) > 1200
        ):

            return (
                value[:1200]
                + "...<truncated>"
            )

        return value

    if dataclasses.is_dataclass(
        value
    ):

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
                in dataclasses.fields(
                    value
                )
            }

        except Exception:
            pass

    if isinstance(
        value,
        dict,
    ):

        return {

            str(key):
                safe(
                    child,
                    depth + 1,
                )

            for key, child
            in list(
                value.items()
            )[:120]
        }

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):

        return [

            safe(
                child,
                depth + 1,
            )

            for child
            in list(value)[:120]
        ]

    if hasattr(
        value,
        "model_dump",
    ):

        try:

            return safe(
                value.model_dump(),
                depth + 1,
            )

        except Exception:
            pass

    if hasattr(
        value,
        "__dict__",
    ):

        try:

            return {

                str(key):
                    safe(
                        child,
                        depth + 1,
                    )

                for key, child
                in vars(
                    value
                ).items()

                if not str(
                    key
                ).startswith("_")
            }

        except Exception:
            pass

    return repr(value)


def population_summary(
    value,
):

    summary = {

        "evidence":
            0,

        "accepted":
            0,

        "sources":
            0,

        "citations":
            0,
    }


    visited = set()


    def walk(
        obj,
        depth=0,
    ):

        if (
            obj is None
            or
            depth > 6
        ):
            return


        identifier = id(obj)

        if identifier in visited:
            return

        visited.add(
            identifier
        )


        if isinstance(
            obj,
            str,
        ):

            citations = len(
                re.findall(
                    r"\[C\d+",
                    obj,
                )
            )

            summary[
                "citations"
            ] = max(
                summary[
                    "citations"
                ],
                citations,
            )

            return


        if isinstance(
            obj,
            dict,
        ):

            for key, child in (
                obj.items()
            ):

                name = str(
                    key
                ).casefold()


                if isinstance(
                    child,
                    (
                        list,
                        tuple,
                    ),
                ):

                    count = len(
                        child
                    )

                    if name in (
                        "evidence",
                        "evidence_items",
                    ):

                        summary[
                            "evidence"
                        ] = max(
                            summary[
                                "evidence"
                            ],
                            count,
                        )

                    elif name in (
                        "accepted",
                        "accepted_candidates",
                        "qualified",
                        "qualified_results",
                    ):

                        summary[
                            "accepted"
                        ] = max(
                            summary[
                                "accepted"
                            ],
                            count,
                        )

                    elif name in (
                        "sources",
                        "source_items",
                    ):

                        summary[
                            "sources"
                        ] = max(
                            summary[
                                "sources"
                            ],
                            count,
                        )


                walk(
                    child,
                    depth + 1,
                )

            return


        if isinstance(
            obj,
            (
                list,
                tuple,
                set,
            ),
        ):

            for child in obj:

                walk(
                    child,
                    depth + 1,
                )

            return


        if dataclasses.is_dataclass(
            obj
        ):

            try:

                for field in (
                    dataclasses.fields(
                        obj
                    )
                ):

                    name = (
                        field.name
                        .casefold()
                    )

                    child = getattr(
                        obj,
                        field.name,
                    )


                    if isinstance(
                        child,
                        (
                            list,
                            tuple,
                        ),
                    ):

                        count = len(
                            child
                        )

                        if name in (
                            "evidence",
                            "evidence_items",
                        ):

                            summary[
                                "evidence"
                            ] = max(
                                summary[
                                    "evidence"
                                ],
                                count,
                            )

                        elif name in (
                            "accepted",
                            "accepted_candidates",
                            "qualified",
                            "qualified_results",
                        ):

                            summary[
                                "accepted"
                            ] = max(
                                summary[
                                    "accepted"
                                ],
                                count,
                            )

                        elif name in (
                            "sources",
                            "source_items",
                        ):

                            summary[
                                "sources"
                            ] = max(
                                summary[
                                    "sources"
                                ],
                                count,
                            )


                    walk(
                        child,
                        depth + 1,
                    )

                return

            except Exception:
                pass


        if hasattr(
            obj,
            "__dict__",
        ):

            try:

                walk(
                    vars(obj),
                    depth + 1,
                )

            except Exception:
                pass


    walk(
        value
    )

    return summary


def type_name(
    value,
):

    if value is None:
        return "None"

    return (
        f"{type(value).__module__}."
        f"{type(value).__name__}"
    )


def emit(
    kind,
    **payload,
):

    with LOCK:

        row = {

            "seq":
                next(SEQ),

            "ts":
                time.time(),

            "kind":
                kind,

            **payload,
        }


        with EVENTS.open(
            "a",
            encoding="utf-8",
        ) as fp:

            fp.write(
                json.dumps(
                    row,
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )


# ================================================================
# PROFILE FILTER
# ================================================================

FUNCTION_WORDS = (
    "ground",
    "answer",
    "runtime_request",
    "conversation",
    "orchestr",
    "execute",
    "respond",
    "publish",
    "serialize",
    "response",
    "qualif",
    "evidence",
)


def relevant_frame(
    frame,
):

    filename = pathlib.Path(
        frame.f_code.co_filename
    )

    try:

        relative = filename.resolve().relative_to(
            PROJECT
        )

    except Exception:

        return False


    relative_text = str(
        relative
    ).casefold()


    if not (
        relative_text.startswith(
            "core/conversation/"
        )
        or
        relative_text.startswith(
            "core/src/"
        )
        or
        relative_text.startswith(
            "core/knowledge_catalog/"
        )
        or
        relative_text.startswith(
            "core/retrieval/evidence"
        )
    ):

        return False


    function = (
        frame.f_code.co_name
        .casefold()
    )


    return any(
        word in function

        for word
        in FUNCTION_WORDS
    )


def profiler(
    frame,
    event,
    arg,
):

    if event != "return":

        return profiler


    if not relevant_frame(
        frame
    ):

        return profiler


    try:

        summary = (
            population_summary(
                arg
            )
        )

        emit(

            "function_return",

            file=
                frame.f_code.co_filename,

            module=
                frame.f_globals.get(
                    "__name__",
                    "",
                ),

            function=
                frame.f_code.co_name,

            line=
                frame.f_lineno,

            return_type=
                type_name(arg),

            evidence=
                summary[
                    "evidence"
                ],

            accepted=
                summary[
                    "accepted"
                ],

            sources=
                summary[
                    "sources"
                ],

            citations=
                summary[
                    "citations"
                ],
        )

    except Exception:

        pass


    return profiler


sys.setprofile(
    profiler
)

threading.setprofile(
    profiler
)


# GENESIS_RECALL_R4_R11_A5_R9_R16_R2_DURABLE
import atexit


def _disable_genesis_profiler():

    try:
        sys.setprofile(None)
    except Exception:
        pass

    try:
        threading.setprofile(None)
    except Exception:
        pass


atexit.register(
    _disable_genesis_profiler
)


# ================================================================
# LOAD REAL PRODUCTION APP
# ================================================================

main = importlib.import_module(
    "core.src.main"
)

app = main.app


# ================================================================
# WRAP ACTUAL FASTAPI ROUTE CALL
#
# APIRoute.dependant.call is the callable FastAPI will invoke.
# Replacing this in the shadow process lets us see the real route
# return object without touching production source.
# ================================================================

target_route = None

route_inventory = []

for route in app.routes:

    path_value = str(
        getattr(route, "path", "")
        or ""
    )

    methods = set(
        getattr(route, "methods", set())
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

    route_inventory.append(
        {
            "path": path_value,
            "methods": sorted(methods),
            "endpoint_module": endpoint_module,
            "endpoint_name": endpoint_name,
        }
    )


emit(
    "route_inventory",
    routes=route_inventory,
)


# ---------------------------------------------------------------
# Discover conversation POST route from the live FastAPI app.
# ---------------------------------------------------------------

candidates = []

for route in app.routes:

    path_value = str(
        getattr(route, "path", "")
        or ""
    )

    methods = set(
        getattr(route, "methods", set())
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
    ).casefold()

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
    ).casefold()

    path_lower = (
        path_value.casefold()
    )

    if "POST" not in methods:
        continue

    score = 0

    if "conversation" in path_lower:
        score += 100

    if "conversation" in endpoint_name:
        score += 60

    if "conversation" in endpoint_module:
        score += 40

    if "query" in endpoint_name:
        score += 10

    if score > 0:
        candidates.append(
            (
                score,
                path_value,
                endpoint_module,
                endpoint_name,
                route,
            )
        )


candidates.sort(
    key=lambda item: (
        -item[0],
        item[1],
        item[2],
        item[3],
    )
)


if candidates:

    best_score = (
        candidates[0][0]
    )

    strongest = [
        item
        for item in candidates
        if item[0] == best_score
    ]

    if len(strongest) == 1:

        (
            score,
            discovered_path,
            endpoint_module,
            endpoint_name,
            target_route,
        ) = strongest[0]

        emit(
            "route_discovered",
            path=discovered_path,
            score=score,
            endpoint_module=endpoint_module,
            endpoint_name=endpoint_name,
        )


if target_route is None:

    emit(
        "route_wrapper_error",
        detail=
            "conversation POST route not uniquely discovered",
        candidates=[
            {
                "score": item[0],
                "path": item[1],
                "module": item[2],
                "endpoint": item[3],
            }
            for item in candidates
        ],
    )

else:

    original_call = (
        target_route.dependant.call
    )


    if original_call is not None:

        if getattr(
            original_call,
            "__code__",
            None,
        ) is not None:

            is_async = (
                original_call.__code__.co_flags
                & 0x80
            )

        else:

            is_async = False


        if is_async:

            @functools.wraps(
                original_call
            )
            async def route_trace(
                *args,
                **kwargs,
            ):

                emit(
                    "route_enter",

                    function=
                        getattr(
                            original_call,
                            "__qualname__",
                            repr(
                                original_call
                            ),
                        ),
                )

                result = await original_call(
                    *args,
                    **kwargs,
                )

                summary = (
                    population_summary(
                        result
                    )
                )

                emit(

                    "route_return",

                    function=
                        getattr(
                            original_call,
                            "__qualname__",
                            repr(
                                original_call
                            ),
                        ),

                    return_type=
                        type_name(
                            result
                        ),

                    evidence=
                        summary[
                            "evidence"
                        ],

                    accepted=
                        summary[
                            "accepted"
                        ],

                    sources=
                        summary[
                            "sources"
                        ],

                    citations=
                        summary[
                            "citations"
                        ],

                    payload=
                        safe(
                            result
                        ),
                )

                return result


        else:

            @functools.wraps(
                original_call
            )
            def route_trace(
                *args,
                **kwargs,
            ):

                emit(
                    "route_enter",

                    function=
                        getattr(
                            original_call,
                            "__qualname__",
                            repr(
                                original_call
                            ),
                        ),
                )

                result = original_call(
                    *args,
                    **kwargs,
                )

                summary = (
                    population_summary(
                        result
                    )
                )

                emit(

                    "route_return",

                    function=
                        getattr(
                            original_call,
                            "__qualname__",
                            repr(
                                original_call
                            ),
                        ),

                    return_type=
                        type_name(
                            result
                        ),

                    evidence=
                        summary[
                            "evidence"
                        ],

                    accepted=
                        summary[
                            "accepted"
                        ],

                    sources=
                        summary[
                            "sources"
                        ],

                    citations=
                        summary[
                            "citations"
                        ],

                    payload=
                        safe(
                            result
                        ),
                )

                return result


        target_route.dependant.call = (
            route_trace
        )


        emit(

            "route_wrapped",

            path=
                str(
                    getattr(
                        target_route,
                        "path",
                        "",
                    )
                ),

            function=
                getattr(
                    original_call,
                    "__qualname__",
                    repr(
                        original_call
                    ),
                ),
        )


emit(
    "launcher_ready",
    route_found=
        target_route is not None,
)
