from __future__ import annotations

import hashlib
import html
import re
import sqlite3
import unicodedata

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


class IdentityVerdict(str, Enum):
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    CONTENT_DUPLICATE = "CONTENT_DUPLICATE"
    NEAR_DUPLICATE = "NEAR_DUPLICATE"
    STRUCTURAL_MATCH = "STRUCTURAL_MATCH"
    DISTINCT = "DISTINCT"
    REVIEW = "REVIEW"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class IdentityFingerprint:
    path: str
    sha256: str | None
    normalized_content_sha256: str | None
    normalized_chars: int | None
    simhash64: int | None
    normalized_title: str
    size_bytes: int


@dataclass(frozen=True)
class IdentityMatch:
    verdict: IdentityVerdict
    candidate_path: str
    matched_path: str | None
    layer: str
    confidence: float
    reason: str

    exact_sha_match: bool = False
    content_hash_match: bool = False
    simhash_distance: int | None = None
    structural_score: float | None = None


TEXTUAL_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".rst",
    ".html",
    ".htm",
    ".xml",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".toml",
    ".csv",
    ".tsv",
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".css",
    ".scss",
    ".sql",
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".c",
    ".h",
    ".hpp",
    ".cpp",
    ".cc",
    ".java",
    ".go",
    ".rs",
}


