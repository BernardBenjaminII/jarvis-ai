from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from dev.as1.identity import (
    IdentityFingerprint,
    IdentityMatch,
    IdentityVerdict,
    hamming64,
    normalize_text,
    normalize_title,
    normalized_content_sha256,
    ratio_similarity,
    simhash64,
    structural_score,
)


@dataclass(frozen=True)
class RuntimeCandidate:
    id: int
    file_path: str
    sha256: str
    title: str
    content_chars: int


class TargetedRuntimeIdentityResolver:
    """
    Pack 2-R2-R1.

    No whole-runtime Python index.

    Every lookup is performed directly against SQLite and
    returns only a bounded number of candidate rows.
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        maximum_candidates: int = 6,
        maximum_content_chars: int = 4_000_000,
    ):
        self.connection = connection
        self.maximum_candidates = maximum_candidates
        self.maximum_content_chars = maximum_content_chars

        self.content_rows_loaded = 0
        self.content_rows_skipped = 0

    # --------------------------------------------------------
    # Layer 1 — exact SHA
    # --------------------------------------------------------

    def exact_sha(
        self,
        digest: str | None,
    ) -> RuntimeCandidate | None:

        if not digest:
            return None

        row = self.connection.execute(
            """
            SELECT
                id,
                file_path,
                sha256,
                title,
                content_chars
            FROM runtime_documents
            WHERE sha256 = ?
            LIMIT 1
            """,
            (digest,),
        ).fetchone()

        if row is None:
            return None

        return self._candidate(row)

    # --------------------------------------------------------
    # Candidate retrieval
    # --------------------------------------------------------

    def candidates(
        self,
        fingerprint: IdentityFingerprint,
    ) -> list[RuntimeCandidate]:

        title = fingerprint.normalized_title

        tokens = [
            token
            for token in title.split()
            if len(token) >= 3
        ]

        # Prefer the longest/most-specific title tokens.
        tokens.sort(
            key=lambda value: (
                len(value),
                value,
            ),
            reverse=True,
        )

        tokens = tokens[:4]

        conditions = []
        parameters: list[object] = []

        for token in tokens:
            conditions.append(
                "lower(title) LIKE ?"
            )
            parameters.append(
                f"%{token.casefold()}%"
            )

        # If the title gives us nothing useful, do NOT scan
        # runtime_documents. Identity remains unresolved until
        # the persistent fingerprint index exists.
        if not conditions:
            return []

        where = " OR ".join(
            conditions
        )

        # content_chars is deliberately only a ranking hint.
        #
        # We do not require raw runtime length to equal
        # normalized candidate length.
        target = (
            fingerprint.normalized_chars
            or 0
        )

        sql = f"""
            SELECT
                id,
                file_path,
                sha256,
                title,
                content_chars
            FROM runtime_documents
            WHERE ({where})
            ORDER BY
                CASE
                    WHEN ? > 0
                     AND content_chars > 0
                    THEN ABS(content_chars - ?)
                    ELSE 9223372036854775807
                END ASC,
                id ASC
            LIMIT ?
        """

        parameters.extend(
            [
                target,
                target,
                self.maximum_candidates,
            ]
        )

        rows = self.connection.execute(
            sql,
            tuple(parameters),
        ).fetchall()

        return [
            self._candidate(row)
            for row in rows
        ]

    def _candidate(
        self,
        row,
    ) -> RuntimeCandidate:

        return RuntimeCandidate(
            id=int(row["id"]),
            file_path=str(row["file_path"]),
            sha256=str(row["sha256"]),
            title=str(row["title"]),
            content_chars=int(
                row["content_chars"]
            ),
        )

    # --------------------------------------------------------
    # Bounded content fetch
    # --------------------------------------------------------

    def content_text(
        self,
        candidate: RuntimeCandidate,
    ) -> str | None:

        if (
            candidate.content_chars
            > self.maximum_content_chars
        ):
            self.content_rows_skipped += 1
            return None

        row = self.connection.execute(
            """
            SELECT content_text
            FROM runtime_documents
            WHERE id = ?
            LIMIT 1
            """,
            (candidate.id,),
        ).fetchone()

        if row is None:
            return None

        text = row["content_text"]

        if text is None:
            return None

        self.content_rows_loaded += 1

        return str(text)

    # --------------------------------------------------------
    # Identity resolution
    # --------------------------------------------------------

    def resolve(
        self,
        *,
        fingerprint: IdentityFingerprint,
        candidate_text: str | None,
    ) -> IdentityMatch:

        # ====================================================
        # 1. EXACT BYTE IDENTITY
        # ====================================================

        exact = self.exact_sha(
            fingerprint.sha256
        )

        if exact is not None:
            return IdentityMatch(
                verdict=(
                    IdentityVerdict.EXACT_DUPLICATE
                ),
                candidate_path=fingerprint.path,
                matched_path=exact.file_path,
                layer="sha256_sql",
                confidence=1.0,
                reason=(
                    "Targeted SQLite SHA-256 lookup found "
                    "an existing runtime document."
                ),
                exact_sha_match=True,
            )

        shortlist = self.candidates(
            fingerprint
        )

        best_near = None
        best_structural = None

        # ====================================================
        # 2. CONTENT IDENTITY
        # ====================================================

        if (
            candidate_text
            and fingerprint.normalized_content_sha256
        ):
            for runtime_candidate in shortlist:

                existing_text = self.content_text(
                    runtime_candidate
                )

                if not existing_text:
                    continue

                existing_sha, existing_chars = (
                    normalized_content_sha256(
                        existing_text
                    )
                )

                if (
                    existing_sha
                    == fingerprint.normalized_content_sha256
                ):
                    return IdentityMatch(
                        verdict=(
                            IdentityVerdict.CONTENT_DUPLICATE
                        ),
                        candidate_path=fingerprint.path,
                        matched_path=(
                            runtime_candidate.file_path
                        ),
                        layer="normalized_content_sql",
                        confidence=0.995,
                        reason=(
                            "Bounded runtime candidate "
                            "normalizes to identical content."
                        ),
                        content_hash_match=True,
                    )

                # ============================================
                # 3. NEAR DUPLICATE
                # ============================================

                left = fingerprint.simhash64
                right = simhash64(
                    existing_text
                )

                if (
                    left is not None
                    and right is not None
                ):
                    distance = hamming64(
                        left,
                        right,
                    )

                    length_ratio = ratio_similarity(
                        fingerprint.normalized_chars,
                        existing_chars,
                    )

                    if (
                        distance <= 3
                        and length_ratio >= 0.98
                        and (
                            fingerprint.normalized_chars
                            or 0
                        ) >= 500
                    ):
                        confidence = (
                            0.98
                            - distance * 0.03
                        )

                        result = IdentityMatch(
                            verdict=(
                                IdentityVerdict.NEAR_DUPLICATE
                            ),
                            candidate_path=fingerprint.path,
                            matched_path=(
                                runtime_candidate.file_path
                            ),
                            layer="simhash64_sql",
                            confidence=confidence,
                            reason=(
                                "Bounded candidate has very "
                                "small SimHash distance and "
                                "nearly identical normalized "
                                "content length."
                            ),
                            simhash_distance=distance,
                        )

                        if (
                            best_near is None
                            or result.confidence
                            > best_near.confidence
                        ):
                            best_near = result

        if best_near is not None:
            return best_near

        # ====================================================
        # 4. STRUCTURAL MATCH
        # ====================================================

        for runtime_candidate in shortlist:

            try:
                existing_size = (
                    Path(
                        runtime_candidate.file_path
                    )
                    .stat()
                    .st_size
                )
            except OSError:
                existing_size = None

            score = structural_score(
                candidate_title=(
                    fingerprint.normalized_title
                ),
                candidate_size=(
                    fingerprint.size_bytes
                ),
                candidate_chars=(
                    fingerprint.normalized_chars
                ),
                existing_title=(
                    runtime_candidate.title
                ),
                existing_size=existing_size,
                existing_chars=(
                    runtime_candidate.content_chars
                ),
            )

            if score >= 0.90:
                result = IdentityMatch(
                    verdict=(
                        IdentityVerdict.STRUCTURAL_MATCH
                    ),
                    candidate_path=fingerprint.path,
                    matched_path=(
                        runtime_candidate.file_path
                    ),
                    layer="structure_sql",
                    confidence=score,
                    reason=(
                        "Bounded SQL candidate has strong "
                        "structural similarity. Preserve as "
                        "a possible revision or variant."
                    ),
                    structural_score=score,
                )

                if (
                    best_structural is None
                    or result.confidence
                    > best_structural.confidence
                ):
                    best_structural = result

        if best_structural is not None:
            return best_structural

        # ====================================================
        # IMPORTANT:
        #
        # A bounded shortlist that found no match does NOT
        # prove global distinctness across 89,330 documents.
        #
        # Therefore targeted SQL mode returns UNRESOLVED
        # rather than manufacturing DISTINCT.
        # ====================================================

        return IdentityMatch(
            verdict=IdentityVerdict.UNRESOLVED,
            candidate_path=fingerprint.path,
            matched_path=None,
            layer="bounded_sql",
            confidence=0.50,
            reason=(
                "No identity collision was found in the "
                "bounded targeted SQL candidate set. "
                "Global DISTINCT requires the persistent "
                "fingerprint index."
            ),
        )
