from __future__ import annotations
from typing import Any

def _walk(v: Any):
    if isinstance(v, dict):
        keys=set(v)
        if keys & {"status_code","status-code","title","url","location","tech","technologies","webserver","content_type","content-type","scheme","host","cdn_name","cname"}:
            yield v
        for x in v.values():
            yield from _walk(x)
    elif isinstance(v, list):
        for x in v:
            yield from _walk(x)

def _status(r):
    for k in ("status_code","status-code","status"):
        v=r.get(k)
        if isinstance(v,int): return v
        if isinstance(v,str) and v.isdigit(): return int(v)
    return None

def _strings(v):
    if isinstance(v,str):
        yield v
    elif isinstance(v,list):
        for x in v: yield from _strings(x)
    elif isinstance(v,dict):
        for x in v.values(): yield from _strings(x)

def _target_from_evidence(evidence: Any) -> str:
    if not isinstance(evidence, dict):
        return ""
    for path in (
        ("target",),
        ("result","target"),
        ("evidence","target"),
    ):
        cur=evidence
        ok=True
        for key in path:
            if not isinstance(cur,dict) or key not in cur:
                ok=False; break
            cur=cur[key]
        if ok and isinstance(cur,str) and cur.strip():
            return cur.strip()
    return ""

def analyze_http_evidence(target: str, evidence: Any) -> dict:
    records=list(_walk(evidence))
    statuses=[]; redirects=[]; tech=set(); titles=set(); servers=set(); cts=set()
    for r in records:
        s=_status(r)
        if s is not None: statuses.append(s)
        loc=r.get("location")
        if isinstance(loc,str) and loc.strip(): redirects.append(loc.strip())
        title=r.get("title")
        if isinstance(title,str) and title.strip(): titles.add(title.strip())
        for k in ("tech","technologies"):
            for x in _strings(r.get(k)):
                if x.strip(): tech.add(x.strip())
        for k in ("webserver","server"):
            x=r.get(k)
            if isinstance(x,str) and x.strip(): servers.add(x.strip())
        for k in ("content_type","content-type"):
            x=r.get(k)
            if isinstance(x,str) and x.strip(): cts.add(x.strip())

    if not target:
        target=_target_from_evidence(evidence)

    score=0; reasons=[]; t=str(target or "").lower()

    if ".staging." in t or t.startswith("staging."):
        score+=8; reasons.append("Authorized non-production staging surface")

    if not records:
        reasons.append("No structured HTTP response record collected")
    else:
        score+=8; reasons.append("Structured HTTP response evidence collected")

    us=sorted(set(statuses))

    if any(200 <= s < 300 for s in us):
        score+=20; reasons.append("Reachable application surface returned 2xx")
    if any(300 <= s < 400 for s in us):
        score+=10; reasons.append("Redirecting HTTP surface identified")
    if any(s in (401,403) for s in us):
        score+=8; reasons.append("Access-controlled endpoint returned 401/403")
    if any(s in (400,404,405) for s in us):
        score+=4; reasons.append("Application endpoint responded with client-error semantics")

    surf=" ".join([t]+[x.lower() for x in redirects]+[x.lower() for x in titles]+[x.lower() for x in cts])
    if any(tok in surf for tok in ("/api","api.","graphql","mcp")):
        score+=14; reasons.append("API-like application surface identified")

    if tech:
        score+=min(10,2+len(tech)); reasons.append("Technology fingerprint available")

    if servers:
        score+=2; reasons.append("HTTP server fingerprint available")

    score=max(0,min(100,score))

    if score>=65:
        priority="high"
        rec="Strong recon lead. Review evidence and approve only a bounded, target-specific investigation if relevant."
    elif score>=40:
        priority="medium"
        rec="Moderate recon lead. Review application behavior and decide whether a narrow investigation is justified."
    elif score>=20:
        priority="low"
        rec="Low-priority recon lead; retain as supporting surface data."
    else:
        priority="informational"
        rec="Insufficient live HTTP evidence for deeper investigation."

    return {
        "target": target,
        "score": score,
        "priority": priority,
        "risk": "yellow",
        "reasons": reasons,
        "recommendation": rec,
        "suggested_actions": [
            "Review the collected HTTP evidence",
            "Map the application/API surface without expanding scope",
            "Decide whether deeper investigation is warranted",
        ],
        "evidence_summary": {
            "record_count": len(records),
            "status_codes": us,
            "redirects": sorted(set(redirects)),
            "technologies": sorted(tech),
            "titles": sorted(titles),
            "servers": sorted(servers),
            "content_types": sorted(cts),
        },
        "score_type": "recon_opportunity_not_vulnerability_evidence",
    }

def analyze_http_evidence_only(evidence: Any) -> dict:
    return analyze_http_evidence(_target_from_evidence(evidence), evidence)
