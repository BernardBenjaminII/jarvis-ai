from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from .authority import resolve_authority
from .contracts import ANALYSIS_SCHEMA_VERSION
from .detectors import detect_pair
from .loader import load_extraction
from .models import AnalysisStatistics, ConstitutionalAnalysis, Relationship


def _sha256_json(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _relationship_id(source_id: str, target_id: str, relationship_type: str) -> str:
    seed = f"{source_id}|{target_id}|{relationship_type}".encode("utf-8")
    return "REL-" + hashlib.sha256(seed).hexdigest()[:20].upper()


class ConstitutionalAnalysisEngine:
    def analyze(self, extraction_directory: Path) -> ConstitutionalAnalysis:
        repository_fingerprint, extraction_fingerprint, claims = load_extraction(extraction_directory)

        by_domain: dict[str, list] = defaultdict(list)
        for claim in claims:
            by_domain[claim.domain].append(claim)

        relationships: list[Relationship] = []
        seen: set[tuple[str, str, str]] = set()

        for domain in sorted(by_domain):
            group = by_domain[domain]
            for left_index, left in enumerate(group):
                for right in group[left_index + 1:]:
                    detection = detect_pair(left, right)
                    if detection is None:
                        continue

                    source, target = sorted((left, right), key=lambda claim: claim.claim_id)
                    key = (source.claim_id, target.claim_id, detection.relationship_type)
                    if key in seen:
                        continue
                    seen.add(key)

                    authority_resolution = ""
                    if detection.relationship_type == "contradicts":
                        authority_resolution = resolve_authority(
                            source.authority_rank,
                            target.authority_rank,
                            source.claim_id,
                            target.claim_id,
                        )

                    relationships.append(
                        Relationship(
                            relationship_id=_relationship_id(*key),
                            source_claim_id=source.claim_id,
                            target_claim_id=target.claim_id,
                            relationship_type=detection.relationship_type,
                            score=detection.score,
                            rationale=detection.rationale,
                            authority_resolution=authority_resolution,
                        )
                    )

        relationships.sort(
            key=lambda item: (
                item.source_claim_id,
                item.target_claim_id,
                item.relationship_type,
                item.relationship_id,
            )
        )

        counts = defaultdict(int)
        authority_resolutions = 0
        for relationship in relationships:
            counts[relationship.relationship_type] += 1
            if relationship.authority_resolution and relationship.authority_resolution != "unresolved_equal_authority":
                authority_resolutions += 1

        statistics = AnalysisStatistics(
            claims=len(claims),
            relationships=len(relationships),
            duplicates=counts["duplicates"],
            supports=counts["supports"],
            contradictions=counts["contradicts"],
            refines=counts["refines"],
            authority_resolutions=authority_resolutions,
            diagnostics=0,
        )

        fingerprint_basis = {
            "schema_version": ANALYSIS_SCHEMA_VERSION,
            "repository_fingerprint": repository_fingerprint,
            "extraction_fingerprint": extraction_fingerprint,
            "claims": [claim.to_dict() for claim in claims],
            "relationships": [relationship.to_dict() for relationship in relationships],
            "statistics": statistics.to_dict(),
        }
        analysis_fingerprint = _sha256_json(fingerprint_basis)

        return ConstitutionalAnalysis(
            schema_version=ANALYSIS_SCHEMA_VERSION,
            repository_fingerprint=repository_fingerprint,
            extraction_fingerprint=extraction_fingerprint,
            analysis_fingerprint=analysis_fingerprint,
            claims=claims,
            relationships=tuple(relationships),
            statistics=statistics,
            diagnostics=(),
        )
