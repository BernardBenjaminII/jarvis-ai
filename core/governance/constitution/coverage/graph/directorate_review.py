from __future__ import annotations
from dataclasses import dataclass
from .directorate_authority import AuthorityResolution

@dataclass(frozen=True)
class ReviewRequirement:
    required_reviewer_directorate_ids: tuple[str, ...]
    approval_directorate_id: str | None
    certification_required: bool
    reasons: tuple[str, ...]
    def to_dict(self) -> dict[str, object]:
        return {'required_reviewer_directorate_ids': list(self.required_reviewer_directorate_ids), 'approval_directorate_id': self.approval_directorate_id, 'certification_required': self.certification_required, 'reasons': list(self.reasons)}

class DirectorateReviewEngine:
    def determine(self, authority: AuthorityResolution) -> ReviewRequirement:
        reviewers = {*authority.maintainer_directorate_ids, *authority.responsible_directorate_ids, *authority.certifier_directorate_ids}
        if authority.owner_directorate_id: reviewers.add(authority.owner_directorate_id)
        reasons = []
        if authority.owner_directorate_id: reasons.append('Owning directorate review required.')
        if authority.maintainer_directorate_ids: reasons.append('Maintaining directorate review required.')
        if authority.certifier_directorate_ids: reasons.append('Constitutional certification review required.')
        if not reasons: reasons.append('No constitutional authority could be resolved.')
        return ReviewRequirement(tuple(sorted(reviewers)), authority.owner_directorate_id, bool(authority.certifier_directorate_ids), tuple(reasons))
