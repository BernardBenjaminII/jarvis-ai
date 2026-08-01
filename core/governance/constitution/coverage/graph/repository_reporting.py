import json
from pathlib import Path
def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
class ConstitutionalRepositoryProjectionReporter:
    def write(self, assessment, output_directory: Path):
        common = {"schema_version": assessment.schema_version,
                  "authority_graph_fingerprint": assessment.authority_graph_fingerprint,
                  "graph_foundation_fingerprint": assessment.graph_foundation_fingerprint,
                  "article_intelligence_fingerprint": assessment.article_intelligence_fingerprint,
                  "repository_projection_fingerprint": assessment.repository_projection_fingerprint}
        written = [
            _write(output_directory/"constitutional_repository_projection.json", assessment.to_dict()),
            _write(output_directory/"constitutional_repository_nodes.json", {**common, "nodes":[n.to_dict() for n in assessment.nodes]}),
            _write(output_directory/"constitutional_repository_edges.json", {**common, "edges":[e.to_dict() for e in assessment.edges]}),
            _write(output_directory/"constitutional_repository_metrics.json", {**common, "metrics":assessment.metrics.to_dict()}),
            _write(output_directory/"constitutional_repository_integrity.json", {**common, "integrity":assessment.integrity.to_dict()}),
        ]
        report = output_directory/"constitutional_repository_summary.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        m = assessment.metrics
        report.write_text(
            "# Genesis VII-C4.3 Pack 3B-2A — Repository Projection\n\n"
            f"**Repository projection fingerprint:** `{assessment.repository_projection_fingerprint}`\n\n"
            f"- Repository roots: {m.repository_count}\n- Packages: {m.package_count}\n"
            f"- Modules: {m.module_count}\n- Documents: {m.document_count}\n"
            f"- Tests: {m.test_count}\n- Verifications: {m.verification_count}\n"
            f"- Unknown: {m.unknown_count}\n"
            f"- Classification completeness: {m.classification_completeness_ratio:.2%}\n"
            f"- Integrity valid: {assessment.integrity.is_valid}\n"
            f"- Diagnostics: {len(assessment.diagnostics)}\n", encoding="utf-8")
        written.append(report)
        return tuple(written)
