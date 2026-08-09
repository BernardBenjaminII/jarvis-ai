from __future__ import annotations

import json
from pathlib import Path

BROKEN_WRAPPER = '''    tracer = EndToEndRetrievalTracer(
        repository_root=Path(bootstrap.repository_root),
        catalog_database=catalog,
    )

    if catalog is None:
        raise RuntimeError(
            "Semantic known-query certification requires a catalog database."
        )

    from core.retrieval.certification.semantic_fixture import (
        install_semantic_fixture_override,
    )

    fixture = install_semantic_fixture_override(
        tracer,
        catalog,
    )
    report = tracer.certify()
'''

CANONICAL_WRAPPER = '''    report = EndToEndRetrievalTracer(
        repository_root=Path(bootstrap.repository_root),
        catalog_database=catalog,
    ).certify()
'''

OLD_IMPORT = "        from core.knowledge_catalog.search import search_catalog\n"
NEW_IMPORT = (
    "        from core.knowledge_catalog.qualified_search "
    "import search_qualified_catalog as search_catalog\n"
)

OLD_WORD_RE = 'WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{3,}")\n'
NEW_WORD_RE = '''WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_./+-]*")
HEX_RE = re.compile(r"^[0-9a-fA-F]{24,}$")
METADATA_TERMS = frozenset(
    {
        "sha256", "metadata", "document", "documents", "file",
        "file_path", "path", "confidence", "score", "chunk",
        "chunk_id", "document_id", "created_at", "updated_at",
        "assigned_by", "content", "text", "source", "runtime",
        "catalog", "page", "chapter", "http", "https",
    }
)
'''

START_MARKER = "    def _database_terms(self) -> list[str]:\n"
END_MARKER = "    @contextmanager\n"

NEW_METHODS = '''    def _database_terms(self) -> list[str]:
        """Return deterministic semantic phrases from the live corpus."""
        if self.catalog_database is None or not self.catalog_database.is_file():
            return []

        candidates: list[str] = []
        seen: set[str] = set()

        def add_candidate(value: Any) -> None:
            phrase = self._semantic_phrase(str(value or ""))
            key = phrase.casefold()
            if not phrase or key in seen:
                return
            seen.add(key)
            candidates.append(phrase)

        with sqlite3.connect(self.catalog_database) as connection:
            tables = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type IN ('table','view')"
                ).fetchall()
            }

            probes = [
                ("runtime_documents", ("title",)),
                ("catalog_documents", ("title",)),
                ("document_subjects", ("subject",)),
                ("knowledge_registry", ("title", "subject")),
                ("runtime_chunks", ("chunk_text", "text", "content")),
            ]

            for table, possible_columns in probes:
                if table not in tables:
                    continue

                columns = {
                    str(row[1])
                    for row in connection.execute(
                        f'PRAGMA table_info("{table}")'
                    ).fetchall()
                }

                for column in possible_columns:
                    if column not in columns:
                        continue

                    try:
                        rows = connection.execute(
                            f'SELECT "{column}" FROM "{table}" '
                            f'WHERE "{column}" IS NOT NULL '
                            f'AND length(trim("{column}")) >= 8 '
                            f'LIMIT 300'
                        ).fetchall()
                    except sqlite3.Error:
                        continue

                    for row in rows:
                        add_candidate(row[0])
                        if len(candidates) >= 250:
                            return candidates

        return candidates

    @staticmethod
    def _semantic_phrase(value: str) -> str:
        """Normalize one corpus value into a meaningful multi-word query."""
        words: list[str] = []

        for token in WORD_RE.findall(value):
            lowered = token.casefold()
            if lowered in METADATA_TERMS:
                continue
            if HEX_RE.fullmatch(token):
                continue
            if token.startswith(("http://", "https://")):
                continue
            words.append(token)
            if len(words) >= 10:
                break

        if len(words) < 2:
            return ""

        phrase = " ".join(words).strip()
        if len(phrase) < 8:
            return ""
        if not any(len(word) >= 5 for word in words):
            return ""
        return phrase

'''

def repair_wrapper(root: Path) -> dict:
    target = root / "dev/certification/certify_genesis_ix_a4_3.py"
    source = target.read_text(encoding="utf-8")
    if BROKEN_WRAPPER in source:
        source = source.replace(BROKEN_WRAPPER, CANONICAL_WRAPPER, 1)
        target.write_text(source, encoding="utf-8")
        return {"target": str(target), "status": "restored", "changed": True}
    if CANONICAL_WRAPPER in source:
        return {"target": str(target), "status": "already_canonical", "changed": False}
    raise RuntimeError("IX-A4.3 wrapper invocation was not recognized.")

def repair_tracer(root: Path) -> dict:
    target = root / "core/retrieval/certification/tracer.py"
    source = target.read_text(encoding="utf-8")
    changed = False

    if NEW_IMPORT not in source:
        if OLD_IMPORT not in source:
            raise RuntimeError("Expected search_catalog import not found.")
        source = source.replace(OLD_IMPORT, NEW_IMPORT, 1)
        changed = True

    if "METADATA_TERMS = frozenset(" not in source:
        if OLD_WORD_RE not in source:
            raise RuntimeError("Expected WORD_RE declaration not found.")
        source = source.replace(OLD_WORD_RE, NEW_WORD_RE, 1)
        changed = True

    if "def _semantic_phrase(value: str)" not in source:
        start = source.find(START_MARKER)
        end = source.find(END_MARKER, start)
        if start < 0 or end < 0:
            raise RuntimeError("Could not locate _database_terms method boundaries.")
        source = source[:start] + NEW_METHODS + source[end:]
        changed = True

    target.write_text(source, encoding="utf-8")
    return {
        "target": str(target),
        "status": "repaired" if changed else "already_repaired",
        "changed": changed,
    }

def main() -> int:
    root = Path.cwd().resolve()
    wrapper = repair_wrapper(root)
    tracer = repair_tracer(root)
    report = {
        "schema_version": "genesis_ix_a4_5_pack3a_2_v1",
        "wrapper": wrapper,
        "tracer": tracer,
    }
    output = root / "docs/audits/genesis_ix_a4_5_pack3a_2"
    output.mkdir(parents=True, exist_ok=True)
    (output / "native_fixture_repair.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "native_fixture_repair.md").write_text(
        "# Genesis IX-A4.5 Pack 3A.2 — Native Semantic Fixture Integration\n\n"
        f"**Wrapper:** `{wrapper['status']}`\n"
        f"**Tracer:** `{tracer['status']}`\n",
        encoding="utf-8",
    )
    print("[PASS] IX-A4.3 wrapper:", wrapper["status"])
    print("[PASS] Retrieval tracer:", tracer["status"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
