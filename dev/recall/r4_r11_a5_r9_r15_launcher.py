
from __future__ import annotations

import dataclasses
import functools
import importlib
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
    "r4_r11_a5_r9_r15_events.jsonl"
)

if str(PROJECT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT),
    )


def safe(value, depth=0):
    if depth > 6:
        return repr(value)

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    if dataclasses.is_dataclass(
        value
    ):
        try:
            return {
                f.name:
                    safe(
                        getattr(
                            value,
                            f.name,
                        ),
                        depth + 1,
                    )
                for f
                in dataclasses.fields(
                    value
                )
            }
        except Exception:
            pass

    if isinstance(value, dict):
        return {
            str(k):
                safe(
                    v,
                    depth + 1,
                )
            for k, v
            in list(
                value.items()
            )[:250]
        }

    if isinstance(
        value,
        (list, tuple, set),
    ):
        return [
            safe(
                v,
                depth + 1,
            )
            for v
            in list(value)[:250]
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
                str(k):
                    safe(
                        v,
                        depth + 1,
                    )
                for k, v
                in vars(value).items()
                if not str(k).startswith(
                    "_"
                )
            }
        except Exception:
            pass

    return repr(value)


def emit(kind, **payload):
    row = {
        "ts":
            time.time(),

        "kind":
            kind,

        **{
            key:
                safe(value)
            for key, value
            in payload.items()
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


integration = importlib.import_module(
    "core.conversation.grounded_answer.integration"
)


# ------------------------------------------------------------
# Grounded runtime request
# ------------------------------------------------------------

if hasattr(
    integration,
    "build_runtime_request",
):

    _original_build = (
        integration.build_runtime_request
    )

    @functools.wraps(
        _original_build
    )
    def build_runtime_request_trace(
        context,
        qualification,
        *args,
        **kwargs,
    ):

        emit(
            "runtime_request_enter",
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


# ------------------------------------------------------------
# Publish telemetry
# ------------------------------------------------------------

if hasattr(
    integration,
    "publish_grounded_answer_telemetry",
):

    _original_publish = (
        integration.publish_grounded_answer_telemetry
    )

    @functools.wraps(
        _original_publish
    )
    def publish_trace(
        *args,
        **kwargs,
    ):

        emit(
            "grounded_publish_enter",
            args=args,
            kwargs=kwargs,
        )

        result = _original_publish(
            *args,
            **kwargs,
        )

        emit(
            "grounded_publish_exit",
            result=result,
        )

        return result

    integration.publish_grounded_answer_telemetry = (
        publish_trace
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
