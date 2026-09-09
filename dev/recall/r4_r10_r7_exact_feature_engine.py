from __future__ import annotations
import math
import re
from typing import Any, Mapping
from core.knowledge_catalog.materialization.search import _fts_query, search_runtime_knowledge
FILE_NOISE = {'html', 'htm', 'pdf', 'txt', 'doc', 'docx', 'xml', 'json', 'csv'}
GENERIC_QUERY_NOISE = {'file', 'document', 'page', 'chapter'}

def text(value: Any) -> str:
    if value is None:
        return ''
    return str(value).strip()

def boundary_tokens(value: str) -> tuple[str, ...]:
    return tuple((token.casefold() for token in re.findall('[A-Za-z0-9]{2,}', str(value or ''))))

def production_terms(query: str) -> tuple[str, ...]:
    expression = _fts_query(query)
    return tuple((term.casefold() for term in re.findall('"([^"]+)"', expression or '')))

def substantive_terms(query: str) -> tuple[str, ...]:
    raw = production_terms(query)
    result = []
    seen = set()
    for token in raw:
        if token in FILE_NOISE:
            continue
        if token in GENERIC_QUERY_NOISE:
            continue
        if token in seen:
            continue
        seen.add(token)
        result.append(token)
    if not result:
        for token in raw:
            if token in seen:
                continue
            seen.add(token)
            result.append(token)
    return tuple(result)

def title_identity_tokens(value: str) -> tuple[str, ...]:
    raw = re.findall('[A-Za-z0-9]+', str(value or '').casefold())
    result = []
    seen = set()
    for token in raw:
        if token in FILE_NOISE:
            continue
        if len(token) >= 2:
            keep = True
        elif len(token) == 1 and token.isdigit():
            keep = True
        else:
            keep = False
        if not keep:
            continue
        if token in seen:
            continue
        seen.add(token)
        result.append(token)
    return tuple(result)

def query_identity_tokens(query: str) -> tuple[str, ...]:
    raw = re.findall('[A-Za-z0-9]+', str(query or '').casefold())
    result = []
    seen = set()
    for token in raw:
        if token in FILE_NOISE:
            continue
        if token in GENERIC_QUERY_NOISE:
            continue
        if len(token) >= 2:
            keep = True
        elif len(token) == 1 and token.isdigit():
            keep = True
        else:
            keep = False
        if not keep:
            continue
        if token in seen:
            continue
        seen.add(token)
        result.append(token)
    return tuple(result)

def title_identity_coverage(query: str, title: str) -> tuple[float, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    qtokens = query_identity_tokens(query)
    ttokens = title_identity_tokens(title)
    tset = set(ttokens)
    matched = tuple((token for token in qtokens if token in tset))
    if not qtokens:
        coverage = 0.0
    else:
        coverage = len(matched) / len(qtokens)
    return (coverage, qtokens, ttokens, matched)

def token_set_for_candidate(row: Mapping[str, Any]) -> set[str]:
    blob = ' '.join((text(row.get('title')), text(row.get('subject')), text(row.get('excerpt')), text(row.get('chunk_text')), text(row.get('source_path')), text(row.get('file_path'))))
    return set(boundary_tokens(blob))

def title_token_set(row: Mapping[str, Any]) -> set[str]:
    blob = ' '.join((text(row.get('title')), text(row.get('subject'))))
    return set(boundary_tokens(blob))

def exact_feature_rows(query, rows):
    qterms = substantive_terms(query)
    candidate_token_sets = [token_set_for_candidate(row) for row in rows]
    document_frequency = {term: sum((1 for tokens in candidate_token_sets if term in tokens)) for term in qterms}
    total_candidates = max(1, len(rows))
    rarity_weights = {term: 1.0 + math.log((total_candidates + 1.0) / (document_frequency[term] + 1.0)) for term in qterms}
    rarity_denominator = sum(rarity_weights.values()) or 1.0
    numeric_terms = tuple((term for term in qterms if term.isdigit()))
    ranked_features = []
    for ordinal, (row, tokens) in enumerate(zip(rows, candidate_token_sets), start=1):
        title_tokens = title_token_set(row)
        matched = tuple((term for term in qterms if term in tokens))
        coverage = len(matched) / len(qterms)
        rarity_coverage = sum((rarity_weights[term] for term in matched)) / rarity_denominator
        title_matched = tuple((term for term in qterms if term in title_tokens))
        title_coverage = len(title_matched) / len(qterms)
        if numeric_terms:
            numeric_identity = sum((1 for term in numeric_terms if term in title_tokens)) / len(numeric_terms)
        else:
            numeric_identity = 0.0
        if len(rows) <= 1:
            bm25_position = 1.0
        else:
            bm25_position = 1.0 - (ordinal - 1) / (len(rows) - 1)
        shadow_score = 0.4 * coverage + 0.27 * rarity_coverage + 0.23 * title_coverage + 0.07 * numeric_identity + 0.03 * bm25_position
        title = text(row.get('title'))
        full_title_identity, full_query_tokens, full_title_tokens, full_matched_tokens = title_identity_coverage(query, title)
        ranked_features.append({'row': row, 'production_rank': ordinal, 'coverage': coverage, 'rarity_coverage': rarity_coverage, 'title_coverage': title_coverage, 'numeric_identity': numeric_identity, 'bm25_position': bm25_position, 'r7_score': shadow_score, 'full_title_identity': full_title_identity})
    return ranked_features
