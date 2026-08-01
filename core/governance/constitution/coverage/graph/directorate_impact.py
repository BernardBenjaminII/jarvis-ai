from __future__ import annotations
from dataclasses import dataclass
from ..fingerprints import canonical_fingerprint
from .directorate_authority import DirectorateAuthorityResolver
from .directorate_capabilities import DirectorateCapabilityResolver
from .directorate_review import DirectorateReviewEngine

@dataclass(frozen=True)
class DirectorateImpactAssessment:
    changed_paths: tuple[str, ...]
    affected_directorate_ids: tuple[str, ...]
    affected_ownership_domain_ids: tuple[str, ...]
    affected_capability_keys: tuple[str, ...]
    required_reviewer_directorate_ids: tuple[str, ...]
    unresolved_paths: tuple[str, ...]
    fingerprint: str
    def to_dict(self):
        return {'changed_paths': list(self.changed_paths), 'affected_directorate_ids': list(self.affected_directorate_ids), 'affected_ownership_domain_ids': list(self.affected_ownership_domain_ids), 'affected_capability_keys': list(self.affected_capability_keys), 'required_reviewer_directorate_ids': list(self.required_reviewer_directorate_ids), 'unresolved_paths': list(self.unresolved_paths), 'fingerprint': self.fingerprint}

class DirectorateImpactAnalyzer:
    def __init__(self, authority_resolver, capability_resolver, review_engine):
        self._authority = authority_resolver; self._capabilities = capability_resolver; self._reviews = review_engine
    def assess(self, changed_paths):
        normalized = tuple(sorted({p.replace('\\','/').strip('/') for p in changed_paths}))
        directorates=set(); domains=set(); capabilities=set(); reviewers=set(); unresolved=[]
        for path in normalized:
            authority=self._authority.resolve(path)
            if not authority.resolved: unresolved.append(path); continue
            if authority.owner_directorate_id: directorates.add(authority.owner_directorate_id)
            directorates.update(authority.maintainer_directorate_ids); directorates.update(authority.certifier_directorate_ids); directorates.update(authority.responsible_directorate_ids)
            if authority.ownership_domain_id: domains.add(authority.ownership_domain_id)
            capabilities.add(self._capabilities.resolve(path, authority).capability_key)
            reviewers.update(self._reviews.determine(authority).required_reviewer_directorate_ids)
        basis={'changed_paths':list(normalized),'affected_directorate_ids':sorted(directorates),'affected_ownership_domain_ids':sorted(domains),'affected_capability_keys':sorted(capabilities),'required_reviewer_directorate_ids':sorted(reviewers),'unresolved_paths':sorted(unresolved)}
        return DirectorateImpactAssessment(normalized, tuple(basis['affected_directorate_ids']), tuple(basis['affected_ownership_domain_ids']), tuple(basis['affected_capability_keys']), tuple(basis['required_reviewer_directorate_ids']), tuple(basis['unresolved_paths']), canonical_fingerprint(basis))
