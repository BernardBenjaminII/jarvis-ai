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


def global_security_providers():
    return (
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
