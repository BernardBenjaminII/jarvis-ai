from __future__ import annotations

import json
from pathlib import Path

OLD_BLOCK = """    def _search_catalog(self, query: str, limit: int) -> Iterable[Mapping[str, Any]]:
        from core.knowledge_catalog.search import search_catalog
        return search_catalog(query, db_path=self.database_path, limit=limit)
"""

NEW_BLOCK = """    def _search_catalog(self, query: str, limit: int) -> Iterable[Mapping[str, Any]]:
        from core.knowledge_catalog.qualified_search import search_qualified_catalog

        return search_qualified_catalog(
            query,
            db_path=self.database_path,
            limit=limit,
        )
"""

def repair(root: Path) -> dict:
    target = root / "core/conversation/grounding.py"
    if not target.is_file():
        raise FileNotFoundError(target)
    source = target.read_text(encoding="utf-8")
    if NEW_BLOCK in source:
        status = "already_integrated"
        changed = False
    elif OLD_BLOCK in source:
        target.write_text(source.replace(OLD_BLOCK, NEW_BLOCK, 1), encoding="utf-8")
        status = "integrated"
        changed = True
    else:
        raise RuntimeError(
            "The canonical CatalogGroundingService._search_catalog block "
            "was not found. No production file was changed."
        )
    report = {
        "schema_version": "genesis_ix_a4_5_pack3a_v1",
        "target": str(target),
        "status": status,
        "changed": changed,
        "integration": (
            "CatalogGroundingService._search_catalog -> "
            "search_qualified_catalog -> search_catalog -> QualificationEngine"
        ),
    }
    output = root / "docs/audits/genesis_ix_a4_5_pack3a"
    output.mkdir(parents=True, exist_ok=True)
    (output / "runtime_integration.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "runtime_integration.md").write_text(
        "# Genesis IX-A4.5 Pack 3A — Runtime Integration\n\n"
        f"**Status:** `{status}`\n"
        f"**Changed:** `{changed}`\n"
        f"**Target:** `{target}`\n\n"
        "```text\n"
        f"{report['integration']}\n"
        "```\n",
        encoding="utf-8",
    )
    print("[PASS] Runtime integration:", status)
    return report

def main() -> int:
    repair(Path.cwd().resolve())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
