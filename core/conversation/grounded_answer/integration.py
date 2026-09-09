from __future__ import annotations
import re
from typing import Any
from core.knowledge_catalog.qualified_search import get_last_qualification_result
from .contracts import GroundedAnswerExecutionRequest, GroundedAnswerRuntimeContext
from .service import GroundedAnswerRuntimeService
from .telemetry import publish_grounded_answer_telemetry


# Sentinel distinguishes a legacy caller that omitted qualification from a
# current caller that explicitly captured "no qualification" for its request.
_QUALIFICATION_UNSET = object()


def ensure_grounded_answer_service(orchestrator: Any):
    service=getattr(orchestrator,"grounded_answer_service",None)
    if isinstance(service,GroundedAnswerRuntimeService): return service
    service=GroundedAnswerRuntimeService.create_default()
    setattr(orchestrator,"grounded_answer_service",service)
    return service

def build_runtime_request(context: Any, qualification: Any):
    metadata=dict(getattr(context,"metadata",{}) or {})
    return GroundedAnswerExecutionRequest(
        context=GroundedAnswerRuntimeContext(
            request_id=str(metadata.get("request_id") or metadata.get("correlation_id") or "executive-request"),
            session_id=str(metadata.get("session_id") or getattr(context,"session_id","") or "executive-session"),
            operator_input=str(getattr(context,"operator_input","") or ""),
            mode=str(getattr(context,"mode","full") or "full"),
            channel=str(getattr(context,"channel","text") or "text"),
            metadata=metadata),
        qualification=qualification)

def augment_synthesis_input(
    orchestrator: Any,
    context: Any,
    synthesis_input: str,
    *,
    qualification: Any = _QUALIFICATION_UNSET,
) -> str:
    # New callers pass the request-local qualification captured immediately
    # after grounding. The ContextVar lookup remains solely for compatibility
    # with older integrations that do not yet provide it explicitly.
    if qualification is _QUALIFICATION_UNSET:
        qualification = get_last_qualification_result()
    if qualification is None: return synthesis_input
    service=ensure_grounded_answer_service(orchestrator)
    request=build_runtime_request(context,qualification)
    response=service.plan(request)
    setattr(orchestrator,"_last_grounded_answer_plan",response.plan)
    setattr(orchestrator,"_last_grounded_answer_response",response)
    telemetry=publish_grounded_answer_telemetry(runtime_request=request,qualification=qualification,response=response)
    setattr(orchestrator,"_last_grounded_answer_telemetry",telemetry)
    contract=response.plan.synthesis_prompt.strip()
    if not contract or "JARVIS GROUNDED ANSWER CONTRACT:" in synthesis_input:
        return synthesis_input
    return synthesis_input.rstrip()+"\n\n"+contract+"\n"

# GENESIS_UI_CONVERSATION_R4_R2
_CITATION_MARKER_RE = re.compile(r"\[(C\d+)\]")
_URL_RE = re.compile(r"https?://[^\s<>()\[\]{}]+", re.IGNORECASE)
_CONTENT_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{3,}")
_CONTENT_STOPWORDS = frozenset({
    "about", "after", "again", "against", "also", "available", "based",
    "before", "being", "below", "could", "evidence", "from", "have",
    "into", "network", "security", "should", "that", "their", "these",
    "they", "this", "through", "using", "which", "with", "would", "your",
})


def _content_terms(value: str) -> set[str]:
    return {
        token.casefold()
        for token in _CONTENT_TOKEN_RE.findall(str(value or ""))
        if token.casefold() not in _CONTENT_STOPWORDS
    }


def enforce_grounded_answer_output(orchestrator: Any, answer: str) -> str:
    """Return model prose only when every citation is valid and supported.

    A failed validation uses the engine's existing deterministic answer. This
    preserves qualified evidence and valid [C#] citations without laundering
    unsupported model claims through authoritative-looking markers.
    """
    plan = getattr(orchestrator, "_last_grounded_answer_plan", None)
    if plan is None:
        return answer

    service = ensure_grounded_answer_service(orchestrator)
    citations = tuple(getattr(plan, "citations", ()) or ())
    state = str(getattr(getattr(plan, "state", None), "value", "")).casefold()
    if state == "unknown" or not citations:
        setattr(orchestrator, "_grounded_answer_output_fallback", True)
        return service.engine.deterministic_answer(plan)

    citation_map = {
        str(item.citation_id): str(item.excerpt or "")
        for item in citations
    }
    used_markers = set(_CITATION_MARKER_RE.findall(answer or ""))
    valid_markers = set(citation_map)
    violation = not used_markers or not used_markers.issubset(valid_markers)

    # Every URL must come verbatim from qualified evidence or its source
    # metadata.  This blocks plausible-looking external links invented by the
    # synthesis model.
    provenance_text = "\n".join(
        "\n".join((
            str(getattr(item, "excerpt", "") or ""),
            str(getattr(item, "source_path", "") or ""),
            str(getattr(item, "title", "") or ""),
        ))
        for item in citations
    )
    if any(url.rstrip(".,;:") not in provenance_text for url in _URL_RE.findall(answer or "")):
        violation = True

    if not violation:
        for line in str(answer or "").splitlines():
            markers = _CITATION_MARKER_RE.findall(line)
            if not markers:
                continue
            claim = _CITATION_MARKER_RE.sub("", line).strip(" -*#\t")
            claim_terms = _content_terms(claim)
            evidence_terms = set().union(*(
                _content_terms(citation_map.get(marker, ""))
                for marker in markers
            ))
            shared = claim_terms & evidence_terms
            ratio = len(shared) / max(1, len(claim_terms))
            if not claim_terms or (ratio < 0.30 and len(shared) < 3):
                violation = True
                break

    if not violation:
        return answer

    fallback = service.engine.deterministic_answer(plan)
    setattr(orchestrator, "_grounded_answer_output_fallback", True)
    return fallback


def get_last_grounded_answer_plan(orchestrator): return getattr(orchestrator,"_last_grounded_answer_plan",None)
def get_last_grounded_answer_response(orchestrator): return getattr(orchestrator,"_last_grounded_answer_response",None)
def get_last_grounded_answer_telemetry(orchestrator): return getattr(orchestrator,"_last_grounded_answer_telemetry",None)
