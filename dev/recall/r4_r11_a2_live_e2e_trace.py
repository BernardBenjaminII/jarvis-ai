from __future__ import annotations

import inspect
import json
import os
import sqlite3
import sys
import threading
import time
from pathlib import Path
from typing import Any


PROJECT = Path(
    os.environ[
        "JARVIS_A2_PROJECT"
    ]
).resolve()

DB = Path(
    os.environ[
        "JARVIS_A2_DB"
    ]
).resolve()

EVENTS = Path(
    os.environ[
        "JARVIS_A2_EVENTS"
    ]
)

CALLS = Path(
    os.environ[
        "JARVIS_A2_CALLS"
    ]
)

CATALOG = Path(
    os.environ[
        "JARVIS_A2_CATALOG"
    ]
)


for path in (
    EVENTS,
    CALLS,
    CATALOG,
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


lock = threading.Lock()


def safe_json(value: Any) -> Any:

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

        if len(text) > 1000:
            text = text[:1000]

        return text

    if isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):
        return [
            safe_json(item)
            for item in value[:20]
        ]

    if isinstance(
        value,
        dict,
    ):
        result = {}

        for index, (
            key,
            item,
        ) in enumerate(
            value.items()
        ):
            if index >= 30:
                break

            result[
                str(key)
            ] = safe_json(
                item
            )

        return result

    try:
        text = repr(value)
    except Exception:
        text = (
            f"<{type(value).__name__}>"
        )

    if len(text) > 1000:
        text = text[:1000]

    return text


def event(
    kind: str,
    **payload: Any,
) -> None:

    record = {
        "time": time.time(),
        "kind": kind,
        **{
            key: safe_json(value)
            for key, value
            in payload.items()
        },
    }

    with lock:
        with EVENTS.open(
            "a",
            encoding="utf-8",
        ) as handle:
            handle.write(
                json.dumps(
                    record,
                    sort_keys=True,
                )
                + "\n"
            )


def append_tsv(
    path: Path,
    values: list[Any],
) -> None:

    with lock:
        with path.open(
            "a",
            encoding="utf-8",
        ) as handle:

            handle.write(
                "\t".join(
                    str(value)
                    .replace(
                        "\t",
                        " ",
                    )
                    .replace(
                        "\n",
                        " ",
                    )
                    for value in values
                )
                + "\n"
            )


CALLS.write_text(
    "event\tmodule\tfunction\tfile\tline\n",
    encoding="utf-8",
)

CATALOG.write_text(
    "event\tdatabase\tcaller_module\tcaller_function\tcaller_file\tcaller_line\n",
    encoding="utf-8",
)


#
# Python-call tracer.
#
# This intentionally records project calls whose names/modules
# indicate retrieval, knowledge, catalog, grounding, evidence,
# conversation, search, query, or executive behavior.
#

KEYWORDS = (
    "knowledge",
    "catalog",
    "retriev",
    "search",
    "ground",
    "evidence",
    "conversation",
    "executive",
    "qualified",
    "materializ",
    "answer",
    "query",
)


def relevant_frame(frame) -> bool:

    filename = str(
        frame.f_code.co_filename
    )

    if not filename.startswith(
        str(PROJECT)
    ):
        return False

    module = str(
        frame.f_globals.get(
            "__name__",
            "",
        )
    ).lower()

    function = str(
        frame.f_code.co_name
    ).lower()

    combined = (
        module
        + " "
        + function
        + " "
        + filename.lower()
    )

    return any(
        keyword in combined
        for keyword in KEYWORDS
    )


def profiler(
    frame,
    event_name,
    arg,
):

    if event_name not in (
        "call",
        "return",
    ):
        return

    if not relevant_frame(
        frame
    ):
        return

    module = frame.f_globals.get(
        "__name__",
        "",
    )

    function = (
        frame.f_code.co_name
    )

    filename = (
        frame.f_code.co_filename
    )

    line = (
        frame.f_lineno
    )

    append_tsv(
        CALLS,
        [
            event_name,
            module,
            function,
            filename,
            line,
        ],
    )

    event(
        "python_call",
        event=event_name,
        module=module,
        function=function,
        file=filename,
        line=line,
    )


sys.setprofile(
    profiler
)

threading.setprofile(
    profiler
)


#
# SQLite connection observation.
#
# Preserve original sqlite3.connect semantics.
#

_original_connect = (
    sqlite3.connect
)


def traced_connect(
    database,
    *args,
    **kwargs,
):

    database_text = str(
        database
    )

    frame = inspect.currentframe()

    caller = (
        frame.f_back
        if frame is not None
        else None
    )

    module = ""

    function = ""

    filename = ""

    line = ""

    if caller is not None:

        module = caller.f_globals.get(
            "__name__",
            "",
        )

        function = (
            caller.f_code.co_name
        )

        filename = (
            caller.f_code.co_filename
        )

        line = (
            caller.f_lineno
        )

    append_tsv(
        CATALOG,
        [
            "sqlite_connect",
            database_text,
            module,
            function,
            filename,
            line,
        ],
    )

    event(
        "sqlite_connect",
        database=database_text,
        expected_catalog=str(DB),
        catalog_match=(
            Path(database_text)
            .expanduser()
            .resolve()
            == DB
            if database_text
            not in (
                ":memory:",
                "",
            )
            else False
        ),
        caller_module=module,
        caller_function=function,
        caller_file=filename,
        caller_line=line,
    )

    return _original_connect(
        database,
        *args,
        **kwargs,
    )


sqlite3.connect = (
    traced_connect
)


event(
    "a2_trace_installed",
    project=str(PROJECT),
    database=str(DB),
    executable=sys.executable,
)


#
# Import application only AFTER instrumentation is installed.
#

from core.src.main import app


event(
    "jarvis_app_imported",
    app_type=type(app).__name__,
)


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8011,
        log_level="info",
    )
