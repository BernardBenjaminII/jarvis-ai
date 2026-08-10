from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Iterable

from core.retrieval.evidence_context.models import EvidenceBundle, EvidenceItem

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_+#.-]*")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n{2,}")
_STOP = {"a","an","and","are","as","at","be","by","do","does","for","from","i","in","is","it","of","on","or","that","the","their","this","to","what","when","where","which","who","with"}

INTENT_DEFINITION="definition"
INTENT_MECHANISM="mechanism"
INTENT_CAUSAL="causal"
INTENT_COMPARISON="comparison"
INTENT_PROCEDURAL="procedural"
INTENT_TEMPORAL="temporal"
INTENT_GENERAL="general"

_INTENT_PATTERNS=(
    (INTENT_MECHANISM,(re.compile(r"\bhow\s+(?:does|do|did|is|are|can|could|would)?\s*.+\bwork\b",re.I),re.compile(r"\bhow\s+.+\bworks\b",re.I),re.compile(r"\bhow\s+.+\bfunction(?:s)?\b",re.I))),
    (INTENT_PROCEDURAL,(re.compile(r"^\s*how\s+to\b",re.I),re.compile(r"\bsteps?\s+to\b",re.I))),
    (INTENT_COMPARISON,(re.compile(r"\bdifference\s+between\b",re.I),re.compile(r"\bcompare\b",re.I),re.compile(r"\bversus\b|\bvs\.?\b",re.I))),
    (INTENT_DEFINITION,(re.compile(r"^\s*what\s+(?:is|are)\b",re.I),re.compile(r"^\s*define\b",re.I),re.compile(r"\bmeaning\s+of\b",re.I))),
    (INTENT_CAUSAL,(re.compile(r"^\s*why\b",re.I),re.compile(r"\bwhat\s+causes?\b",re.I),re.compile(r"\breason(?:s)?\s+for\b",re.I))),
    (INTENT_TEMPORAL,(re.compile(r"^\s*when\b",re.I),re.compile(r"\bhow\s+long\b",re.I))),
)

_INTENT_CUES={
    INTENT_DEFINITION:(" is "," are "," means "," refers to "," defined as "," describes "," represents "),
    INTENT_MECHANISM:(" works "," works by "," operates "," operates by "," functions "," mechanism "," process "," through "," using "," moves "," advances "," travers"," accesses "," returns "," points to "," derefer"," increment"," begin("," end("),
    INTENT_CAUSAL:(" because "," causes "," caused by "," due to "," therefore "," results in "," leads to "," reason "),
    INTENT_COMPARISON:(" whereas "," while "," compared "," unlike "," similar "," different "," both "," however "),
    INTENT_PROCEDURAL:(" first "," next "," then "," finally "," step "," run "," execute "," create "," configure "," install "," use "),
    INTENT_TEMPORAL:(" before "," after "," during "," until "," when "," time "," duration "),
    INTENT_GENERAL:tuple(),
}

def _tokens(text:str)->tuple[str,...]:
    out=[]
    for token in _TOKEN_RE.findall(text.casefold()):
        token=token.strip(".")
        if len(token)>=2 and token not in _STOP:
            out.append(token)
    return tuple(out)

def _unique(values:Iterable[str])->tuple[str,...]:
    seen=set(); out=[]
    for v in values:
        if v not in seen:
            seen.add(v); out.append(v)
    return tuple(out)

def detect_query_intent(query:str)->str:
    text=" ".join(str(query).split())
    for intent,patterns in _INTENT_PATTERNS:
        if any(p.search(text) for p in patterns):
            return intent
    return INTENT_GENERAL

@dataclass(frozen=True)
class FocusedEvidence:
    item: EvidenceItem
    utility_score: float
    query_coverage: float
    passage_density: float
    intent_alignment: float
    focus_text: str

@dataclass(frozen=True)
class FocusResult:
    bundle: EvidenceBundle
    utility_scores: dict[str,float]
    intent: str
    diagnostics: tuple[dict,...]

