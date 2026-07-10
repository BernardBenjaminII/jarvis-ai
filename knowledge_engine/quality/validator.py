from __future__ import annotations

from knowledge_engine.quality.models import QualityReport


class KnowledgeQualityValidator:

    def validate_chunk(self, text: str) -> QualityReport:

        errors = []
        warnings = []

        if not text:

            errors.append("Empty chunk.")

        if len(text.strip()) < 20:

            warnings.append("Chunk unusually small.")

        #
        # Detect tuple serialization.
        #

        if text.startswith("('"):

            errors.append(
                "Chunk appears to contain tuple serialization."
            )

        if text.startswith('("'):

            errors.append(
                "Chunk appears to contain tuple serialization."
            )

        if "\\n" in text:

            warnings.append(
                "Escaped newlines detected."
            )

        score = 100

        score -= len(errors) * 40

        score -= len(warnings) * 10

        score = max(score, 0)

        return QualityReport(
            passed=len(errors) == 0,
            score=score,
            errors=errors,
            warnings=warnings,
        )