TITLE_STOPWORDS = {
    "a",
    "an",
    "and",
    "book",
    "document",
    "edition",
    "file",
    "manual",
    "of",
    "pdf",
    "the",
    "txt",
    "version",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def normalize_title(value: str) -> str:
    value = Path(value).stem

    value = unicodedata.normalize(
        "NFKC",
        value,
    ).casefold()

    value = re.sub(
        r"[_\-.]+",
        " ",
        value,
    )

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    tokens = [
        token
        for token in value.split()
        if token not in TITLE_STOPWORDS
    ]

    return " ".join(tokens)


def normalize_text(text: str) -> str:
    """
    Deterministic normalization for document identity.

    This is intentionally stronger than retrieval normalization
    but weaker than semantic rewriting.

    Formatting differences should disappear.
    Meaningful textual differences should remain.
    """

    text = unicodedata.normalize(
        "NFKC",
        text,
    )

    text = html.unescape(text)

    # Normalize line endings.
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove zero-width / common invisible characters.
    text = (
        text
        .replace("\u200b", "")
        .replace("\u200c", "")
        .replace("\u200d", "")
        .replace("\ufeff", "")
    )

    # HTML-ish tags are formatting, not content identity.
    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    text = text.casefold()

    # Normalize punctuation boundaries.
    text = re.sub(
        r"[^\w\s]",
        " ",
        text,
        flags=re.UNICODE,
    )

    # Collapse whitespace.
    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


def normalized_content_sha256(
    text: str,
) -> tuple[str, int]:

    normalized = normalize_text(text)

    digest = hashlib.sha256(
        normalized.encode(
            "utf-8",
            errors="ignore",
        )
    ).hexdigest()

    return digest, len(normalized)


def _tokens(
    normalized_text: str,
) -> list[str]:

    return [
        token
        for token in normalized_text.split()
        if len(token) >= 2
    ]


def simhash64(text: str) -> int | None:
    normalized = normalize_text(text)

    tokens = _tokens(normalized)

    if not tokens:
        return None

    vector = [0] * 64

    # Use token trigrams where possible. This makes the
    # fingerprint substantially more resistant to common
    # repeated words than raw token hashing.
    if len(tokens) >= 3:
        features = (
            " ".join(tokens[i:i + 3])
            for i in range(len(tokens) - 2)
        )
    else:
        features = iter(tokens)

    used = 0

    for feature in features:
        used += 1

        digest = hashlib.blake2b(
            feature.encode(
                "utf-8",
                errors="ignore",
            ),
            digest_size=8,
        ).digest()

        value = int.from_bytes(
            digest,
            "big",
        )

        for bit in range(64):
            if value & (1 << bit):
                vector[bit] += 1
            else:
                vector[bit] -= 1

    if used == 0:
        return None

    output = 0

    for bit, score in enumerate(vector):
        if score >= 0:
            output |= 1 << bit

    return output


def hamming64(
    left: int,
    right: int,
) -> int:

    return (
        left ^ right
    ).bit_count()


def title_similarity(
    left: str,
    right: str,
) -> float:

    left_tokens = set(
        normalize_title(left).split()
    )

    right_tokens = set(
        normalize_title(right).split()
    )

    if not left_tokens or not right_tokens:
        return 0.0

    intersection = len(
        left_tokens & right_tokens
    )

    union = len(
        left_tokens | right_tokens
    )

    if union == 0:
        return 0.0

    return intersection / union


def ratio_similarity(
    left: int | None,
    right: int | None,
) -> float:

    if not left or not right:
        return 0.0

    larger = max(left, right)
    smaller = min(left, right)

    if larger <= 0:
        return 0.0

    return smaller / larger


def structural_score(
    *,
    candidate_title: str,
    candidate_size: int,
    candidate_chars: int | None,
    existing_title: str,
    existing_size: int | None,
    existing_chars: int | None,
) -> float:

    title_score = title_similarity(
        candidate_title,
        existing_title,
    )

    size_score = ratio_similarity(
        candidate_size,
        existing_size,
    )

    char_score = ratio_similarity(
        candidate_chars,
        existing_chars,
    )

    # Text length is more useful than binary file size where
    # it exists.
    if candidate_chars and existing_chars:
        return (
            title_score * 0.50
            + char_score * 0.40
            + size_score * 0.10
        )

    return (
        title_score * 0.70
        + size_score * 0.30
    )


def read_direct_text(
    path: Path,
    max_bytes: int = 32 * 1024 * 1024,
) -> str | None:

    if path.suffix.casefold() not in TEXTUAL_EXTENSIONS:
        return None

    try:
        size = path.stat().st_size
    except OSError:
        return None

    if size > max_bytes:
        return None

    try:
        return path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except OSError:
        return None


class LegacyTextProvider:
    """
    Read-only adapter for legacy extracted text.

    JARVIS has had more than one document schema. This adapter
    intentionally discovers the relation rather than hardcoding
    one historical layout.
    """

    TEXT_COLUMNS = (
        "content_text",
        "extracted_text",
        "document_text",
        "text",
        "content",
        "body",
    )

    PATH_COLUMNS = (
        "file_path",
        "document_path",
        "path",
        "source_path",
    )

    ID_COLUMNS = (
        "document_id",
        "doc_id",
    )

    ORDER_COLUMNS = (
        "page_number",
        "page",
        "page_index",
        "sequence",
        "chunk_index",
        "id",
    )

    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection

    def _tables(self) -> set[str]:
        return {
            str(row[0])
            for row in self.connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                """
            )
        }

    def _columns(
        self,
        table: str,
    ) -> list[str]:

        return [
            str(row[1])
            for row in self.connection.execute(
                f'PRAGMA table_info("{table}")'
            )
        ]

    @staticmethod
    def _first(
        preferred: Iterable[str],
        available: Iterable[str],
    ) -> str | None:

        available_set = set(available)

        for name in preferred:
            if name in available_set:
                return name

        return None

    def get_text(
        self,
        path: Path,
    ) -> str | None:

        tables = self._tables()

        if "document_text" not in tables:
            return None

        dt_cols = self._columns(
            "document_text"
        )

        text_col = self._first(
            self.TEXT_COLUMNS,
            dt_cols,
        )

        if text_col is None:
            return None

        # First try direct path ownership.
        dt_path_col = self._first(
            self.PATH_COLUMNS,
            dt_cols,
        )

        order_col = self._first(
            self.ORDER_COLUMNS,
            dt_cols,
        )

        order_sql = (
            f' ORDER BY "{order_col}"'
            if order_col
            else ""
        )

        if dt_path_col:
            rows = self.connection.execute(
                f'''
                SELECT "{text_col}"
                FROM document_text
                WHERE "{dt_path_col}"=?
                {order_sql}
                ''',
                (str(path),),
            ).fetchall()

            text = "\n".join(
                str(row[0])
                for row in rows
                if row[0]
            )

            if text.strip():
                return text

        # Otherwise resolve document ID through documents.
        if "documents" not in tables:
            return None

        doc_cols = self._columns(
            "documents"
        )

        doc_path_col = self._first(
            self.PATH_COLUMNS,
            doc_cols,
        )

        if doc_path_col is None:
            return None

        doc_pk = (
            "id"
            if "id" in doc_cols
            else None
        )

        if doc_pk is None:
            return None

        dt_id_col = self._first(
            self.ID_COLUMNS,
            dt_cols,
        )

        if dt_id_col is None:
            return None

        document = self.connection.execute(
            f'''
            SELECT "{doc_pk}"
            FROM documents
            WHERE "{doc_path_col}"=?
            LIMIT 1
            ''',
            (str(path),),
        ).fetchone()

        if document is None:
            return None

        document_id = document[0]

        rows = self.connection.execute(
            f'''
            SELECT "{text_col}"
            FROM document_text
            WHERE "{dt_id_col}"=?
            {order_sql}
            ''',
            (document_id,),
        ).fetchall()

        text = "\n".join(
            str(row[0])
            for row in rows
            if row[0]
        )

        if text.strip():
            return text

        return None


def get_candidate_text(
    *,
    path: Path,
    legacy_text: LegacyTextProvider | None,
) -> str | None:

    direct = read_direct_text(path)

    if direct and direct.strip():
        return direct

    if legacy_text is not None:
        extracted = legacy_text.get_text(path)

        if extracted and extracted.strip():
            return extracted

    return None


def build_fingerprint(
    *,
    path: Path,
    sha256: str | None,
    text: str | None,
) -> IdentityFingerprint:

    try:
        size = path.stat().st_size
    except OSError:
        size = 0

    normalized_sha = None
    normalized_chars = None
    simhash = None

    if text and text.strip():
        normalized_sha, normalized_chars = (
            normalized_content_sha256(text)
        )

        simhash = simhash64(text)

    return IdentityFingerprint(
        path=str(path),
        sha256=sha256,
        normalized_content_sha256=normalized_sha,
        normalized_chars=normalized_chars,
        simhash64=simhash,
        normalized_title=normalize_title(
            path.name
        ),
        size_bytes=size,
    )


class RuntimeIdentityIndex:
    """
    Bounded read-only identity lookup over runtime_documents.

    Pack 2-R1 intentionally separates:

        candidate retrieval
            from
        identity determination

    Shortlisting may be permissive.

    Duplicate verdicts remain strict and are made only by
    subsequent deterministic identity layers.
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
    ):
        self.connection = connection

        self.rows: list[dict] = []

        self.by_sha: dict[
            str,
            list[dict],
        ] = {}

        self.by_title: dict[
            str,
            list[dict],
        ] = {}

        self.by_title_token: dict[
            str,
            list[dict],
        ] = {}

        self._load_metadata()

    def _load_metadata(self):
        available = {
            str(row[1])
            for row in self.connection.execute(
                'PRAGMA table_info("runtime_documents")'
            )
        }

        wanted = [
            name
            for name in (
                "id",
                "file_path",
                "sha256",
                "title",
                "content_chars",
            )
            if name in available
        ]

        sql = (
            "SELECT "
            + ", ".join(
                f'"{name}"'
                for name in wanted
            )
            + " FROM runtime_documents"
        )

        sha_index: dict[
            str,
            list[dict],
        ] = {}

        title_index: dict[
            str,
            list[dict],
        ] = {}

        token_index: dict[
            str,
            list[dict],
        ] = {}

        for row in self.connection.execute(sql):
            item = dict(row)

            runtime_path = str(
                item.get("file_path") or ""
            )

            if not runtime_path:
                continue

            title = str(
                item.get("title")
                or Path(runtime_path).name
            )

            normalized = normalize_title(title)

            item["normalized_title"] = normalized
            item["title_tokens"] = tuple(
                sorted(
                    set(
                        normalized.split()
                    )
                )
            )

            self.rows.append(item)

            digest = str(
                item.get("sha256") or ""
            )

            if digest:
                sha_index.setdefault(
                    digest,
                    [],
                ).append(item)

            if normalized:
                title_index.setdefault(
                    normalized,
                    [],
                ).append(item)

            for token in item["title_tokens"]:
                # One-character tokens are usually noise.
                if len(token) < 2:
                    continue

                token_index.setdefault(
                    token,
                    [],
                ).append(item)

        self.by_sha = sha_index
        self.by_title = title_index
        self.by_title_token = token_index

    def exact_sha_matches(
        self,
        digest: str | None,
    ) -> list[dict]:

        if not digest:
            return []

        return list(
            self.by_sha.get(
                digest,
                (),
            )
        )

    @staticmethod
    def _char_ratio_hint(
        candidate_chars: int | None,
        runtime_chars: object,
    ) -> float:
        """
        Runtime content_chars may describe raw extracted text
        while candidate normalized_chars describes normalized
        text.

        Therefore this value is ONLY a retrieval hint.

        It must never determine duplicate identity.
        """

        if not candidate_chars:
            return 0.0

        try:
            runtime_value = int(runtime_chars)
        except (TypeError, ValueError):
            return 0.0

        if runtime_value <= 0:
            return 0.0

        return ratio_similarity(
            candidate_chars,
            runtime_value,
        )

    def shortlist(
        self,
        *,
        fingerprint: IdentityFingerprint,
        maximum: int = 40,
    ) -> list[dict]:
        """
        Build a bounded candidate set.

        Pack 2 original defect:
            exact normalized title OR >=97% length agreement

        could exclude a true content duplicate before content
        comparison.

        Pack 2-R1 retrieval strategy:

        1. exact normalized-title candidates;
        2. title-token candidates;
        3. loose content-length candidates;
        4. rank all retrieved candidates;
        5. actual identity layers make the verdict.

        No shortlist signal is itself proof of duplication.
        """

        chosen: dict[int, dict] = {}

        candidate_title = (
            fingerprint.normalized_title
        )

        candidate_tokens = {
            token
            for token in candidate_title.split()
            if len(token) >= 2
        }

        # ----------------------------------------------------
        # 1. Exact normalized title.
        # ----------------------------------------------------

        for row in self.by_title.get(
            candidate_title,
            (),
        ):
            row_id = row.get("id")

            if row_id is not None:
                chosen[int(row_id)] = row

        # ----------------------------------------------------
        # 2. Title token retrieval.
        #
        # "urban operations variant"
        # can now retrieve
        # "urban operations"
        # ----------------------------------------------------

        token_hits: dict[int, int] = {}

        for token in candidate_tokens:
            for row in self.by_title_token.get(
                token,
                (),
            ):
                row_id = row.get("id")

                if row_id is None:
                    continue

                row_id = int(row_id)

                token_hits[row_id] = (
                    token_hits.get(row_id, 0)
                    + 1
                )

                chosen.setdefault(
                    row_id,
                    row,
                )

        # ----------------------------------------------------
        # 3. Loose content-length retrieval.
        #
        # This is intentionally permissive because raw
        # content_chars and normalized_chars are different
        # measurements.
        #
        # We cap additions aggressively.
        # ----------------------------------------------------

        target_chars = (
            fingerprint.normalized_chars
        )

        length_added = 0
        length_cap = max(
            maximum * 4,
            100,
        )

        if target_chars:
            for row in self.rows:
                ratio = self._char_ratio_hint(
                    target_chars,
                    row.get("content_chars"),
                )

                # Retrieval threshold only.
                #
                # Identity thresholds remain much stricter.
                if ratio < 0.80:
                    continue

                row_id = row.get("id")

                if row_id is None:
                    continue

                chosen.setdefault(
                    int(row_id),
                    row,
                )

                length_added += 1

                if length_added >= length_cap:
                    break

        # ----------------------------------------------------
        # Rank the retrieved candidates.
        # ----------------------------------------------------

        ranked: list[
            tuple[float, dict]
        ] = []

        for row in chosen.values():
            runtime_title = str(
                row.get("normalized_title")
                or ""
            )

            runtime_tokens = set(
                row.get("title_tokens")
                or ()
            )

            title_score = title_similarity(
                candidate_title,
                runtime_title,
            )

            if (
                candidate_tokens
                and runtime_tokens
            ):
                shared = len(
                    candidate_tokens
                    & runtime_tokens
                )

                token_recall = (
                    shared
                    / max(
                        1,
                        min(
                            len(candidate_tokens),
                            len(runtime_tokens),
                        ),
                    )
                )
            else:
                token_recall = 0.0

            char_score = (
                self._char_ratio_hint(
                    fingerprint.normalized_chars,
                    row.get("content_chars"),
                )
            )

            # Retrieval score only.
            score = (
                title_score * 0.50
                + token_recall * 0.35
                + char_score * 0.15
            )

            ranked.append(
                (score, row)
            )

        ranked.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            row
            for _, row
            in ranked[:maximum]
        ]

    def get_content_text(
        self,
        document_id: int,
    ) -> str | None:
        """
        Fetch ONE shortlisted runtime document's content.

        The runtime content corpus is never bulk-loaded.
        """

        row = self.connection.execute(
            """
            SELECT content_text
            FROM runtime_documents
            WHERE id=?
            LIMIT 1
            """,
            (document_id,),
        ).fetchone()

        if row is None:
            return None

        value = row[0]

        if value is None:
            return None

        return str(value)


