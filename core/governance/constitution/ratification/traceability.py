from __future__ import annotations
from .models import TraceabilityRecord

def build_traceability(articles,claims,repository_fingerprint,extraction_fingerprint,analysis_fingerprint):
    by_id={c.claim_id:c for c in claims}
    result=[]
    for article in articles:
        evidence=[by_id[x] for x in article.supporting_claim_ids]
        result.append(TraceabilityRecord(
            article_id=article.article_id,claim_ids=article.supporting_claim_ids,
            source_paths=tuple(sorted({c.source_path for c in evidence})),
            source_hashes=tuple(sorted({c.source_hash for c in evidence if c.source_hash})),
            repository_fingerprint=repository_fingerprint,
            extraction_fingerprint=extraction_fingerprint,analysis_fingerprint=analysis_fingerprint,
        ))
    return tuple(sorted(result,key=lambda x:x.article_id))
