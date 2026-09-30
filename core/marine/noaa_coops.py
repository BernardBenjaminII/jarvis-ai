"""NOAA CO-OPS marine observation provider."""

import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .contracts import MarineObservation
from .freshness import age_seconds, classify


DATA_API = (
    "https://api.tidesandcurrents.noaa.gov"
    "/api/prod/datagetter"
)

PRODUCTS = {
    "water_level": ("water_level", "m"),
    "water_temperature": ("water_temperature", "degC"),
    "wind": ("wind_speed", "m/s"),
    "air_pressure": ("air_pressure", "hPa"),
    "visibility": ("visibility", "km"),
}


def _parse_time(value):
    parsed = datetime.strptime(
        value.strip(),
        "%Y-%m-%d %H:%M",
    )
    return parsed.replace(tzinfo=timezone.utc)


class NOAA_COOPS_Provider:
    provider_id = "noaa_coops"

    def __init__(
        self,
        *,
        opener=urlopen,
        timeout=15.0,
        clock=None,
    ):
        self.opener = opener
        self.timeout = timeout
        self.clock = clock or (
            lambda: datetime.now(timezone.utc)
        )

    def _fetch_json(self, params):
        url = DATA_API + "?" + urlencode(params)

        request = Request(
            url,
            headers={
                "User-Agent": "JARVIS-Marine/1.0",
                "Accept": "application/json",
            },
        )

        with self.opener(
            request,
            timeout=self.timeout,
        ) as response:
            raw = response.read(2 * 1024 * 1024 + 1)

        if len(raw) > 2 * 1024 * 1024:
            raise ValueError(
                "NOAA CO-OPS response exceeds size limit"
            )

        payload = json.loads(raw.decode("utf-8"))

        if not isinstance(payload, dict):
            raise ValueError(
                "NOAA CO-OPS response is not an object"
            )

        if payload.get("error"):
            error = payload["error"]

            if isinstance(error, dict):
                message = error.get(
                    "message",
                    "NOAA CO-OPS error",
                )
            else:
                message = str(error)

            raise ValueError(message)

        return payload

    def observations(
        self,
        *,
        station,
        product,
    ):
        if product not in PRODUCTS:
            raise ValueError(
                f"unsupported CO-OPS product: {product}"
            )

        params = {
            "product": product,
            "application": "JARVIS",
            "station": station,
            "date": "latest",
            "time_zone": "gmt",
            "units": "metric",
            "format": "json",
        }

        # Water levels require a datum.
        if product == "water_level":
            params["datum"] = "MSL"

        payload = self._fetch_json(params)

        metadata = payload.get("metadata") or {}
        rows = payload.get("data") or []

        if not isinstance(rows, list):
            raise ValueError(
                "NOAA CO-OPS data is not a list"
            )

        try:
            lat = float(metadata["lat"])
            lon = float(metadata["lon"])
        except (KeyError, TypeError, ValueError):
            raise ValueError(
                "NOAA CO-OPS station metadata "
                "lacks valid coordinates"
            ) from None

        station_name = metadata.get("name")
        kind, unit = PRODUCTS[product]

        received = self.clock()
        results = []

        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue

            raw_value = row.get("v")
            raw_time = row.get("t")

            if raw_value in (None, "") or not raw_time:
                continue

            try:
                value = float(raw_value)
                observed = _parse_time(raw_time)
            except (TypeError, ValueError):
                continue

            age = age_seconds(
                observed,
                received,
            )

            results.append(
                MarineObservation(
                    observation_id=(
                        f"noaa-coops:{station}:"
                        f"{product}:"
                        f"{int(observed.timestamp())}:"
                        f"{index}"
                    ),
                    kind=kind,
                    value=value,
                    unit=unit,
                    latitude=lat,
                    longitude=lon,
                    observed_at=observed,
                    received_at=received,
                    provider=self.provider_id,
                    station_id=str(station),
                    station_name=station_name,
                    data_mode="OBSERVED",
                    freshness=classify(
                        kind,
                        age,
                    ),
                    age_seconds=age,
                    quality=row.get("q"),
                )
            )

        return results