class LayeredIdentityResolver:
    def __init__(
        self,
        runtime_index: RuntimeIdentityIndex,
    ):
        self.runtime = runtime_index

    def resolve(
        self,
        *,
        fingerprint: IdentityFingerprint,
        candidate_text: str | None,
        maximum_shortlist: int = 40,
    ) -> IdentityMatch:

        candidate_path = fingerprint.path

        # ====================================================
        # LAYER 1 — EXACT BYTE IDENTITY
        # ====================================================

        exact = self.runtime.exact_sha_matches(
            fingerprint.sha256
        )

        if exact:
            match = exact[0]

            return IdentityMatch(
                verdict=(
                    IdentityVerdict.EXACT_DUPLICATE
                ),
                candidate_path=candidate_path,
                matched_path=str(
                    match.get("file_path")
                ),
                layer="sha256",
                confidence=1.0,
                reason=(
                    "Byte-for-byte SHA-256 identity with "
                    "an existing runtime document."
                ),
                exact_sha_match=True,
            )

        shortlist = self.runtime.shortlist(
            fingerprint=fingerprint,
            maximum=maximum_shortlist,
        )

        best_near = None
        best_structural = None

        # ====================================================
        # LAYERS 2 + 3
        #
        # Only fetch runtime content for a bounded shortlist.
        # ====================================================

        if (
            candidate_text
            and fingerprint.normalized_content_sha256
        ):
            candidate_norm = normalize_text(
                candidate_text
            )

            for row in shortlist:
                document_id = row.get("id")

                if document_id is None:
                    continue

                existing_text = (
                    self.runtime.get_content_text(
                        int(document_id)
                    )
                )

                if not existing_text:
                    continue

                existing_sha, existing_chars = (
                    normalized_content_sha256(
                        existing_text
                    )
                )

                # --------------------------------------------
                # LAYER 2 — NORMALIZED CONTENT IDENTITY
                # --------------------------------------------

                if (
                    existing_sha
                    == fingerprint.normalized_content_sha256
                ):
                    return IdentityMatch(
                        verdict=(
                            IdentityVerdict.CONTENT_DUPLICATE
                        ),
                        candidate_path=candidate_path,
                        matched_path=str(
                            row.get("file_path")
                        ),
                        layer="normalized_content",
                        confidence=0.995,
                        reason=(
                            "Different byte representation "
                            "normalizes to identical textual "
                            "content."
                        ),
                        content_hash_match=True,
                    )

                # --------------------------------------------
                # LAYER 3 — NEAR DUPLICATE
                # --------------------------------------------

                existing_simhash = simhash64(
                    existing_text
                )

                if (
                    fingerprint.simhash64 is not None
                    and existing_simhash is not None
                ):
                    distance = hamming64(
                        fingerprint.simhash64,
                        existing_simhash,
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

                        candidate = IdentityMatch(
                            verdict=(
                                IdentityVerdict.NEAR_DUPLICATE
                            ),
                            candidate_path=candidate_path,
                            matched_path=str(
                                row.get("file_path")
                            ),
                            layer="simhash64",
                            confidence=confidence,
                            reason=(
                                "Very small SimHash distance "
                                "with nearly identical "
                                "normalized content length."
                            ),
                            simhash_distance=distance,
                        )

                        if (
                            best_near is None
                            or candidate.confidence
                            > best_near.confidence
                        ):
                            best_near = candidate

        if best_near is not None:
            return best_near

        # ====================================================
        # LAYER 4 — STRUCTURAL IDENTITY
        #
        # Structural match alone never silently deduplicates.
        # It identifies likely revisions or ambiguous identity.
        # ====================================================

        for row in shortlist:
            existing_path = str(
                row.get("file_path") or ""
            )

            existing_title = str(
                row.get("title")
                or Path(existing_path).name
            )

            existing_chars = row.get(
                "content_chars"
            )

            try:
                existing_chars = (
                    int(existing_chars)
                    if existing_chars is not None
                    else None
                )
            except (TypeError, ValueError):
                existing_chars = None

            existing_size = None

            try:
                existing_size = (
                    Path(existing_path)
                    .stat()
                    .st_size
                )
            except OSError:
                pass

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
                existing_title=existing_title,
                existing_size=existing_size,
                existing_chars=existing_chars,
            )

            if score >= 0.90:
                candidate = IdentityMatch(
                    verdict=(
                        IdentityVerdict.STRUCTURAL_MATCH
                    ),
                    candidate_path=candidate_path,
                    matched_path=existing_path,
                    layer="structure",
                    confidence=score,
                    reason=(
                        "Title and document structure are "
                        "strongly similar. Treat as possible "
                        "revision/variant, not an automatic "
                        "duplicate."
                    ),
                    structural_score=score,
                )

                if (
                    best_structural is None
                    or candidate.confidence
                    > best_structural.confidence
                ):
                    best_structural = candidate

        if best_structural is not None:
            return best_structural

        # ====================================================
        # No deterministic identity collision.
        # ====================================================

        if fingerprint.normalized_content_sha256:
            return IdentityMatch(
                verdict=IdentityVerdict.DISTINCT,
                candidate_path=candidate_path,
                matched_path=None,
                layer="deterministic",
                confidence=0.95,
                reason=(
                    "No exact, normalized-content, "
                    "near-duplicate, or strong structural "
                    "runtime identity was found."
                ),
            )

        return IdentityMatch(
            verdict=IdentityVerdict.UNRESOLVED,
            candidate_path=candidate_path,
            matched_path=None,
            layer="insufficient_content",
            confidence=0.50,
            reason=(
                "No exact SHA match exists, but extracted "
                "text was unavailable for deterministic "
                "content identity. Preserve for later "
                "inspection rather than guessing."
            ),
        )
