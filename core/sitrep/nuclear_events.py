"""Official U.S. NRC event-notification provider.

The NRC page is an operational notice stream. Records retain the regulator's
wording and are never promoted to emergency warnings by JARVIS inference.
"""
from __future__ import annotations

import csv
import html
import io
import os
import re
from datetime import datetime, timezone
from urllib.request import Request, urlopen

DEFAULT_NRC_URL = "https://www.nrc.gov/sites/default/files/doc_library/reading-rm/doc-collections/event-status/event/event-notification-rpt-lastmonth.txt"


def _clean(value):
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(html.unescape(value).split())


class NrcEventProvider:
    provider_id = "us_nrc_event_notifications"
    publisher = "U.S. Nuclear Regulatory Commission"

    def __init__(self, *, url=None, timeout=30.0, opener=urlopen, clock=None):
        self.url = url or os.getenv("JARVIS_SITREP_NRC_EVENTS_URL", DEFAULT_NRC_URL)
        self.timeout = timeout
        self._opener = opener
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def collect(self):
        request = Request(self.url, headers={"User-Agent": "Mozilla/5.0 JARVIS-SITREP/5.1", "Accept": "text/plain,*/*;q=0.5", "Referer": "https://www.nrc.gov/reading-rm/doc-collections/event-status/event/index"})
        with self._opener(request, timeout=self.timeout) as response:
            text = response.read().decode(response.headers.get_content_charset() or "utf-8", "replace")
        return self.parse(text)

    def parse(self, text):
        retrieved = self._clock().isoformat()
        lines=(text or "").replace("\x00", "").splitlines()
        if not lines or "En No" not in lines[0]:
            raise ValueError("NRC raw report header was not recognized")
        header=next(csv.reader([lines[0]], delimiter="|")); width=len(header)
        logical=[]; current=""
        for line in lines[1:]:
            if line.count("|") >= width-2:
                if current: logical.append(current)
                current=line
            else:
                current += " " + line
        if current: logical.append(current)
        events = []
        for line in logical:
            values=next(csv.reader([line], delimiter="|"))
            values += [""] * max(0, width-len(values))
            row=dict(zip(header, values))
            event_id=row.get("En No", "").strip()
            if not event_id.isdigit(): continue
            title=(row.get("Site Name") or row.get("Licensee Name") or f"NRC Event {event_id}").strip()
            event_text=_clean(row.get("Event Text", ""))
            emergency=(row.get("Emergency Class") or "Not classified").strip()
            summary=f"{emergency}. {event_text}"[:700]
            events.append({
                "id": f"nrc-{event_id}", "kind": "nuclear_event",
                "classification": "REGULATOR NOTICE", "severity": "watch",
                "title": title, "region": (row.get("State Cd") or "United States").strip(),
                "summary": summary, "published_at": (row.get("Notification Dt") or row.get("Event Dt") or None),
                "operational_state": "LIVE",
                "source": {"provider_id": self.provider_id, "publisher": self.publisher,
                           "authority": "primary", "retrieved_at": retrieved,
                           "url": self.url, "event_number": event_id,
                           "emergency_class": emergency},
            })
        if not events:
            raise ValueError("NRC page contained no event notifications")
        return {"provider_id": self.provider_id, "publisher": self.publisher,
                "feed_url": self.url, "retrieved_at": retrieved, "events": events}
