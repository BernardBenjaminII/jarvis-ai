"""Marine environmental API routes."""

from fastapi import APIRouter, Query

from core.marine.service import MarineService


router = APIRouter(
    prefix="/environment",
    tags=["marine-environment"],
)

service = MarineService()


@router.get("/marine")
def marine_snapshot(
    station: str | None = Query(
        default=None,
        min_length=1,
        max_length=32,
    ),
    product: list[str] | None = Query(default=None),
):
    return service.snapshot(
        station=station,
        products=product,
    )
