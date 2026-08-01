from __future__ import annotations
import hashlib, json, re
from collections import Counter
from .contracts import RatificationStatus
from .models import ClaimEvidence, ConstitutionalArticle, RatificationPolicy

_WORD_RE = re.compile(r"[A-Za-z0-9]+")
def _hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def _title(domain):
    return " ".join(x.capitalize() for x in _WORD_RE.findall(domain.replace("_"," ").replace("-"," "))) or "General"
def _domain(cluster):
    counts = Counter(c.domain or "general" for c in cluster)
    return sorted(counts.items(), key=lambda x:(-x[1],x[0]))[0][0]
def _conflicts(ids, relationships):
    found=set()
    for edge in relationships:
        if str(edge.get("relationship_type","")) != "contradicts": continue
        a,b=str(edge.get("source_claim_id","")),str(edge.get("target_claim_id",""))
        if a in ids: found.add(b)
        if b in ids: found.add(a)
    return tuple(sorted(found))

def build_articles(clusters, relationships, policy: RatificationPolicy):
    provisional=[]
    for cluster in clusters:
        representative=sorted(cluster,key=lambda c:(-c.authority_rank,-len(c.text),c.source_path,c.line_start,c.claim_id))[0]
        domain=_domain(cluster)
        ids=tuple(sorted(c.claim_id for c in cluster))
        conflicts=_conflicts(frozenset(ids),relationships)
        high_single=(len(cluster)==1 and policy.ratify_singleton_high_authority and representative.authority_rank>=policy.high_authority_threshold)
        enough=len(cluster)>=policy.minimum_supporting_claims
        if conflicts and not policy.allow_unresolved_conflicts:
            status=RatificationStatus.REVIEW_REQUIRED.value
            rationale="Unresolved contradictory claims require constitutional review."
        elif enough or high_single:
            status=RatificationStatus.RATIFIED.value
            rationale="Cluster satisfies deterministic ratification policy."
        else:
            status=RatificationStatus.REJECTED.value
            rationale="Cluster does not satisfy deterministic ratification threshold."
        provisional.append({
            "canonical_text":representative.text.strip(),"domain":domain,"status":status,
            "authority":representative.authority,"authority_rank":representative.authority_rank,
            "supporting_claim_ids":ids,
            "supporting_source_paths":tuple(sorted({c.source_path for c in cluster})),
            "conflict_claim_ids":conflicts,"evidence_count":len(cluster),"rationale":rationale,
        })
    provisional.sort(key=lambda x:(x["domain"],x["canonical_text"].lower(),x["supporting_claim_ids"]))
    result=[]
    for index,item in enumerate(provisional,1):
        article_id=f"ARTICLE-{index:04d}"
        fp=_hash({"article_id":article_id,**item,"revision":1})
        result.append(ConstitutionalArticle(
            article_id=article_id,title=_title(item["domain"]),canonical_text=item["canonical_text"],
            domain=item["domain"],section_id="",status=item["status"],authority=item["authority"],
            authority_rank=item["authority_rank"],supporting_claim_ids=item["supporting_claim_ids"],
            supporting_source_paths=item["supporting_source_paths"],conflict_claim_ids=item["conflict_claim_ids"],
            evidence_count=item["evidence_count"],fingerprint=fp,revision=1,rationale=item["rationale"],
        ))
    return tuple(result)
