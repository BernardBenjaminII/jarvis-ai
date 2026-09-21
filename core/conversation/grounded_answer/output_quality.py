"""Conservative output checks, not a semantic entailment verifier."""
import re

MARKER = re.compile(r'\[(C\d+)\]')
PAGE = re.compile(r'\b(?:pages?|pp?\.)\s*\d', re.I)
ABSENCE = re.compile(r'\b(?:sources?|references?|evidence)\s+(?:do(?:es)?\s+not|don\x27t|doesn\x27t)\s+(?:provide|mention|contain|include|discuss)', re.I)
STOP = set('according local references consider should could would these those their there from with that this your have only when what into about provided sources evidence'.split())

def terms(text):
    return {w.lower() for w in re.findall(r'[A-Za-z]{3,}', text) if w.lower() not in STOP}

def sentences(text):
    """Split prose while preserving numbered-list items as sentences."""
    text = re.sub(
        r'^\[JARVIS/[^\]]+\]\s*',
        '',
        str(text or '').strip(),
    )

    # Numbered list items often arrive on one line:
    #
    #   1. First item. 2. Second item.
    #
    # Protect list ordinals before ordinary sentence splitting so ``1.``
    # never becomes an independent sentence.
    ordinal_token = "__JARVIS_ORDINAL_{}__"

    ordinals = []

    def protect_ordinal(match):
        ordinals.append(match.group(1))
        return ordinal_token.format(len(ordinals) - 1)

    protected = re.sub(
        r'(?<!\d)(\d+)\.\s+(?=[A-Z])',
        protect_ordinal,
        text,
    )

    parts = [
        part.strip(' -*\t')
        for part in re.split(
            r'(?<=[.!?])\s+(?=[A-Z\[(])|\n+',
            protected,
        )
        if part.strip()
    ]

    restored = []

    for part in parts:
        for index, number in enumerate(ordinals):
            part = part.replace(
                ordinal_token.format(index),
                f"{number}. ",
            )

        restored.append(part.strip())

    return restored


def output_issue_detail(answer, citations):
    """Return structured details for the first output-quality violation."""
    mapping = {c.citation_id: c.excerpt for c in citations}

    for index, sentence in enumerate(sentences(answer), start=1):
        ids = MARKER.findall(sentence)

        def issue(reason, **extra):
            return {
                "reason": reason,
                "sentence_index": index,
                "sentence": sentence,
                "citation_ids": ids,
                **extra,
            }

        if PAGE.search(sentence):
            return issue("page_locator_not_supported_by_citation_schema")

        if ABSENCE.search(sentence):
            return issue("unverified_source_absence_claim")

        if not ids:
            # A colon-terminated lead-in or heading may organize the answer
            # without asserting an independently checkable factual claim.
            # Keep the exemption narrow: numbered statements and source-
            # absence claims remain subject to validation.
            if (
                sentence.endswith(":")
                and not re.search(r"\\b\\d+(?:[.,]\\d+)*\\b", sentence)
                and not ABSENCE.search(sentence)
            ):
                continue

            if sentence == "Evidence is relevant but incomplete.":
                continue

            return issue("uncited_sentence")

        unknown = [i for i in ids if i not in mapping]
        if unknown:
            return issue(
                "unknown_citation",
                unknown_citation_ids=unknown,
            )

        claim = MARKER.sub("", sentence)
        evidence = " ".join(mapping[i] for i in ids)

        a = terms(claim)
        b = terms(evidence)

        overlap_ratio = (
            len(a & b) / len(a)
            if a
            else 0.0
        )

        if not a or overlap_ratio < .45:
            return issue(
                "weak_sentence_support",
                term_overlap_ratio=overlap_ratio,
            )

        numbers = set(
            re.findall(r"\\b\\d+(?:[.,]\\d+)*\\b", claim)
        )
        evidence_numbers = set(
            re.findall(r"\\b\\d+(?:[.,]\\d+)*\\b", evidence)
        )

        unsupported_numbers = sorted(numbers - evidence_numbers)

        if unsupported_numbers:
            return issue(
                "unsupported_number",
                unsupported_numbers=unsupported_numbers,
            )

    return None


def output_issue(answer, citations):
    """Backward-compatible reason-only output-quality check."""
    detail = output_issue_detail(answer, citations)
    return detail["reason"] if detail else None

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
