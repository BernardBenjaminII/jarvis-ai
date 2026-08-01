from __future__ import annotations
import json
from pathlib import Path
from .article_intelligence import ConstitutionalArticleIntelligence

class ConstitutionalArticleIntelligenceReporter:
    def write(self, intelligence: ConstitutionalArticleIntelligence, output_directory: Path) -> tuple[Path, ...]:
        output_directory.mkdir(parents=True, exist_ok=True)
        common = {
            "schema_version": intelligence.schema_version,
            "coverage_fingerprint": intelligence.coverage_fingerprint,
            "article_intelligence_fingerprint": intelligence.article_intelligence_fingerprint,
        }
        documents = {
            "constitutional_article_usage.json": {**common, "article_usage": list(intelligence.usage_registry)},
            "constitutional_article_rankings.json": {**common, "rankings": intelligence.rankings},
            "constitutional_authority_distribution.json": {**common, "authority_distribution": intelligence.authority_distribution},
            "constitutional_influence_scores.json": {**common, "influence_scores": list(intelligence.influence_scores)},
            "constitutional_article_heatmap.json": {**common, "heatmap": intelligence.heatmap},
        }
        written = []
        for name, body in documents.items():
            path = output_directory / name
            path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
            written.append(path)
        report = output_directory / "constitutional_article_summary.md"
        report.write_text(
            "# Genesis VII-C4.3 Pack 2 — Constitutional Article Intelligence\n\n"
            f"**Coverage fingerprint:** `{intelligence.coverage_fingerprint}`\n\n"
            f"**Article intelligence fingerprint:** `{intelligence.article_intelligence_fingerprint}`\n\n"
            f"- Articles analyzed: {len(intelligence.usage_registry)}\n"
            f"- Critical hotspots: {intelligence.heatmap['critical_count']}\n"
            f"- Review hotspots: {intelligence.heatmap['review_count']}\n"
            f"- Active articles: {intelligence.heatmap['active_count']}\n"
            f"- Cold articles: {intelligence.heatmap['cold_count']}\n"
            f"- Diagnostics: {len(intelligence.diagnostics)}\n"
        )
        written.append(report)
        return tuple(written)
