from .contracts import KnowledgeReadiness
from .enums import KnowledgeCoverageStatus as K

def build_knowledge_readiness(*, query, coverage, known_domains=(), missing_domains=(), recommended_sources=(), catalog_reference='', minimum_coverage=0.70):
    if coverage >= minimum_coverage: status, proceed, limit = K.SUFFICIENT, True, min(coverage,0.95)
    elif coverage > 0: status, proceed, limit = K.PARTIAL, True, coverage
    else: status, proceed, limit = K.INSUFFICIENT, False, 0.0
    return KnowledgeReadiness(query,status,coverage,tuple(sorted(set(known_domains))),tuple(sorted(set(missing_domains))),tuple(sorted(set(recommended_sources))),proceed,limit,catalog_reference)
