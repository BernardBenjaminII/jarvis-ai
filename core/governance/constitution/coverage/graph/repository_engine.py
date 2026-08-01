import json
from pathlib import Path
from ..fingerprints import canonical_fingerprint
from .repository_builder import build_repository_projection
from .repository_contracts import REPOSITORY_PROJECTION_SCHEMA_VERSION
from .repository_integrity import verify_repository_projection_integrity
from .repository_metrics import compute_repository_projection_metrics
from .repository_models import RepositoryProjectionAssessment

class ConstitutionalRepositoryProjectionEngine:
    def assess(self, *, pack3b1_directory: Path):
        source = json.loads((pack3b1_directory / "constitutional_authority_graph.json").read_text(encoding="utf-8"))
        afp = str(source.get("authority_graph_fingerprint", ""))
        gfp = str(source.get("graph_foundation_fingerprint", ""))
        ifp = str(source.get("article_intelligence_fingerprint", ""))
        authority_nodes = source.get("nodes", [])
        diagnostics = []
        if not afp: diagnostics.append("Authority graph fingerprint is missing.")
        if not gfp: diagnostics.append("Graph foundation fingerprint is missing.")
        if not ifp: diagnostics.append("Article intelligence fingerprint is missing.")
        if not isinstance(authority_nodes, list):
            authority_nodes = []; diagnostics.append("Authority node registry is invalid.")
        nodes, edges = build_repository_projection(authority_nodes)
        integrity = verify_repository_projection_integrity(nodes, edges)
        metrics = compute_repository_projection_metrics(nodes, edges)
        diagnostics.extend(integrity.diagnostics)
        basis = {"schema_version": REPOSITORY_PROJECTION_SCHEMA_VERSION,
                 "authority_graph_fingerprint": afp, "graph_foundation_fingerprint": gfp,
                 "article_intelligence_fingerprint": ifp,
                 "nodes": [n.to_dict() for n in nodes], "edges": [e.to_dict() for e in edges],
                 "metrics": metrics.to_dict(), "integrity": integrity.to_dict(),
                 "diagnostics": diagnostics}
        return RepositoryProjectionAssessment(REPOSITORY_PROJECTION_SCHEMA_VERSION, afp, gfp, ifp,
                                              canonical_fingerprint(basis), nodes, edges, metrics,
                                              integrity, tuple(diagnostics))
