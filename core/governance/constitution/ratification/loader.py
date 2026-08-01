from __future__ import annotations
import json
from pathlib import Path
from .models import ClaimEvidence

class AnalysisArtifactError(RuntimeError): pass

def _read(path: Path):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc: raise AnalysisArtifactError(f"Missing C2 artifact: {path}") from exc
    except json.JSONDecodeError as exc: raise AnalysisArtifactError(f"Invalid JSON: {path}: {exc}") from exc

def load_analysis(directory: Path):
    summary = _read(directory / "constitutional_analysis.json")
    graph = _read(directory / "constitutional_graph.json")
    nodes, edges = graph.get("nodes", []), graph.get("edges", [])
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise AnalysisArtifactError("C2 graph requires list-valued nodes and edges")
    claims = []
    for i, item in enumerate(nodes):
        if not isinstance(item, dict): raise AnalysisArtifactError(f"Node {i} is not an object")
        claim = ClaimEvidence(
            claim_id=str(item.get("claim_id","")),
            source_path=str(item.get("source_path","")),
            text=str(item.get("text","")),
            domain=str(item.get("domain","general") or "general"),
            authority=str(item.get("authority","other") or "other"),
            authority_rank=int(item.get("authority_rank",100) or 100),
            source_hash=str(item.get("source_hash","")),
            excerpt_hash=str(item.get("excerpt_hash","")),
            line_start=int(item.get("line_start",0) or 0),
            line_end=int(item.get("line_end",0) or 0),
        )
        if not claim.claim_id or not claim.text:
            raise AnalysisArtifactError(f"Node {i} lacks claim_id or text")
        claims.append(claim)
    claims.sort(key=lambda x: x.claim_id)
    edges = tuple(sorted(
        (dict(x) for x in edges if isinstance(x, dict)),
        key=lambda x: (
            str(x.get("source_claim_id","")),
            str(x.get("target_claim_id","")),
            str(x.get("relationship_type","")),
            str(x.get("relationship_id","")),
        ),
    ))
    return (
        str(summary.get("repository_fingerprint","")),
        str(summary.get("extraction_fingerprint","")),
        str(summary.get("analysis_fingerprint","")),
        tuple(claims),
        edges,
    )
