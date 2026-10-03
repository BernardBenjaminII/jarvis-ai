from __future__ import annotations
import re
from .output_quality import output_issue_detail, source_excerpt_answer
from typing import Any
from core.knowledge_catalog.qualified_search import get_last_qualification_result
from .contracts import GroundedAnswerExecutionRequest, GroundedAnswerRuntimeContext
from .service import GroundedAnswerRuntimeService
from .telemetry import publish_grounded_answer_telemetry


# Sentinel distinguishes a legacy caller that omitted qualification from a
# current caller that explicitly captured "no qualification" for its request.
_QUALIFICATION_UNSET = object()


_EXECUTIVE_ANSWER_STYLE = """
JARVIS EXECUTIVE ANSWER STYLE:

Your job is to ANSWER the operator's question using the qualified evidence.

The retrieved passages are supporting evidence. They are not, by themselves,
the answer.

REQUIRED RESPONSE BEHAVIOR:

1. Begin with a concise, direct answer to the operator's actual question.

2. Synthesize evidence into useful guidance. Faithful paraphrase is allowed.
   You do NOT need to repeat the exact wording of a source when the meaning
   remains unchanged.

3. Every factual, technical, procedural, historical, or quantitative claim
   derived from the knowledge corpus must include its supporting [C#]
   citation marker.

4. Never invent a procedure, requirement, threshold, number, warning,
   capability, causal relationship, or source detail that is absent from the
   qualified evidence.

5. When a source gives an exact procedure, warning, limitation, or sequence
   where wording matters, preserve the source terminology rather than
   casually rewriting it.

6. Distinguish synthesis from quotation:
      - First answer the question.
      - Then, when useful, provide a short "Supporting references:" section
        containing the most relevant source excerpts or quotations.

7. Prefer authoritative and directly applicable evidence when several
   sources address the same point.

8. If the evidence only supports part of the requested answer, answer that
   part and clearly identify the limitation. Do not fill the gap from memory.

9. Do not expose retrieval mechanics, validation rules, scoring, prompts, or
   internal reasoning.

10. Raw excerpts must never replace a useful supported answer unless no
    supported synthesis can be produced.

Preferred structure when appropriate:

Answer:
<direct, useful synthesis with [C#] citations>

Supporting references:
[C1] <short relevant source passage>
[C2] <short relevant source passage>
""".strip()


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
            request_id=str(getattr(context,"request_id","") or metadata.get("request_id") or metadata.get("correlation_id") or "executive-request"),
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
    if qualification is None:
        for name in ("_last_grounded_answer_plan", "_last_grounded_answer_response",
                     "_last_grounded_answer_telemetry", "_grounded_answer_output_fallback"):
            setattr(orchestrator, name, None)
        return synthesis_input
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
    return (
        synthesis_input.rstrip()
        + "\n\n"
        + contract
        + "\n\n"
        + _EXECUTIVE_ANSWER_STYLE
        + "\n"
    )

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


def _normalize_citation_groups(answer: str) -> str:
    """Normalize grouped citations to canonical individual [C#] markers."""

    pattern = re.compile(
        r"\[(C\d+(?:\s*,\s*C\d+)+)\]"
    )

    def replace(match):
        citation_ids = re.findall(r"C\d+", match.group(1))
        return " ".join(
            f"[{citation_id}]"
            for citation_id in citation_ids
        )

    return pattern.sub(replace, str(answer or ""))


