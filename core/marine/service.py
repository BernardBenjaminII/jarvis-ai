"""JARVIS marine environmental aggregation service."""

from datetime import datetime, timezone

from .noaa_coops import NOAA_COOPS_Provider


DEFAULT_PRODUCTS = [
    "water_level",
    "water_temperature",
    "wind",
    "air_pressure",
    "visibility",
]


class MarineService:
    def __init__(self, providers=None):
        self.providers = list(
            providers or [NOAA_COOPS_Provider()]
        )

    def snapshot(
        self,
        *,
        station=None,
        products=None,
    ):
        now = datetime.now(timezone.utc)

        if not station:
            return {
                "generated_at": (
                    now.isoformat().replace("+00:00", "Z")
                ),
                "operational_state": "READY",
                "observations": [],
                "sources": [],
                "errors": [],
                "message": (
                    "Marine subsystem online; provide "
                    "a station to request observations."
                ),
            }

        requested = products or DEFAULT_PRODUCTS

        observations = []
        sources = []
        errors = []

        for provider in self.providers:
            provider_rows = 0
            provider_errors = 0

            for product in requested:
                try:
                    rows = provider.observations(
                        station=station,
                        product=product,
                    )

                    observations.extend(
                        row.to_dict()
                        for row in rows
                    )

                    provider_rows += len(rows)

                except Exception as exc:
                    provider_errors += 1

                    errors.append({
                        "provider": provider.provider_id,
                        "product": product,
                        "error_type": type(exc).__name__,
                        "message": str(exc)[:300],
                    })

            sources.append({
                "provider": provider.provider_id,
                "observations": provider_rows,
                "errors": provider_errors,
            })

        if observations and not errors:
            state = "LIVE"
        elif observations:
            state = "DEGRADED"
        elif errors:
            state = "UNAVAILABLE"
        else:
            state = "EMPTY"

        return {
            "generated_at": (
                now.isoformat().replace("+00:00", "Z")
            ),
            "operational_state": state,
            "observations": observations,
            "sources": sources,
            "errors": errors,
        }
