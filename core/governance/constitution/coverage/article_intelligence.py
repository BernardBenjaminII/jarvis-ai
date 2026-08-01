from __future__ import annotations
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median
from typing import Any
from .fingerprints import canonical_fingerprint

@dataclass(frozen=True)
class ConstitutionalArticleIntelligence:
    schema_version: str
    coverage_fingerprint: str
    article_intelligence_fingerprint: str
    usage_registry: tuple[dict[str, Any], ...]
    influence_scores: tuple[dict[str, Any], ...]
    rankings: dict[str, Any]
    authority_distribution: dict[str, Any]
    heatmap: dict[str, Any]
    diagnostics: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "coverage_fingerprint": self.coverage_fingerprint,
            "article_intelligence_fingerprint": self.article_intelligence_fingerprint,
            "usage_registry": list(self.usage_registry),
            "influence_scores": list(self.influence_scores),
            "rankings": self.rankings,
            "authority_distribution": self.authority_distribution,
            "heatmap": self.heatmap,
            "diagnostics": list(self.diagnostics),
        }

class ConstitutionalArticleIntelligenceEngine:
    SCHEMA_VERSION = "1.0.0"

    def assess(self, *, pack1_directory: Path, c4_2_directory: Path) -> ConstitutionalArticleIntelligence:
        metrics = json.loads((pack1_directory / "constitutional_coverage_metrics.json").read_text())
        trace = json.loads((pack1_directory / "constitutional_coverage_traceability.json").read_text())
        audit = json.loads((c4_2_directory / "constitutional_repository_audit.json").read_text())
        inventory = json.loads((c4_2_directory / "constitutional_repository_inventory.json").read_text())

        article_metrics = metrics.get("article_metrics", [])
        artifacts = inventory.get("artifacts", [])
        assessments = audit.get("assessments", [])
        diagnostics: list[str] = []

        artifact_by_id = {str(a.get("artifact_id", "")): a for a in artifacts}
        domains_by_article: dict[str, set[str]] = defaultdict(set)
        artifacts_by_article: dict[str, set[str]] = defaultdict(set)
        for assessment in assessments:
            artifact_id = str(assessment.get("artifact_id", ""))
            domain = str(artifact_by_id.get(artifact_id, {}).get("domain", "general"))
            for article_id in assessment.get("applicable_articles", []) or []:
                article_id = str(article_id)
                domains_by_article[article_id].add(domain)
                artifacts_by_article[article_id].add(artifact_id)

        usage = []
        for metric in sorted(article_metrics, key=lambda x: str(x.get("article_id", ""))):
            article_id = str(metric.get("article_id", ""))
            basis = {
                "article_id": article_id,
                "reference_count": int(metric.get("reference_count", 0)),
                "artifact_count": int(metric.get("artifact_count", 0)),
                "classification": str(metric.get("classification", "unused")),
                "compliant_count": int(metric.get("compliant_count", 0)),
                "review_required_count": int(metric.get("review_required_count", 0)),
                "noncompliant_count": int(metric.get("noncompliant_count", 0)),
                "artifacts": sorted(artifacts_by_article.get(article_id, set())),
                "domains": sorted(domains_by_article.get(article_id, set())),
            }
            usage.append({**basis, "usage_fingerprint": canonical_fingerprint(basis)})

        max_refs = max((x["reference_count"] for x in usage), default=0)
        max_domains = max((len(x["domains"]) for x in usage), default=0)
        influence = []
        for item in usage:
            score = round(
                0.55 * (item["reference_count"] / max_refs if max_refs else 0)
                + 0.25 * (len(item["domains"]) / max_domains if max_domains else 0)
                + 0.15 * min(1.0, item["review_required_count"] / 5)
                + 0.05 * min(1.0, item["noncompliant_count"] / 3),
                6,
            )
            basis = {"article_id": item["article_id"], "influence_score": score}
            influence.append({**basis, "influence_fingerprint": canonical_fingerprint(basis)})

        score_by_id = {x["article_id"]: x["influence_score"] for x in influence}
        def ranked(key):
            ordered = sorted(usage, key=lambda x: (key(x), x["article_id"]), reverse=True)
            return [{"rank": i, "article_id": x["article_id"], "value": key(x)} for i, x in enumerate(ordered, 1)]

        rankings = {
            "most_referenced": ranked(lambda x: x["reference_count"]),
            "most_influential": ranked(lambda x: score_by_id[x["article_id"]]),
            "widest_domain_reach": ranked(lambda x: len(x["domains"])),
            "most_reviewed": ranked(lambda x: x["review_required_count"]),
            "never_exercised": sorted(x["article_id"] for x in usage if x["reference_count"] == 0),
        }
        rankings["rankings_fingerprint"] = canonical_fingerprint(rankings)

        counts = Counter(x["classification"] for x in usage)
        distribution = {
            "classification_distribution": dict(sorted(counts.items())),
            "articles_with_cross_domain_authority": sum(len(x["domains"]) > 1 for x in usage),
            "articles_with_single_domain_authority": sum(len(x["domains"]) == 1 for x in usage),
            "articles_without_observed_domain_authority": sum(len(x["domains"]) == 0 for x in usage),
        }
        distribution["distribution_fingerprint"] = canonical_fingerprint(distribution)

        cells = []
        for item in usage:
            if item["noncompliant_count"] > 0:
                hotspot = "critical"
            elif item["review_required_count"] > 0:
                hotspot = "review"
            elif item["reference_count"] > 0:
                hotspot = "active"
            else:
                hotspot = "cold"
            cells.append({
                "article_id": item["article_id"],
                "hotspot": hotspot,
                "reference_count": item["reference_count"],
                "influence_score": score_by_id[item["article_id"]],
            })
        heatmap = {
            "cells": cells,
            "critical_count": sum(x["hotspot"] == "critical" for x in cells),
            "review_count": sum(x["hotspot"] == "review" for x in cells),
            "active_count": sum(x["hotspot"] == "active" for x in cells),
            "cold_count": sum(x["hotspot"] == "cold" for x in cells),
        }
        heatmap["heatmap_fingerprint"] = canonical_fingerprint(heatmap)

        coverage_fp = str(trace.get("coverage_fingerprint", ""))
        basis = {
            "schema_version": self.SCHEMA_VERSION,
            "coverage_fingerprint": coverage_fp,
            "usage_registry": usage,
            "influence_scores": influence,
            "rankings": rankings,
            "authority_distribution": distribution,
            "heatmap": heatmap,
            "diagnostics": diagnostics,
        }
        return ConstitutionalArticleIntelligence(
            self.SCHEMA_VERSION,
            coverage_fp,
            canonical_fingerprint(basis),
            tuple(usage),
            tuple(influence),
            rankings,
            distribution,
            heatmap,
            tuple(diagnostics),
        )
