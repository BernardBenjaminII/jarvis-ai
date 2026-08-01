from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .directorate_authority import DirectorateAuthorityResolver
from .directorate_capabilities import DirectorateCapabilityResolver
from .directorate_impact import DirectorateImpactAnalyzer
from .directorate_projection import ConstitutionalDirectorateProjectionEngine
from .directorate_queries import ConstitutionalDirectorateQueryService
from .directorate_review import DirectorateReviewEngine

@dataclass(frozen=True)
class ExecutiveGovernanceService:
    queries: ConstitutionalDirectorateQueryService
    authority: DirectorateAuthorityResolver
    capabilities: DirectorateCapabilityResolver
    reviews: DirectorateReviewEngine
    impact: DirectorateImpactAnalyzer
    @classmethod
    def from_projection_directory(cls, *, pack3b2b1_directory: Path):
        assessment=ConstitutionalDirectorateProjectionEngine().assess(pack3b2b1_directory=pack3b2b1_directory)
        queries=ConstitutionalDirectorateQueryService(assessment['graph']); authority=DirectorateAuthorityResolver(queries); capabilities=DirectorateCapabilityResolver(); reviews=DirectorateReviewEngine(); impact=DirectorateImpactAnalyzer(authority,capabilities,reviews)
        return cls(queries,authority,capabilities,reviews,impact)
    def owner(self,path): return self.authority.resolve(path).owner_directorate_key
    def maintainers(self,path): return tuple(x.removeprefix('directorate:') for x in self.authority.resolve(path).maintainer_directorate_ids)
    def certifiers(self,path): return tuple(x.removeprefix('directorate:') for x in self.authority.resolve(path).certifier_directorate_ids)
    def reviewers(self,path): return tuple(x.removeprefix('directorate:') for x in self.reviews.determine(self.authority.resolve(path)).required_reviewer_directorate_ids)
    def executive_summary(self,path):
        authority=self.authority.resolve(path); capability=self.capabilities.resolve(path,authority); review=self.reviews.determine(authority)
        return {'authority':authority.to_dict(),'capability':capability.to_dict(),'review':review.to_dict()}
