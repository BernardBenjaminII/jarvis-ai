from __future__ import annotations

import re

FILE_NOISE = {
    "html",
    "htm",
    "pdf",
    "txt",
    "doc",
    "docx",
    "xml",
    "json",
    "csv",
}

GENERIC_QUERY_NOISE = {
    "file",
    "document",
    "page",
    "chapter",
}

def title_identity_tokens(
    value: str,
) -> tuple[str, ...]:

    raw = re.findall(
        r"[A-Za-z0-9]+",
        str(value or "").casefold(),
    )

    result = []
    seen = set()


    for token in raw:

        if token in FILE_NOISE:
            continue


        if len(token) >= 2:

            keep = True

        elif (
            len(token) == 1
            and
            token.isdigit()
        ):

            keep = True

        else:

            keep = False


        if not keep:
            continue

        if token in seen:
            continue

        seen.add(
            token
        )

        result.append(
            token
        )


    return tuple(
        result
    )

def query_identity_tokens(
    query: str,
) -> tuple[str, ...]:

    raw = re.findall(
        r"[A-Za-z0-9]+",
        str(query or "").casefold(),
    )

    result = []
    seen = set()


    for token in raw:

        if token in FILE_NOISE:
            continue

        if token in GENERIC_QUERY_NOISE:
            continue


        if len(token) >= 2:

            keep = True

        elif (
            len(token) == 1
            and
            token.isdigit()
        ):

            keep = True

        else:

            keep = False


        if not keep:
            continue

        if token in seen:
            continue

        seen.add(
            token
        )

        result.append(
            token
        )


    return tuple(
        result
    )

def title_identity_coverage(
    query: str,
    title: str,
) -> tuple[
    float,
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
]:

    qtokens = query_identity_tokens(
        query
    )

    ttokens = title_identity_tokens(
        title
    )

    tset = set(
        ttokens
    )


    matched = tuple(
        token
        for token in qtokens
        if token in tset
    )


    if not qtokens:

        coverage = 0.0

    else:

        coverage = (
            len(
                matched
            )
            /
            len(
                qtokens
            )
        )


    return (
        coverage,
        qtokens,
        ttokens,
        matched,
    )

def r7_exact_feature_vector(
    query: str,
    qterms: tuple[str, ...],
    matched: tuple[str, ...],
    rarity_weights: dict[str, float],
    rarity_denominator: float,
    title_tokens: set[str],
    numeric_terms: tuple[str, ...],
    ordinal: int,
    row_count: int,
    title: str,
):

    coverage = (
        len(matched)
        /
        len(qterms)
    )

    rarity_coverage = (
        sum(
            rarity_weights[term]
            for term in matched
        )
        /
        rarity_denominator
    )

    title_matched = tuple(
        term
        for term in qterms
        if term in title_tokens
    )

    title_coverage = (
        len(title_matched)
        /
        len(qterms)
    )

    if numeric_terms:
        numeric_identity = (
            sum(
                1
                for term in numeric_terms
                if term in title_tokens
            )
            /
            len(numeric_terms)
        )
    else:
        numeric_identity = 0.0

    if row_count <= 1:
        bm25_position = 1.0
    else:
        bm25_position = (
            1.0
            -
            (ordinal - 1)
            /
            (row_count - 1)
        )

    shadow_score = (
        0.40 * coverage
        + 0.27 * rarity_coverage
        + 0.23 * title_coverage
        + 0.07 * numeric_identity
        + 0.03 * bm25_position
    )

    (
        full_title_identity,
        full_query_tokens,
        full_title_tokens,
        full_matched_tokens,
    ) = title_identity_coverage(
        query,
        title,
    )

    return {
        'coverage': coverage,
        'rarity_coverage': rarity_coverage,
        'title_coverage': title_coverage,
        'numeric_identity': numeric_identity,
        'bm25_position': bm25_position,
        'shadow_score': shadow_score,
        'full_title_identity': full_title_identity,
        'full_query_tokens': full_query_tokens,
        'full_title_tokens': full_title_tokens,
        'full_matched_tokens': full_matched_tokens,
    }
