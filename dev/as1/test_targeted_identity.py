from __future__ import annotations

import sqlite3
import tempfile

from pathlib import Path

from dev.as1.identity import (
    IdentityVerdict,
    build_fingerprint,
    sha256_file,
)

from dev.as1.targeted_identity import (
    TargetedRuntimeIdentityResolver,
)


def db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    conn.execute(
        """
        CREATE TABLE runtime_documents (
            id INTEGER PRIMARY KEY,
            file_path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            title TEXT NOT NULL,
            media_type TEXT NOT NULL,
            content_text TEXT NOT NULL,
            content_chars INTEGER NOT NULL
        )
        """
    )

    return conn


def main():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        original = (
            root / "Urban Operations Manual.txt"
        )

        original_text = (
            "Urban operations require careful analysis "
            "of terrain infrastructure civilians and "
            "enemy capabilities. "
        ) * 40

        original.write_text(
            original_text,
            encoding="utf-8",
        )

        conn = db()

        conn.execute(
            """
            INSERT INTO runtime_documents (
                id,
                file_path,
                sha256,
                title,
                media_type,
                content_text,
                content_chars
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                str(original),
                sha256_file(original),
                original.name,
                "text/plain",
                original_text,
                len(original_text),
            ),
        )

        conn.commit()

        resolver = (
            TargetedRuntimeIdentityResolver(
                conn,
                maximum_candidates=3,
            )
        )

        # ----------------------------------------------------
        # Exact duplicate
        # ----------------------------------------------------

        exact = root / "copy.txt"
        exact.write_bytes(
            original.read_bytes()
        )

        exact_text = exact.read_text()

        exact_fp = build_fingerprint(
            path=exact,
            sha256=sha256_file(exact),
            text=exact_text,
        )

        result = resolver.resolve(
            fingerprint=exact_fp,
            candidate_text=exact_text,
        )

        assert (
            result.verdict
            == IdentityVerdict.EXACT_DUPLICATE
        )

        # ----------------------------------------------------
        # Formatted content duplicate with changed title.
        # ----------------------------------------------------

        formatted = (
            root
            / "Urban Operations Variant.txt"
        )

        formatted_text = (
            original_text
            .upper()
            .replace(
                ".",
                " . "
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

        result = resolver.resolve(
            fingerprint=formatted_fp,
            candidate_text=formatted_text,
        )

        assert (
            result.verdict
            == IdentityVerdict.CONTENT_DUPLICATE
        )

        assert (
            result.matched_path
            == str(original)
        )

        # ----------------------------------------------------
        # Unrelated document.
        #
        # Bounded SQL must NOT claim global DISTINCT.
        # ----------------------------------------------------

        unrelated = (
            root / "Tomato Gardening.txt"
        )

        unrelated_text = (
            "Tomatoes require sunlight water soil "
            "spacing and seasonal planning. "
        ) * 40

        unrelated.write_text(
            unrelated_text,
            encoding="utf-8",
        )

        unrelated_fp = build_fingerprint(
            path=unrelated,
            sha256=sha256_file(unrelated),
            text=unrelated_text,
        )

        result = resolver.resolve(
            fingerprint=unrelated_fp,
            candidate_text=unrelated_text,
        )

        assert (
            result.verdict
            == IdentityVerdict.UNRESOLVED
        )

        conn.close()

    print(
        "GENESIS AS1 PACK 2-R2-R1 "
        "TARGETED SQL TESTS: PASS"
    )


if __name__ == "__main__":
    main()
