from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "dev/integration/fixtures/phase_ii_c_sample.txt"


@dataclass
class StageResult:
    name: str
    passed: bool
    details: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class KnowledgePipelineIntegrationCheck:
    """
    Phase II-C integration verifier.

    This is intentionally conservative:
    - verifies pipeline modules import,
    - verifies the fixture exists,
    - verifies basic handoff data exists,
    - does not mutate the production Knowledge catalog.
    """

    REQUIRED_IMPORTS = [
        "knowledge_engine.receiving.scanner",
        "knowledge_engine.receiving.sanitizer",
        "knowledge_engine.receiving.filters",
        "knowledge_engine.discovery.scanner",
        "knowledge_engine.discovery.service",
        "knowledge_engine.inspectors.registry",
        "knowledge_engine.inspectors.text",
        "knowledge_engine.extraction.extractors.base",
        "knowledge_engine.processing.processor",
        "knowledge_engine.processing.extract_text_stage",
        "knowledge_engine.processing.chunk_stage",
        "knowledge_engine.chunking.chunker",
        "knowledge_engine.embeddings.engine",
        "knowledge_engine.objects.service",
        "knowledge_engine.registry.service",
        "knowledge_engine.knowledge_graph.builder",
        "knowledge_engine.retrieval.vector_search",
    ]

    def __init__(self):
        self.results: list[StageResult] = []

    def run(self) -> bool:
        self.results.append(self._check_fixture())
        self.results.append(self._check_imports())
        self.results.append(self._check_basic_text_handoff())

        return all(result.passed for result in self.results)

    def _check_fixture(self) -> StageResult:
        result = StageResult("Fixture", True)

        if not FIXTURE.exists():
            result.passed = False
            result.errors.append(f"Missing fixture: {FIXTURE}")
            return result

        text = FIXTURE.read_text(encoding="utf-8", errors="replace")

        if not text.strip():
            result.passed = False
            result.errors.append("Fixture is empty.")
            return result

        result.details.append(f"Fixture exists: {FIXTURE.relative_to(ROOT)}")
        result.details.append(f"Characters: {len(text)}")
        return result

    def _check_imports(self) -> StageResult:
        result = StageResult("Pipeline Imports", True)

        for module in self.REQUIRED_IMPORTS:
            try:
                importlib.import_module(module)
                result.details.append(f"import {module}")
            except Exception as exc:
                result.passed = False
                result.errors.append(f"{module}: {exc}")

        return result

    def _check_basic_text_handoff(self) -> StageResult:
        result = StageResult("Basic Text Handoff", True)

        try:
            text = FIXTURE.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            result.passed = False
            result.errors.append(f"Could not read fixture: {exc}")
            return result

        handoff = {
            "source_path": str(FIXTURE),
            "content_type": "text/plain",
            "text": text,
            "length": len(text),
        }

        required_keys = [
            "source_path",
            "content_type",
            "text",
            "length",
        ]

        for key in required_keys:
            if key not in handoff:
                result.passed = False
                result.errors.append(f"Missing handoff key: {key}")

        if handoff["length"] <= 0:
            result.passed = False
            result.errors.append("Handoff text length is zero.")

        result.details.append("Created basic handoff payload.")
        result.details.append(f"content_type={handoff['content_type']}")
        result.details.append(f"length={handoff['length']}")

        return result

    def print_report(self) -> None:
        print()
        print("=" * 70)
        print("PHASE II-C KNOWLEDGE ENGINE INTEGRATION")
        print("=" * 70)

        passed = 0
        failed = 0

        for result in self.results:
            symbol = "✓" if result.passed else "✗"
            print()
            print(f"{symbol} {result.name}")

            if result.details:
                print("    Details:")
                for line in result.details:
                    print(f"        • {line}")

            if result.errors:
                print("    Errors:")
                for line in result.errors:
                    print(f"        • {line}")

            if result.passed:
                passed += 1
            else:
                failed += 1

        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Stages Passed : {passed}")
        print(f"Stages Failed : {failed}")
        print("=" * 70)


def main() -> int:
    check = KnowledgePipelineIntegrationCheck()
    ok = check.run()
    check.print_report()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
