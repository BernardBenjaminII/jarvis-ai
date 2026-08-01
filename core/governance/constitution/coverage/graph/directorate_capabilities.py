from __future__ import annotations

from dataclasses import dataclass
from .directorate_authority import AuthorityResolution

@dataclass(frozen=True)
class CapabilityResolution:
    capability_key: str
    repository_path: str
    owner_directorate_key: str | None
    constitutional_scope: tuple[str, ...]
    review_scopes: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            'capability_key': self.capability_key,
            'repository_path': self.repository_path,
            'owner_directorate_key': self.owner_directorate_key,
            'constitutional_scope': list(self.constitutional_scope),
            'review_scopes': list(self.review_scopes),
        }

class DirectorateCapabilityResolver:
    def resolve(self, repository_path: str, authority: AuthorityResolution) -> CapabilityResolution:
        normalized = repository_path.replace('\\', '/').strip('/')
        parts = tuple(part for part in normalized.split('/') if part)
        capability_key = '.'.join(parts[:3]) if parts else 'repository.root'
        constitutional_scope = tuple(sorted({authority.owner_directorate_key or 'unresolved', *(item.removeprefix('directorate:') for item in authority.certifier_directorate_ids)}))
        review_scopes = tuple(sorted({*(item.removeprefix('directorate:') for item in authority.maintainer_directorate_ids), *(item.removeprefix('directorate:') for item in authority.responsible_directorate_ids)}))
        return CapabilityResolution(capability_key, normalized, authority.owner_directorate_key, constitutional_scope, review_scopes)
