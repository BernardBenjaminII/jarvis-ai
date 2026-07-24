"""Evidence-backed, read-only public API restoration recommendations."""

from __future__ import annotations

from dataclasses import dataclass

from core.architecture import architecture_fingerprint, canonical_json

from .compatibility import CompatibilityFinding, CompatibilityReport


@dataclass(frozen=True, slots=True)
class RestorationRecommendation:
    package: str
    symbol: str
    action: str
    target_file: str
    source_module: str | None
    rationale: str
    confidence: float

    def to_canonical_json(self) -> str:
        return canonical_json(self)

    def fingerprint(self) -> str:
        return architecture_fingerprint(self)


def recommendation_for_finding(
    finding: CompatibilityFinding,
) -> RestorationRecommendation:
    target_file = finding.package.replace(".", "/") + "/__init__.py"

    if finding.finding_type == "missing_export" and finding.implementation_candidates:
        source_module = finding.implementation_candidates[0]
        action = "restore_public_export"
        rationale = (
            f"Expose {finding.symbol} from {source_module} through "
            f"{finding.package} without duplicating implementation."
        )
        confidence = 0.99 if len(finding.implementation_candidates) == 1 else 0.82
    elif finding.finding_type == "missing_symbol":
        source_module = None
        action = "investigate_removed_or_renamed_symbol"
        rationale = (
            "No implementation candidate was discovered. Review history, migration "
            "documents, and certified contracts before changing source."
        )
        confidence = 0.55
    else:
        source_module = None
        action = "investigate_missing_package"
        rationale = (
            "The expected package is unavailable. Determine whether the package moved, "
            "was retired, or failed to install before restoration."
        )
        confidence = 0.45

    return RestorationRecommendation(
        package=finding.package,
        symbol=finding.symbol,
        action=action,
        target_file=target_file,
        source_module=source_module,
        rationale=rationale,
        confidence=confidence,
    )


def build_restoration_plan(
    report: CompatibilityReport,
) -> tuple[RestorationRecommendation, ...]:
    return tuple(
        recommendation_for_finding(finding)
        for finding in report.findings
    )


__all__ = [
    "RestorationRecommendation",
    "build_restoration_plan",
    "recommendation_for_finding",
]
