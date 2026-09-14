"""Conservative output checks, not a semantic entailment verifier."""
import re

MARKER = re.compile(r'\[(C\d+)\]')
PAGE = re.compile(r'\b(?:pages?|pp?\.)\s*\d', re.I)
ABSENCE = re.compile(r'\b(?:sources?|references?|evidence)\s+(?:do(?:es)?\s+not|don\x27t|doesn\x27t)\s+(?:provide|mention|contain|include|discuss)', re.I)
STOP = set('according local references consider should could would these those their there from with that this your have only when what into about provided sources evidence'.split())

def terms(text):
    return {w.lower() for w in re.findall(r'[A-Za-z]{3,}', text) if w.lower() not in STOP}

def sentences(text):
    # Retain citation parentheses with their sentence; protect decimal values.
    text = re.sub(r'^\[JARVIS/[^\]]+\]\s*', '', text.strip())
    return [s.strip(' -*\t') for s in re.split(r'(?<=[.!?])\s+(?=[A-Z\[(])|\n+', text) if s.strip()]

def output_issue(answer, citations):
    mapping = {c.citation_id: c.excerpt for c in citations}
    for sentence in sentences(answer):
        ids = MARKER.findall(sentence)
        if PAGE.search(sentence):
            return 'page_locator_not_supported_by_citation_schema'
        if ABSENCE.search(sentence):
            return 'unverified_source_absence_claim'
        if not ids:
            # Short headings and the exact evidence limitation are permitted.
            if sentence.endswith(':') and len(sentence.split()) <= 8:
                continue
            if sentence == 'Evidence is relevant but incomplete.':
                continue
            return 'uncited_sentence'
        if any(i not in mapping for i in ids):
            return 'unknown_citation'
        claim = MARKER.sub('', sentence)
        evidence = ' '.join(mapping[i] for i in ids)
        a, b = terms(claim), terms(evidence)
        if not a or len(a & b) / len(a) < .45:
            return 'weak_sentence_support'
        numbers = set(re.findall(r'\b\d+(?:[.,]\d+)*\b', claim))
        if not numbers <= set(re.findall(r'\b\d+(?:[.,]\d+)*\b', evidence)):
            return 'unsupported_number'
    return None

def source_excerpt_answer(plan):
    """Quote short, query-matching source sentences; never invent a paraphrase."""
    query_terms = terms(plan.query)
    lines = ['Relevant passages from your local references:']
    included = []
    for citation in plan.citations:
        # Repair PDF line-wrap hyphens, then whitespace; words are otherwise retained.
        text = re.sub(r'(?<=\w)-\s*\n\s*(?=\w)', '', citation.excerpt)
        blocks = re.split(r'\n\s*\n', text)
        candidates = []
        for block in blocks:
            flat = ' '.join(block.split())
            for sentence in sentences(flat):
                if not 35 <= len(sentence) <= 650 or not sentence.endswith(('.', '!')):
                    continue
                overlap = len(terms(sentence) & query_terms)
                if overlap >= 2:
                    candidates.append((overlap, sentence))
        selected = sorted(candidates, key=lambda x: -x[0])[:2]
        if selected:
            included.append(citation)
            for _, sentence in selected:
                lines.append(f'\n> {sentence}\n\n[{citation.citation_id}]')
    if not included:
        return 'I found qualified references, but could not produce a reliably supported answer. Please narrow the question.'
    lines.append('\nSources:')
    for c in included:
        lines.append(f'- [{c.citation_id}] {c.title}')
    lines.append('\nThese are source excerpts, not a complete or location-specific plan.')
    if plan.conflicts:
        lines.append('Potential conflicts between sources require review.')
    return '\n'.join(lines)
