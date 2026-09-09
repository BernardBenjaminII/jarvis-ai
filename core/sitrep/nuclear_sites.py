"""Public-reference nuclear facility locations from OpenStreetMap Overpass."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_OVERPASS_URLS = (
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
)
QUERY = """[out:json][timeout:120];
nwr[\"power\"=\"plant\"][\"plant:source\"=\"nuclear\"];
out center tags;"""


class NuclearSiteProvider:
    provider_id = "openstreetmap_nuclear_sites"
    publisher = "OpenStreetMap contributors"

    def __init__(self, *, endpoint=None, timeout=60.0, opener=urlopen, clock=None):
        configured = endpoint or os.getenv("JARVIS_SITREP_OVERPASS_URL")
        self.endpoints = (configured,) if configured else DEFAULT_OVERPASS_URLS
        self.timeout = timeout
        self._opener = opener
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def collect(self):
        body = urlencode({"data": QUERY}).encode("utf-8")
        failures = []
        for endpoint in self.endpoints:
            request = Request(endpoint, data=body, headers={"User-Agent": "JARVIS-SITREP/5.1 (+local operational dashboard)", "Accept": "application/json"})
            try:
                with self._opener(request, timeout=self.timeout) as response:
                    payload = json.load(response)
                result = self.parse(payload)
                result["feed_url"] = endpoint
                return result
            except Exception as exc:
                failures.append(f"{endpoint}: {type(exc).__name__}: {exc}")
        raise RuntimeError("All Overpass endpoints failed: " + " | ".join(failures))

    def parse(self, payload):
        if not isinstance(payload, dict) or not isinstance(payload.get("elements"), list):
            raise ValueError("Overpass response did not contain elements")
        retrieved = self._clock().isoformat()
        sites = []
        seen = set()
        for element in payload["elements"]:
            tags = element.get("tags") or {}
            center = element.get("center") or element
            lat, lon = center.get("lat"), center.get("lon")
            if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
                continue
            name = tags.get("name") or tags.get("operator") or "Nuclear facility"
            identity = f"{element.get('type', 'object')}/{element.get('id')}"
            if identity in seen:
                continue
            seen.add(identity)
            sites.append({
                "id": f"osm-{identity.replace('/', '-')}", "kind": "nuclear_site",
                "name": name, "operator": tags.get("operator"),
                "facility_type": tags.get("power") or "facility",
                "location": {"latitude": float(lat), "longitude": float(lon)},
                "source": {"provider_id": self.provider_id, "publisher": self.publisher,
                           "authority": "public_reference", "retrieved_at": retrieved,
                           "url": f"https://www.openstreetmap.org/{identity}"},
            })
        if not sites:
            raise ValueError("OpenStreetMap returned no mapped nuclear facilities")
        return {"provider_id": self.provider_id, "publisher": self.publisher,
                "feed_url": self.endpoints[0], "retrieved_at": retrieved, "sites": sites}
