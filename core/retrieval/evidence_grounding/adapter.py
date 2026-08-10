from __future__ import annotations

from collections.abc import Mapping
from core.retrieval.evidence_context.models import EvidenceBundle
from core.retrieval.qualification import EvidenceCandidate, QualificationDecision, QualificationResult, QualificationScore, QualifiedEvidence

def _unit(value:float)->float:
    return max(0.0,min(1.0,float(value)))

class EvidenceBundleQualificationAdapter:
    def convert(self,bundle:EvidenceBundle,*,utility_scores:Mapping[str,float]|None=None,query_intent:str|None=None)->QualificationResult:
        accepted=[]; utility_scores=utility_scores or {}
        for item in bundle.selected_evidence:
            utility=_unit(utility_scores.get(item.evidence_id,item.hybrid_score))
            candidate=EvidenceCandidate(
                source_id=f"runtime-document:{item.runtime_document_id}:chunk:{item.runtime_chunk_id}",
                source_path=item.file_path,title=item.document_title,subject=bundle.query,excerpt=item.text,
                backend="genesis_x_b2_evidence_context",retrieval_score=_unit(item.hybrid_score),
                metadata={
                    "evidence_id":item.evidence_id,"rank":item.rank,"source_role":item.source_role,
                    "runtime_chunk_id":item.runtime_chunk_id,"runtime_document_id":item.runtime_document_id,
                    "chunk_uuid":item.chunk_uuid,"fragment_uuid":item.fragment_uuid,
                    "hybrid_score":item.hybrid_score,"semantic_score":item.semantic_score,
                    "lexical_score":item.lexical_score,"title_score":item.title_score,
                    "matched_terms":list(item.matched_terms),"chars":item.chars,
                    "synthesis_utility_score":utility,"query_intent":query_intent,
                },
            )
            accepted.append(QualifiedEvidence(candidate=candidate,score=QualificationScore(final=utility),decision=QualificationDecision.ACCEPTED,explanation="Accepted by Genesis X-B2.3 evidence assembly; synthesis utility propagated by Genesis X-B2.4A-1."))
        return QualificationResult(accepted=tuple(accepted))