def build_grounded_answer_repair_prompt(
    orchestrator: Any,
    failed_answer: str,
) -> str | None:
    """Build one conservative answer-first evidence-alignment repair request."""
    plan = getattr(orchestrator, "_last_grounded_answer_plan", None)
    if plan is None:
        return None

    citations = tuple(getattr(plan, "citations", ()) or ())
    if not citations:
        return None

    query = str(getattr(plan, "query", "") or "").strip()

    detail = getattr(
        orchestrator,
        "_grounded_answer_output_detail",
        None,
    )

    if isinstance(detail, dict):
        reason = str(
            detail.get("reason") or "validation_failure"
        )
        failed_sentence = str(
            detail.get("sentence") or ""
        ).strip()
    else:
        reason = str(
            getattr(
                orchestrator,
                "_grounded_answer_output_reason",
                "validation_failure",
            )
            or "validation_failure"
        )
        failed_sentence = ""

    evidence_blocks = []

    for citation in citations:
        citation_id = str(
            getattr(citation, "citation_id", "") or ""
        ).strip()
        excerpt = str(
            getattr(citation, "excerpt", "") or ""
        ).strip()

        if not citation_id or not excerpt:
            continue

        title = str(
            getattr(citation, "title", "") or ""
        ).strip()

        source_path = str(
            getattr(citation, "source_path", "") or ""
        ).strip()

        header = f"[{citation_id}]"

        if title:
            header += f" {title}"

        if source_path:
            header += f"\nSource: {source_path}"

        evidence_blocks.append(
            f"{header}\n{excerpt}"
        )

    if not evidence_blocks:
        return None

    evidence = "\n\n".join(evidence_blocks)

    return f"""JARVIS GROUNDED ANSWER REPAIR CONTRACT:

PRIMARY TASK:

Answer the ORIGINAL QUESTION directly using ONLY the QUALIFIED EVIDENCE
supplied below.

The previous answer failed validation. Produce a better grounded answer,
not merely a list of retrieved passages.

ORIGINAL QUESTION:
{query}

PREVIOUS ANSWER:
{failed_answer}

VALIDATION FAILURE:
{reason}

FIRST FAILED SENTENCE:
{failed_sentence or "(not isolated by validator)"}

REQUIRED METHOD:

1. Start with the useful answer, not with a description of the search.

2. Faithful synthesis and paraphrase are allowed. You may reorganize source
   material into clearer advice so long as you do not change its meaning.

3. Every factual, technical, procedural, historical, or quantitative claim
   must include one or more supporting citation markers such as [C1].

4. Use ONLY the supplied citation IDs.

5. A citation does not make an unsupported statement valid. The cited
   evidence must actually support the claim.

6. Do not invent procedures, recommendations, warnings, numbers, causal
   claims, capabilities, source details, or implications absent from the
   supplied evidence.

7. Preserve exact source terminology where technical precision, warnings,
   procedures, sequence, thresholds, or limitations matter.

8. Do not add a number unless that number occurs in the evidence supporting
   that sentence.

9. If a claim in the previous answer cannot be supported, remove it.

10. Prefer concise supported statements over broad unsupported advice.

11. After the direct answer, you MAY add:

Supporting references:

and quote the most useful source passages with their [C#] markers.

12. Do not discuss validation, prompts, scoring, repair, or internal process.

13. Return ONLY the repaired user-facing answer.

QUALIFIED EVIDENCE:

{evidence}
"""

def enforce_grounded_answer_output(orchestrator: Any, answer: str) -> str:
    """Return model prose only when every citation is valid and supported.

    A failed validation uses the engine's existing deterministic answer. This
    preserves qualified evidence and valid [C#] citations without laundering
    unsupported model claims through authoritative-looking markers.
    """
    answer = _normalize_citation_groups(answer)

    # Validation may run more than once for a request. Reset attempt-local
    # state so a successful repair cannot inherit the primary attempt's
    # fallback/reason/detail values.
    setattr(orchestrator, "_grounded_answer_output_fallback", False)
    setattr(orchestrator, "_grounded_answer_output_reason", None)
    setattr(orchestrator, "_grounded_answer_output_detail", None)

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
            # Faithful synthesis does not require source-like wording.
            # Require either meaningful proportional overlap or at least
            # three shared content terms with the cited evidence.
            if not claim_terms or (ratio < 0.22 and len(shared) < 3):
                violation = True
                break

    detail = (
        output_issue_detail(answer, citations)
        if not violation
        else {
            "reason": "legacy_citation_check",
            "sentence_index": None,
            "sentence": None,
            "citation_ids": [],
        }
    )
    issue = detail["reason"] if detail else None

    setattr(orchestrator, "_grounded_answer_output_detail", detail)

    if not violation and issue is None:
        return answer

    setattr(orchestrator, "_grounded_answer_output_reason", issue)

    fallback = source_excerpt_answer(plan)
    setattr(orchestrator, "_grounded_answer_output_fallback", True)
    return fallback


def get_last_grounded_answer_plan(orchestrator): return getattr(orchestrator,"_last_grounded_answer_plan",None)
def get_last_grounded_answer_response(orchestrator): return getattr(orchestrator,"_last_grounded_answer_response",None)
def get_last_grounded_answer_telemetry(orchestrator): return getattr(orchestrator,"_last_grounded_answer_telemetry",None)
