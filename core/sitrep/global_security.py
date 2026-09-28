"""
JARVIS SITREP R8.1 — Global Security Acquisition

Official public-source collectors for:
    - AFRICOM operational releases
    - EASA Conflict Zone Information Bulletins
    - GDACS global disaster alerts

Classification is an automated TRIAGE HINT.
It is not independent verification or an intelligence judgment.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
from html import unescape
import json
import math
import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen


MAX_BYTES = 8 * 1024 * 1024

AFRICOM_RSS = (
    "https://www.africom.mil/"
    "syndication-feed/rss/press-releases"
)

EASA_CZIB_RSS = (
    "https://www.easa.europa.eu/"
    "en/domains/air-operations/czibs/feed.xml"
)

GDACS_24H_RSS = "https://gdacs.org/xml/rss_24h.xml"
GDACS_7D_RSS = "https://gdacs.org/xml/rss_7d.xml"

UKMTO_INCIDENTS_JSON = (
    "https://sccd.royalnavy.mod.uk/api/ukmto/all"
)

MSCIO_ALERTS_JSON = (
    "https://www.mscio.eu/alerts/filter"
)

MARITIME_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


MILITARY_TERMS = re.compile(
    r"\b("
    r"airstrike|airstrikes|strike|strikes|attack|attacks|"
    r"operation|operations|combat|hostilities|military|"
    r"missile|missiles|drone|drones|weapon|weapons|"
    r"terrorist|terrorism|isis|isil|al[\s-]?shabaab|"
    r"armed|forces|deployment|deploy|exercise|"
    r"intercept|intercepts|destroyed|destroys|"
    r"target|targeting|security|conflict|"
    r"evacuation|blockade|warship|naval|"
    r"mine|mines|artillery"
    r")\b",
    re.I,
)


AVIATION_TERMS = re.compile(
    r"\b("
    r"airspace|conflict|zone|czib|risk|"
    r"missile|drone|military|hostilities|"
    r"flight|aviation|fir|operator"
    r")\b",
    re.I,
)


DISASTER_TERMS = re.compile(
    r"\b("
    r"earthquake|flood|flooding|cyclone|hurricane|"
    r"typhoon|volcano|volcanic|eruption|tsunami|"
    r"wildfire|fire|drought|landslide|storm|"
    r"tropical|disaster|alert"
    r")\b",
    re.I,
)


CRITICAL_TERMS = re.compile(
    r"\b("
    r"major attack|mass casualty|catastrophic|"
    r"emergency evacuation|declared emergency|"
    r"nuclear attack|ballistic missile attack|"
    r"large-scale attack"
    r")\b",
    re.I,
)


HIGH_TERMS = re.compile(
    r"\b("
    r"airstrike|airstrikes|missile|missiles|"
    r"drone attack|armed attack|strike targeting|"
    r"strikes targeting|hostilities|blockade|"
    r"warship|terrorist attack|combat operation|"
    r"red alert"
    r")\b",
    re.I,
)


MEDIUM_TERMS = re.compile(
    r"\b("
    r"military exercise|deployment|deploy|"
    r"conflict zone|airspace|security warning|"
    r"intercept|unrest|orange alert"
    r")\b",
    re.I,
)


def clean(value):
    return " ".join(
        unescape(
            re.sub(
                r"<[^>]*>",
                " ",
                str(value or ""),
            )
        ).split()
    )


def parse_date(value):
    if not value:
        return None

    text = str(value).strip()

    try:
        result = datetime.fromisoformat(
            text.replace("Z", "+00:00")
        )
    except (ValueError, TypeError):
        try:
            result = parsedate_to_datetime(text)
        except (
            ValueError,
            TypeError,
            OverflowError,
        ):
            return None

    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)

    return result.astimezone(timezone.utc)


def canonical_url(value, base_url):
    try:
        absolute = urljoin(base_url, str(value or ""))
        parsed = urlsplit(absolute)

        if parsed.scheme not in ("https",):
            return None

        if (
            not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            return None

        return urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.query,
                "",
            )
        )
    except ValueError:
        return None


def triage(title, summary, default="watch"):
    """
    Automated display priority only.

    This does NOT claim independent verification,
    strategic importance, attribution, or operational impact.
    """

    text = f"{title} {summary}"

    if CRITICAL_TERMS.search(text):
        return (
            "critical",
            "Automated triage: critical-event terminology",
        )

    if HIGH_TERMS.search(text):
        return (
            "high",
            "Automated triage: active attack / strike terminology",
        )

    if MEDIUM_TERMS.search(text):
        return (
            "medium",
            "Automated triage: elevated security-risk terminology",
        )

    return (
        default,
        "Automated triage: monitored security development",
    )


class OfficialSecurityFeed:
    """
    Generic bounded RSS/Atom collector.

    Unlike the older generic SecurityFeed, article links may
    resolve to a different HTTPS hostname. This is necessary
    for official publishers whose feed and article delivery
    use different subdomains.

    The feed endpoint itself remains fixed and controlled.
    """

    def __init__(
        self,
        provider_id,
        publisher,
        url,
        category,
        terms,
        *,
        default_priority="watch",
        max_age_days=30,
        opener=urlopen,
        clock=None,
        request_headers=None,
    ):
        self.provider_id = provider_id
        self.publisher = publisher
        self.url = url
        self.category = category
        self.terms = terms
        self.default_priority = default_priority
        self.max_age_days = max_age_days
        self._opener = opener
        self.request_headers = dict(request_headers or {})
        self._clock = clock or (
            lambda: datetime.now(timezone.utc)
        )

    def collect(self):
        headers = {
            "User-Agent": "JARVIS-SITREP/8.1",
            "Accept": (
                "application/rss+xml,"
                "application/atom+xml,"
                "application/xml,"
                "text/xml,"
                "*/*;q=0.2"
            ),
        }
        headers.update(self.request_headers)

        request = Request(
            self.url,
            headers=headers,
        )

        with self._opener(
            request,
            timeout=15,
        ) as response:
            raw = response.read(MAX_BYTES + 1)

        if len(raw) > MAX_BYTES:
            raise ValueError(
                "Security feed exceeds size limit"
            )

        return self.parse(raw)

    def _entry_text(self, entry, *names):
        for name in names:
            for child in entry:
                if child.tag.split("}")[-1] == name:
                    text = "".join(child.itertext())
                    if text:
                        return text

        return ""

    def _entry_link(self, entry):
        for child in entry:
            if child.tag.split("}")[-1] != "link":
                continue

            href = child.get("href")

            if href:
                return href

            if child.text:
                return child.text

        return ""

    def _point(self, entry):
        for child in entry.iter():
            if child.tag.split("}")[-1] != "point":
                continue

            try:
                lat, lon = map(
                    float,
                    (child.text or "").split(),
                )

                if (
                    math.isfinite(lat)
                    and math.isfinite(lon)
                    and -90 <= lat <= 90
                    and -180 <= lon <= 180
                ):
                    return {
                        "latitude": lat,
                        "longitude": lon,
                    }

            except (ValueError, TypeError):
                pass

        return None

    def parse(self, raw):
        if re.search(
            br"<!\s*(DOCTYPE|ENTITY)",
            raw,
            re.I,
        ):
            raise ValueError(
                "XML declarations not allowed"
            )

        root = ET.fromstring(raw)

        root_name = root.tag.split("}")[-1].lower()

        if root_name not in (
            "rss",
            "feed",
            "rdf",
        ):
            raise ValueError(
                f"Unsupported feed root: {root_name}"
            )

        entries = []

        for element in root.iter():
            if element.tag.split("}")[-1] in (
                "item",
                "entry",
            ):
                entries.append(element)

        if not entries:
            raise ValueError(
                "Feed has no recognizable entries"
            )

        now = self._clock()
        items = []

        for entry in entries[:300]:
            title = clean(
                self._entry_text(
                    entry,
                    "title",
                )
            )

            summary = clean(
                self._entry_text(
                    entry,
                    "description",
                    "summary",
                    "content",
                )
            )

            raw_url = self._entry_link(entry)

            url = canonical_url(
                raw_url,
                self.url,
            )

            published = parse_date(
                self._entry_text(
                    entry,
                    "pubDate",
                    "published",
                    "updated",
                    "date",
                )
            )

            if not title or not url or not published:
                continue

            # Current operational window.
            if not (
                now - timedelta(days=self.max_age_days)
                <= published
                <= now + timedelta(days=1)
            ):
                continue

            text = f"{title} {summary}"

            if (
                self.terms is not None
                and not self.terms.search(text)
            ):
                continue

            priority, reason = triage(
                title,
                summary,
                self.default_priority,
            )

            location = self._point(entry)

            identity = sha256(
                (
                    self.provider_id
                    + "|"
                    + url
                    + "|"
                    + title
                ).encode("utf-8")
            ).hexdigest()[:20]

            items.append(
                {
                    "id": (
                        f"{self.provider_id}-"
                        f"{identity}"
                    ),
                    "kind": "security_event",
                    "category": self.category,
                    "title": title[:300],
                    "summary": summary[:900],
                    "published_at": (
                        published.isoformat()
                    ),
                    "severity": priority,
                    "priority_reason": reason,
                    "location": location,
                    "region": (
                        "Source coordinates"
                        if location
                        else (
                            "Location unspecified / "
                            "multi-region"
                        )
                    ),
                    "operational_state": "LIVE",
                    "classification": (
                        "SECURITY REPORT"
                    ),
                    "verification": (
                        "Publisher report; not "
                        "independently verified by JARVIS"
                    ),
                    "source": {
                        "provider_id": self.provider_id,
                        "publisher": self.publisher,
                        "authority": "primary",
                        "retrieved_at": now.isoformat(),
                        "url": url,
                        "feed_url": self.url,
                    },
                }
            )

        return {
            "provider_id": self.provider_id,
            "publisher": self.publisher,
            "feed_url": self.url,
            "retrieved_at": now.isoformat(),
            "security_events": items,
        }


class MaritimeJSONFeed:
    """
    Generic bounded JSON maritime collector.

    Source-specific subclasses normalize publisher-native JSON into
    the existing JARVIS security_event contract. Acquisition keeps
    publisher reports independent so downstream fusion can correlate
    corroborating reports rather than losing them at ingestion.
    """

    def __init__(
        self,
        provider_id,
        publisher,
        url,
        *,
        max_age_days=365,
        opener=urlopen,
        clock=None,
        request_headers=None,
    ):
        self.provider_id = provider_id
        self.publisher = publisher
        self.url = url
        self.max_age_days = max_age_days
        self._opener = opener
        self._clock = clock or (
            lambda: datetime.now(timezone.utc)
        )
        self.request_headers = dict(request_headers or {})

    def collect(self):
        headers = dict(MARITIME_BROWSER_HEADERS)
        headers.update(self.request_headers)

        request = Request(
            self.url,
            headers=headers,
        )

        with self._opener(
            request,
            timeout=15,
        ) as response:
            raw = response.read(MAX_BYTES + 1)

        if len(raw) > MAX_BYTES:
            raise ValueError(
                "Maritime JSON feed exceeds size limit"
            )

        return self.parse(raw)

    def _load_json(self, raw):
        try:
            return json.loads(
                raw.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise ValueError(
                "Invalid maritime JSON payload"
            ) from exc

    def _valid_time(self, published, now):
        return (
            published is not None
            and (
                now - timedelta(days=self.max_age_days)
                <= published
                <= now + timedelta(days=1)
            )
        )

    @staticmethod
    def _location(latitude, longitude):
        try:
            lat = float(latitude)
            lon = float(longitude)
        except (TypeError, ValueError):
            return None

        if not (
            math.isfinite(lat)
            and math.isfinite(lon)
            and -90 <= lat <= 90
            and -180 <= lon <= 180
        ):
            return None

        return {
            "latitude": lat,
            "longitude": lon,
        }

    def _event(
        self,
        *,
        native_id,
        title,
        summary,
        published,
        location,
        region,
        native_type,
        native_level=None,
        metadata=None,
        source_url=None,
        default_priority="watch",
    ):
        priority, reason = triage(
            title,
            summary,
            default_priority,
        )

        identity = sha256(
            (
                self.provider_id
                + "|"
                + str(native_id)
            ).encode("utf-8")
        ).hexdigest()[:20]

        source = {
            "provider_id": self.provider_id,
            "publisher": self.publisher,
            "authority": "primary",
            "retrieved_at": self._clock().isoformat(),
            # Event URL and acquisition feed URL are distinct.
            # A shared collection/feed URL must never masquerade as
            # event identity or group_reports() may false-merge every
            # record from that feed.
            "url": source_url,
            "feed_url": self.url,
        }

        event = {
            "id": f"{self.provider_id}-{identity}",
            "kind": "security_event",
            "category": "maritime",
            "title": clean(title)[:300],
            "summary": clean(summary)[:900],
            "published_at": published.isoformat(),
            "severity": priority,
            "priority_reason": reason,
            "location": location,
            "region": (
                clean(region)
                if region
                else (
                    "Source coordinates"
                    if location
                    else "Location unspecified / multi-region"
                )
            ),
            "operational_state": "LIVE",
            "classification": "MARITIME SECURITY REPORT",
            "verification": (
                "Publisher report; not independently verified by JARVIS"
            ),
            "source": source,
            "native_type": clean(native_type),
        }

        if native_level is not None:
            event["native_level"] = native_level

        if metadata:
            event["maritime"] = metadata

        return event


class UKMTOMaritimeProvider(MaritimeJSONFeed):
    def __init__(
        self,
        *,
        opener=urlopen,
        clock=None,
    ):
        super().__init__(
            "ukmto_incidents",
            "United Kingdom Maritime Trade Operations",
            UKMTO_INCIDENTS_JSON,
            max_age_days=365,
            opener=opener,
            clock=clock,
            request_headers={
                "Referer": (
                    "https://www.ukmto.org/recent-incidents"
                ),
            },
        )

    def parse(self, raw):
        payload = self._load_json(raw)

        if not isinstance(payload, list):
            raise ValueError(
                "UKMTO payload root must be a list"
            )

        now = self._clock()
        items = []

        for record in payload[:500]:
            if not isinstance(record, dict):
                continue

            native_id = (
                record.get("sitecoreId")
                or record.get("incidentNumber")
            )
            published = parse_date(
                record.get("utcDateOfIncident")
            )
            native_type = clean(
                record.get("incidentTypeName")
            )
            summary = clean(
                record.get("otherDetails")
            )

            if (
                not native_id
                or not published
                or not native_type
                or not self._valid_time(
                    published,
                    now,
                )
            ):
                continue

            incident_number = record.get(
                "incidentNumber"
            )
            place = clean(record.get("place"))
            vessel_name = clean(
                record.get("vesselName")
            )
            vessel_type = clean(
                record.get("vesselType")
            )

            title_parts = ["UKMTO"]

            if incident_number is not None:
                title_parts.append(
                    f"Incident {incident_number}"
                )

            title_parts.append(native_type)

            if place:
                title_parts.append(place)

            title = " — ".join(title_parts)

            location = self._location(
                record.get("locationLatitude"),
                record.get("locationLongitude"),
            )

            metadata = {
                "incident_number": incident_number,
                "sitecore_id": record.get(
                    "sitecoreId"
                ),
                "incident_issuer": clean(
                    record.get("incidentIssuer")
                ),
                "place": place or None,
                "source_region": clean(
                    record.get("region")
                ) or None,
                "vessel_name": (
                    vessel_name
                    if vessel_name not in ("", "..")
                    else None
                ),
                "vessel_type": vessel_type or None,
                "vessel_under_pirate_control": bool(
                    record.get(
                        "vesselUnderPirateControl"
                    )
                ),
                "crew_held": record.get(
                    "crewHeld"
                ),
                "date_vessel_taken": record.get(
                    "dateVesselTaken"
                ),
                "pin_colour": clean(
                    record.get("pinColour")
                ) or None,
            }

            # Preserve UKMTO's native level separately.
            # It is publisher metadata, not a JARVIS severity.
            native_level = record.get(
                "incidentTypeLevel"
            )

            items.append(
                self._event(
                    native_id=native_id,
                    title=title,
                    summary=summary,
                    published=published,
                    location=location,
                    region=place,
                    native_type=native_type,
                    native_level=native_level,
                    metadata=metadata,
                    # The UKMTO collection page is shared by every
                    # incident. Do not use it as event identity because
                    # group_reports() treats identical source URLs as
                    # duplicate reports. Provenance remains available
                    # through source.feed_url.
                    source_url=None,
                    default_priority="watch",
                )
            )

        return {
            "provider_id": self.provider_id,
            "publisher": self.publisher,
            "feed_url": self.url,
            "retrieved_at": now.isoformat(),
            "security_events": items,
        }


class MSCIOMaritimeProvider(MaritimeJSONFeed):
    def __init__(
        self,
        *,
        opener=urlopen,
        clock=None,
    ):
        super().__init__(
            "mscio_alerts",
            "Maritime Security Centre Indian Ocean",
            MSCIO_ALERTS_JSON,
            max_age_days=365,
            opener=opener,
            clock=clock,
            request_headers={
                "Referer": (
                    "https://www.mscio.eu/alerts/"
                ),
            },
        )

    def parse(self, raw):
        payload = self._load_json(raw)

        if not isinstance(payload, dict):
            raise ValueError(
                "MSCIO payload root must be an object"
            )

        records = payload.get("data")

        if not isinstance(records, list):
            raise ValueError(
                "MSCIO payload data must be a list"
            )

        now = self._clock()
        items = []

        for record in records[:500]:
            if not isinstance(record, dict):
                continue

            native_id = record.get("AlertId")
            published = parse_date(
                record.get("RegistrationDate")
            )
            native_type = clean(
                record.get("AlertTypeType")
            )
            summary = clean(
                record.get("ThreatDescription")
            )

            if (
                native_id is None
                or not published
                or not native_type
                or not self._valid_time(
                    published,
                    now,
                )
            ):
                continue

            location = self._location(
                record.get("Latitude"),
                record.get("Longitude"),
            )

            title = (
                f"MSCIO Alert {native_id}"
                f" — {native_type}"
            )

            metadata = {
                "alert_id": native_id,
                "alert_type_code": clean(
                    record.get("AlertType")
                ) or None,
            }

            items.append(
                self._event(
                    native_id=native_id,
                    title=title,
                    summary=summary,
                    published=published,
                    location=location,
                    region=None,
                    native_type=native_type,
                    metadata=metadata,
                    source_url=(
                        "https://www.mscio.eu/"
                        f"alerts/{native_id}"
                    ),
                    default_priority="watch",
                )
            )

        return {
            "provider_id": self.provider_id,
            "publisher": self.publisher,
            "feed_url": self.url,
            "retrieved_at": now.isoformat(),
            "security_events": items,
        }


def global_security_providers():
    return (
        UKMTOMaritimeProvider(),
        MSCIOMaritimeProvider(),

        OfficialSecurityFeed(
            "us_africom_press",
            "U.S. Africa Command",
            AFRICOM_RSS,
            "physical",
            MILITARY_TERMS,
            default_priority="watch",
            request_headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/153.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "application/rss+xml,"
                    "application/xml;q=0.9,"
                    "*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
        ),

        OfficialSecurityFeed(
            "easa_conflict_zones",
            "European Union Aviation Safety Agency",
            EASA_CZIB_RSS,
            "aviation",
            AVIATION_TERMS,
            default_priority="medium",
            max_age_days=365,
        ),

        OfficialSecurityFeed(
            "gdacs_7d",
            "Global Disaster Alert and Coordination System",
            GDACS_7D_RSS,
            "disaster",
            DISASTER_TERMS,
            default_priority="watch",
        ),
    )
