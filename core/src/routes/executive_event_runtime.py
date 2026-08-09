"""FastAPI projections for the constitutional Executive Event Runtime."""
from __future__ import annotations

from fastapi import APIRouter, Query, Request

from core.executive.events import ExecutiveEventRuntime

router = APIRouter(
    prefix="/operations/executive",
    tags=["executive-event-runtime"],
)


def get_event_runtime(request: Request) -> ExecutiveEventRuntime:
    runtime = getattr(
        request.app.state,
        "executive_event_runtime",
        None,
    )
    if not isinstance(runtime, ExecutiveEventRuntime):
        raise RuntimeError(
            "Executive Event Runtime is not installed."
        )
    return runtime


@router.get("/event-runtime")
def executive_event_runtime_status(
    request: Request,
) -> dict[str, object]:
    runtime = get_event_runtime(request)
    snapshot = runtime.snapshot()

    return {
        "ok": True,
        "resource": "executive_event_runtime",
        "data": {
            **snapshot.to_dict(),
            "integration_state": "configured",
            "configured": True,
        },
        "transport_version": "1.0.0",
    }
