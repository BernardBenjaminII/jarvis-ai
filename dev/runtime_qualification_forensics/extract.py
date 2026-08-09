from collections.abc import Mapping
from .contracts import CandidateForensicRecord

def mapping(value):
    if value is None: return {}
    if isinstance(value, Mapping): return dict(value)
    if hasattr(value,"to_dict") and callable(value.to_dict):
        try:
            result=value.to_dict()
            return dict(result) if isinstance(result,Mapping) else {}
        except Exception:
            return {}
    try: return dict(value)
    except Exception: return {}

def number(value):
    if value is None: return None
    if isinstance(value, Mapping):
        for key in ("value","score","final","normalized"):
            if key in value: return number(value[key])
        return None
    try: return float(value)
    except (TypeError,ValueError): return None

def component(data,*names):
    for container in (
        mapping(data.get("qualification_components")),
        mapping(data.get("components")),
        mapping(data.get("score")),
        data,
    ):
        for name in names:
            if name in container:
                resolved=number(container[name])
                if resolved is not None: return resolved
    return None

def infer_reason(decision, explanation, lexical, phrase, subject, confidence, final, threshold):
    if decision.casefold().startswith("accept"): return None
    text=explanation.casefold()
    for keyword,reason in (
        ("lexical","LEXICAL"),("phrase","PHRASE"),("subject","SUBJECT"),
        ("topic","SUBJECT"),("confidence","CONFIDENCE"),
        ("threshold","FINAL_THRESHOLD"),("below","FINAL_THRESHOLD"),
    ):
        if keyword in text: return reason
    scored={"LEXICAL":lexical,"PHRASE":phrase,"SUBJECT":subject,"CONFIDENCE":confidence}
    scored={k:v for k,v in scored.items() if v is not None}
    if scored: return min(scored,key=scored.get)
    if final is not None and threshold is not None and final < threshold:
        return "FINAL_THRESHOLD"
    return "UNKNOWN"

def candidate_record(value, *, raw_rank, threshold):
    data=mapping(value)
    nested=mapping(data.get("candidate"))
    metadata=mapping(data.get("metadata"))
    raw=mapping(metadata.get("raw_row") or data.get("raw_row"))
    merged={**raw,**metadata,**nested,**data}
    candidate_id=str(merged.get("source_id") or merged.get("chunk_id") or merged.get("document_id") or merged.get("id") or f"candidate-{raw_rank}")
    title=str(merged.get("title") or merged.get("document_title") or candidate_id)
    source_path=str(merged.get("source_path") or merged.get("file_path") or merged.get("path") or "")
    decision=str(merged.get("qualification_decision") or merged.get("decision") or merged.get("status") or "UNKNOWN")
    explanation=str(merged.get("qualification_explanation") or merged.get("explanation") or merged.get("reason") or "")
    lexical=component(merged,"lexical","lexical_score")
    phrase=component(merged,"phrase","phrase_score")
    subject=component(merged,"subject","subject_score")
    confidence=component(merged,"confidence","confidence_score")
    final=component(merged,"final","final_score","qualification_score")
    retrieval=component(merged,"retrieval_score","raw_score")
    active=threshold if threshold is not None else number(merged.get("threshold"))
    margin=None if final is None or active is None else final-active
    reason=infer_reason(decision,explanation,lexical,phrase,subject,confidence,final,active)
    return CandidateForensicRecord(
        candidate_id,title,source_path,raw_rank,retrieval,lexical,phrase,subject,
        confidence,final,active,margin,decision,reason,explanation,
        {"diagnostic_keys":sorted(str(k) for k in data)}
    )