class EvidenceFocusService:
    def __init__(self,*,max_passage_chars:int=2200,max_sentences:int=8):
        self.max_passage_chars=max(256,int(max_passage_chars)); self.max_sentences=max(1,int(max_sentences))

    def _query_terms(self,query:str,bundle_terms:Iterable[str])->tuple[str,...]:
        return _unique((*_tokens(query),*(_tokens(" ".join(bundle_terms)))))

    def _intent_alignment(self,text:str,intent:str)->float:
        if intent==INTENT_GENERAL: return 0.0
        n=f" {str(text).casefold()} "; cues=_INTENT_CUES.get(intent,tuple())
        hits=sum(1 for cue in cues if cue in n)
        return min(1.0,hits/4.0) if cues else 0.0

    def _sentence_score(self,sentence:str,query_terms:tuple[str,...],intent:str)->float:
        st=set(_tokens(sentence)); qt=set(query_terms)
        if not st: return 0.0
        overlap=len(st & qt); coverage=overlap/max(1,len(qt)); density=overlap/max(1,len(st)); ia=self._intent_alignment(sentence,intent)
        structural=0.06 if any(x in sentence for x in ("++","->","::",".begin(",".end(","*it","=>")) else 0.0
        return min(1.0,0.48*coverage+0.18*min(1.0,density*3.0)+0.28*ia+structural)

    def _focus_text(self,text:str,query_terms:tuple[str,...],intent:str)->tuple[str,float,float]:
        text=(text or "").strip()
        if not text: return "",0.0,0.0
        parts=[p.strip() for p in _SENTENCE_RE.split(text) if p.strip()]
        if not parts:
            short=text[:self.max_passage_chars]; return short,0.0,self._intent_alignment(short,intent)
        scored=[(self._sentence_score(s,query_terms,intent),i,s) for i,s in enumerate(parts)]
        relevant=[r for r in scored if r[0]>0.0]
        if not relevant:
            short=text[:self.max_passage_chars]; return short,0.0,self._intent_alignment(short,intent)
        best=sorted(relevant,key=lambda r:(-r[0],r[1])); idx={i for _,i,_ in best[:self.max_sentences]}
        focused="\n".join(s for i,s in enumerate(parts) if i in idx).strip() or text
        focused=focused[:self.max_passage_chars]
        ft=_tokens(focused); qs=set(query_terms); density=sum(1 for t in ft if t in qs)/max(1,len(ft))
        return focused,min(1.0,density*5.0),self._intent_alignment(focused,intent)

    def score(self,query:str,bundle:EvidenceBundle,item:EvidenceItem)->FocusedEvidence:
        intent=detect_query_intent(query); terms=self._query_terms(query,bundle.query_terms); qs=set(terms); it=set(_tokens(item.text))
        coverage=len(it & qs)/max(1,len(qs)); focus_text,pdensity,ialign=self._focus_text(item.text,terms,intent)
        matched=set(_tokens(" ".join(item.matched_terms))); mcoverage=len(matched & qs)/max(1,len(qs)) if qs else 0.0
        role_bonus={"anchor":0.035,"neighbor":0.0}.get(item.source_role,0.0)
        utility=0.34*float(item.hybrid_score)+0.12*coverage+0.17*pdensity+0.11*mcoverage+0.06*float(item.lexical_score)+0.18*ialign+role_bonus
        return FocusedEvidence(item,max(0.0,min(1.0,utility)),max(0.0,min(1.0,coverage)),max(0.0,min(1.0,pdensity)),max(0.0,min(1.0,ialign)),focus_text)

    def focus_result(self,query:str,bundle:EvidenceBundle)->FocusResult:
        intent=detect_query_intent(query); scored=[self.score(query,bundle,i) for i in bundle.selected_evidence]
        scored.sort(key=lambda x:(-x.utility_score,-x.intent_alignment,-x.passage_density,-x.query_coverage,-x.item.hybrid_score,x.item.rank,x.item.runtime_chunk_id))
        items=[]; utilities={}; diagnostics=[]
        for rank,r in enumerate(scored,1):
            original=r.item; text=r.focus_text or original.text; focused=replace(original,rank=rank,text=text,chars=len(text)); items.append(focused); utilities[focused.evidence_id]=r.utility_score
            diagnostics.append({"original_rank":original.rank,"focused_rank":rank,"evidence_id":original.evidence_id,"runtime_chunk_id":original.runtime_chunk_id,"runtime_document_id":original.runtime_document_id,"source_role":original.source_role,"query_intent":intent,"hybrid_score":round(original.hybrid_score,6),"utility_score":round(r.utility_score,6),"query_coverage":round(r.query_coverage,6),"passage_density":round(r.passage_density,6),"intent_alignment":round(r.intent_alignment,6),"original_chars":original.chars,"focused_chars":len(text)})
        fb=replace(bundle,selected_evidence=tuple(items),total_chars=sum(x.chars for x in items))
        return FocusResult(fb,utilities,intent,tuple(diagnostics))

    def focus(self,query:str,bundle:EvidenceBundle)->EvidenceBundle:
        return self.focus_result(query,bundle).bundle

    def diagnostics(self,query:str,bundle:EvidenceBundle)->list[dict]:
        return list(self.focus_result(query,bundle).diagnostics)
