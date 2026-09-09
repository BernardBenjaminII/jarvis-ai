from __future__ import annotations

import sqlite3
import tempfile

from pathlib import Path

from dev.as1.identity import (
    IdentityVerdict,
    LayeredIdentityResolver,
    RuntimeIdentityIndex,
    build_fingerprint,
    hamming64,
    normalize_text,
    normalized_content_sha256,
    sha256_file,
    simhash64,
)


def build_runtime_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    conn.executescript(
        """
        CREATE TABLE runtime_documents (
            id INTEGER PRIMARY KEY,
            file_path TEXT NOT NULL,
            sha256 TEXT,
            title TEXT,
            content_text TEXT,
            content_chars INTEGER
        );
        """
    )

    return conn


def main():
    # --------------------------------------------------------
    # Normalization
    # --------------------------------------------------------

    a = "Hello,\nWORLD!"
    b = " hello   world "

    assert normalize_text(a) == normalize_text(b)

    sha_a, chars_a = normalized_content_sha256(a)
    sha_b, chars_b = normalized_content_sha256(b)

    assert sha_a == sha_b
    assert chars_a == chars_b

    # --------------------------------------------------------
    # SimHash sanity
    # --------------------------------------------------------

    s1 = simhash64(
        "the quick brown fox jumps over the lazy dog"
    )

    s2 = simhash64(
        "the quick brown fox jumps over the lazy dog"
    )

    assert s1 is not None
    assert s2 is not None
    assert hamming64(s1, s2) == 0

    # --------------------------------------------------------
    # Runtime test fixture
    # --------------------------------------------------------

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        runtime_file = (
            root / "Urban Operations Manual.txt"
        )

        runtime_text = (
            "Urban operations require careful analysis "
            "of terrain, infrastructure, civilians, and "
            "enemy capabilities.\n"
        ) * 20

        runtime_file.write_text(
            runtime_text,
            encoding="utf-8",
        )

        runtime_sha = sha256_file(
            runtime_file
        )

        conn = build_runtime_db()

        conn.execute(
            """
            INSERT INTO runtime_documents (
                id,
                file_path,
                sha256,
                title,
                content_text,
                content_chars
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                str(runtime_file),
                runtime_sha,
                runtime_file.name,
                runtime_text,
                len(runtime_text),
            ),
        )

        conn.commit()

        index = RuntimeIdentityIndex(conn)

        resolver = LayeredIdentityResolver(
            index
        )

        # ----------------------------------------------------
        # Exact byte duplicate
        # ----------------------------------------------------

        exact = root / "copy.txt"

        exact.write_bytes(
            runtime_file.read_bytes()
        )

        exact_fp = build_fingerprint(
            path=exact,
            sha256=sha256_file(exact),
            text=exact.read_text(),
        )

        exact_result = resolver.resolve(
            fingerprint=exact_fp,
            candidate_text=exact.read_text(),
        )

        assert (
            exact_result.verdict
            == IdentityVerdict.EXACT_DUPLICATE
        )

        # ----------------------------------------------------
        # Same normalized content, different bytes
        # ----------------------------------------------------

        formatted = (
            root
            / "Urban-Operations-Manual-variant.txt"
        )

        formatted_text = (
            runtime_text
            .upper()
            .replace(
                ",",
                " , "
            )
        )

        formatted.write_text(
            formatted_text,
            encoding="utf-8",
        )

        formatted_fp = build_fingerprint(
            path=formatted,
            sha256=sha256_file(formatted),
            text=formatted_text,
        )

        formatted_result = resolver.resolve(
            fingerprint=formatted_fp,
            candidate_text=formatted_text,
        )

        assert (
            formatted_result.verdict
            in {
                IdentityVerdict.CONTENT_DUPLICATE,
                IdentityVerdict.NEAR_DUPLICATE,
            }
        )

        # ----------------------------------------------------
        # Distinct
        # ----------------------------------------------------

        distinct = root / "gardening.txt"

        distinct_text = (
            "Tomatoes require sunlight, water, fertile "
            "soil, spacing, and seasonal planning.\n"
        ) * 20

        distinct.write_text(
            distinct_text,
            encoding="utf-8",
        )

        distinct_fp = build_fingerprint(
            path=distinct,
            sha256=sha256_file(distinct),
            text=distinct_text,
        )

        distinct_result = resolver.resolve(
            fingerprint=distinct_fp,
            candidate_text=distinct_text,
        )

        assert (
            distinct_result.verdict
            in {
                IdentityVerdict.DISTINCT,
                IdentityVerdict.UNRESOLVED,
            }
        )

        conn.close()

    print(
        "GENESIS AS1 PACK 2 "
        "IDENTITY TESTS: PASS"
    )


if __name__ == "__main__":
    main()
