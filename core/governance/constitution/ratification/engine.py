from __future__ import annotations
import hashlib, json
from pathlib import Path
from .articles import build_articles
from .clustering import build_clusters
from .contracts import RATIFICATION_SCHEMA_VERSION, RatificationStatus
from .loader import load_analysis
from .models import CanonicalConstitution, RatificationPolicy, RatificationStatistics
from .sections import build_sections
from .traceability import build_traceability

def _hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

class ConstitutionalRatificationEngine:
    def ratify(self,analysis_directory:Path,policy:RatificationPolicy|None=None):
        active=policy or RatificationPolicy()
        repo,extract,analysis,claims,relationships=load_analysis(analysis_directory)
        clusters=build_clusters(claims,relationships)
        articles=build_articles(clusters,relationships,active)
        articles,sections=build_sections(articles)
        trace=build_traceability(articles,claims,repo,extract,analysis)
        represented={x for a in articles for x in a.supporting_claim_ids}
        stats=RatificationStatistics(
            claims=len(claims),clusters=len(clusters),articles=len(articles),
            ratified_articles=sum(a.status==RatificationStatus.RATIFIED.value for a in articles),
            review_required_articles=sum(a.status==RatificationStatus.REVIEW_REQUIRED.value for a in articles),
            rejected_articles=sum(a.status==RatificationStatus.REJECTED.value for a in articles),
            sections=len(sections),traced_claims=len(represented),
            unrepresented_claims=len({c.claim_id for c in claims}-represented),diagnostics=0,
        )
        basis={"schema_version":RATIFICATION_SCHEMA_VERSION,"repository_fingerprint":repo,
               "extraction_fingerprint":extract,"analysis_fingerprint":analysis,
               "policy":active.to_dict(),"articles":[a.to_dict() for a in articles],
               "sections":[s.to_dict() for s in sections],"traceability":[t.to_dict() for t in trace],
               "statistics":stats.to_dict()}
        return CanonicalConstitution(
            schema_version=RATIFICATION_SCHEMA_VERSION,repository_fingerprint=repo,
            extraction_fingerprint=extract,analysis_fingerprint=analysis,
            ratification_fingerprint=_hash(basis),policy=active,articles=articles,
            sections=sections,traceability=trace,statistics=stats,diagnostics=(),
        )
