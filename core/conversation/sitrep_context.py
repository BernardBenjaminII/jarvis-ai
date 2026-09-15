"""Bounded, source-attributed SITREP answers. No model or network calls here.

Provider text is rendered as evidence, never evaluated as instructions. The
shared service starts any required refresh in the background.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from urllib.parse import urlsplit


def wants_sitrep(question):
    q = question.lower()
    if re.search(r"\b(?:code|implement|debug|install|python|javascript|pdf|catalog)\b", q):
        return False
    if re.match(r"\s*(?:what is|define|explain what) (?:a |the )?sitrep\b", q):
        return False
    if re.search(r"\bsitrep\b|\bsituation report\b", q):
        return True
    current = re.search(r"\b(?:latest|current|today|recent|now|updates?|brief|briefing)\b|what.s happening", q)
    subject = re.search(r"\b(?:security|cybersecurity|cyber|conflicts?|hotspots?|advisories|alerts|nuclear|threats?)\b|hot spots", q)
    return bool(current and subject)


def clean(value, limit=900):
    text = re.sub(r"<[^>]*>", " ", str(value or ""))
    return " ".join(text.split())[:limit]


def parsed_date(value):
    if not value:
        return None
    text = str(value).strip()
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        dt = None
        for fmt in ("%m/%d/%Y", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M"):
            try:
                dt = datetime.strptime(text, fmt)
                break
            except ValueError:
                pass
        if dt is None:
            return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def safe_url(value):
    text = str(value or "")
    try:
        parts = urlsplit(text)
        if parts.scheme in ("http", "https") and parts.netloc and not re.search(r"[\s<>]", text):
            return text
    except ValueError:
        pass
    return ""


STOP = set("""a an the and or to of in on at for from with about me my you your jarvis
    please can could would will do does did is are was were has have it its that this
    what which who where how show tell give get refer use using based according
    sitrep situation report reports latest current currently today recent recently
    now brief briefing summarize summarise summary update updates developments
    happening happening security news alert alerts advisory advisories threat threats
    cyber cybersecurity physical nuclear incident incidents event events conflict
    conflicts hot spot spots hotspot hotspots global world worldwide international
    data information say says notices notice notifications notification warnings warning see check list need needs attention important most top priority
    any there available feed feeds sources source last past hours hour days day
    refreshing refresh fetch""".split())


def answer_snapshot(question, snapshot, *, now=None, limit=6, freshness_seconds=900):
    now = now or datetime.now(timezone.utc)
    q = re.sub(r"['’]s\b", "", question.lower())
    limit = max(1, min(int(limit), 10))
    categories = set()
    if re.search(r"\b(?:cyber|cybersecurity|cve|vulnerabilit\w*|ransomware)\b", q):
        categories.add("cyber")
    if re.search(r"\b(?:physical|conflicts?|hotspots?)\b|hot spots", q):
        categories.add("physical")
    nuclear = bool(re.search(r"\bnuclear\b", q))
    sites = nuclear and bool(re.search(r"\b(?:sites?|facilities|plants?|reactors?)\b", q))
    travel = bool(re.search(r"\btravel\b", q))
    excluded = STOP | {"travel", "sites", "site", "facilities", "plants", "plant", "reactors", "reactor"}
    terms = [t for t in re.findall(r"[\w]+(?:-[\w]+)*", q) if t not in excluded and not t.isdigit()]
    # Match the requested subject; never substitute unrelated global headlines.
    aliases = {"usa": "united states", "uk": "united kingdom"}
    terms = [aliases.get(t, t) for t in terms]
    cutoff = None
    period = re.search(r"\b(?:last|past)\s+(\d+)\s+(hours?|days?)\b", q)
    if period:
        amount = min(int(period.group(1)), 36500)
        cutoff = now - (timedelta(hours=amount) if period.group(2).startswith("hour") else timedelta(days=amount))
    elif re.search(r"\btoday\b", q):
        cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)

    source_map = {s.get("provider_id"): s for s in snapshot.get("sources", [])}
    candidates = []
    keys = ("nuclear_sites",) if sites else ("nuclear_events",) if nuclear else ("incidents",) if travel else ("security_events",) if categories else ("security_events", "incidents", "nuclear_events")
    if nuclear and categories:
        keys = ("security_events", "nuclear_events")
    for key in keys:
        for row in snapshot.get(key, []):
            if row.get("fixture") or row.get("is_fixture") or str(row.get("operational_state", "")).upper() in ("DEMO", "FIXTURE", "UNAVAILABLE", "PENDING"):
                continue
            if categories and key == "security_events" and row.get("category") not in categories:
                continue
            source = row.get("source") or {}
            searchable = " ".join(clean(row.get(k), 2000) for k in ("title", "name", "summary", "region", "country_code", "operator")) + " " + clean(source.get("publisher"))
            if not all(re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", searchable, re.I) for t in terms):
                continue
            published = parsed_date(row.get("published_at"))
            if cutoff is not None and (published is None or published < cutoff or published > now):
                continue
            if published is not None and published > now:
                continue
            candidates.append((row, key, published))
    priority = {"critical": 4, "high": 3, "elevated": 2, "moderate": 2, "watch": 1, "low": 0}
    urgent = bool(re.search(r"\b(?:priority|important|attention|urgent|critical)\b", q))
    def sort_key(item):
        row, key, dt = item
        date_value = dt.timestamp() if dt else float("-inf")
        severity = priority.get(str(row.get("severity", "")).lower(), 0)
        return (severity, date_value) if urgent else (date_value, severity)
    candidates.sort(key=sort_key, reverse=True)
    unique = []
    seen = set()
    for item in candidates:
        row = item[0]
        identity = row.get("id") or (row.get("title"), (row.get("source") or {}).get("url"))
        if identity not in seen:
            unique.append(item)
            seen.add(identity)
    selected = unique[:limit]
    state = clean(snapshot.get("operational_state", "UNAVAILABLE"), 40)
    lines = [f"SITREP briefing — snapshot status: {state}."]
    if snapshot.get("refreshing"):
        lines.append("A source refresh is running in the background. This answer uses the latest available cached reports; ask again when the refresh finishes.")
    degraded = [s for s in snapshot.get("sources", []) if s.get("state") != "LIVE"]
    if degraded:
        lines.append("Feed status: " + "; ".join(clean(s.get("publisher") or s.get("provider_id"), 80) + " — " + clean(s.get("state", "UNKNOWN"), 30) for s in degraded[:12]) + ".")
    if cutoff is not None:
        lines.append(f"Publication window: {cutoff.isoformat()} through {now.isoformat()} (UTC); undated reports excluded.")
    if terms:
        lines.append("Subject filter: " + ", ".join(terms) + ".")
    if not selected:
        lines.append("No matching reports are available in this SITREP snapshot. This does not establish that no incidents or threats exist.")
    else:
        lines.append(f"Showing {len(selected)} of {len(unique)} matching records, ordered by " + ("source priority, then publication date." if urgent else "publication date, newest first; undated records last."))
    evidence = []
    for index, (row, key, published) in enumerate(selected, 1):
        source = row.get("source") or {}
        provider = source_map.get(source.get("provider_id"), {})
        retrieved_raw = source.get("retrieved_at") or provider.get("retrieved_at")
        retrieved = parsed_date(retrieved_raw)
        status = str(row.get("operational_state") or provider.get("state") or "UNKNOWN").upper()
        if provider.get("state") in ("STALE", "REFRESHING", "UNAVAILABLE"):
            status = provider["state"]
        if retrieved is None or retrieved > now:
            freshness = "retrieval time unknown or invalid"
        elif (now - retrieved).total_seconds() > freshness_seconds:
            freshness = "cached beyond the refresh interval; freshness unconfirmed"
        else:
            freshness = "retrieved within the refresh interval"
        citation = f"S{index}"
        title = clean(row.get("title") or row.get("name") or "Untitled report", 300)
        summary = clean(row.get("summary"), 700)
        publisher = clean(source.get("publisher") or provider.get("publisher") or "Unknown source", 120)
        url = safe_url(source.get("url"))
        label = "Facility reference — not an incident" if key == "nuclear_sites" else clean(row.get("classification") or row.get("kind") or key, 80)
        lines.extend(["", f"[{citation}] {title}", f"{label} | source priority: {clean(row.get('severity') or 'not assigned', 30)} | {status}"])
        if summary:
            lines.append("Source summary: " + summary)
        lines.append(f"Published: {clean(row.get('published_at') or 'not supplied', 60)}. Retrieved: {clean(retrieved_raw or 'unknown', 60)} — {freshness}.")
        lines.append(f"Source: {publisher}" + (f" — {url}" if url else " — link unavailable"))
        evidence.append(dict(citation=citation, id=row.get("id"), title=title, summary=summary, publisher=publisher, url=url, published_at=row.get("published_at"), retrieved_at=retrieved_raw, operational_state=status, freshness=freshness))
    lines.extend(["", "Coverage is limited to the configured SITREP feeds. These are source reports and advisory records, not independent confirmation or a complete threat assessment."])
    return "\n".join(lines), dict(adapter="sitrep_snapshot", sitrep=dict(snapshot_state=state, generated_at=snapshot.get("generated_at"), refreshing=bool(snapshot.get("refreshing")), matched_records=len(unique), evidence=evidence, filter_terms=terms))


def answer_sitrep(question):
    try:
        from core.sitrep import get_sitrep_service
        service = get_sitrep_service()
        refresh = bool(re.search(r"\brefresh\b", question, re.I))
        snapshot = service.snapshot_background(force_refresh=refresh)
        return answer_snapshot(question, snapshot, freshness_seconds=service._cache_ttl_seconds)
    except Exception as exc:
        return ("SITREP data is currently unavailable. I cannot verify the latest security situation from its feeds. Try again after checking SITREP source status.",
                {"adapter": "sitrep_snapshot", "sitrep": {"snapshot_state": "UNAVAILABLE", "error_type": type(exc).__name__, "evidence": []}})
