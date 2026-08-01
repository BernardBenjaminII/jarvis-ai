from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from .directorate_queries import ConstitutionalDirectorateQueryService


@dataclass(frozen=True)
class AuthorityResolution:
    repository_path: str
    ownership_domain_id: str | None
    owner_directorate_id: str | None
    owner_directorate_key: str | None
    maintainer_directorate_ids: tuple[str, ...]
    certifier_directorate_ids: tuple[str, ...]
    responsible_directorate_ids: tuple[str, ...]

    @property
    def resolved(self) -> bool:
        return self.owner_directorate_id is not None

    def to_dict(self) -> dict[str, object]:
        return {
            'repository_path': self.repository_path,
            'ownership_domain_id': self.ownership_domain_id,
            'owner_directorate_id': self.owner_directorate_id,
            'owner_directorate_key': self.owner_directorate_key,
            'maintainer_directorate_ids': list(self.maintainer_directorate_ids),
            'certifier_directorate_ids': list(self.certifier_directorate_ids),
            'responsible_directorate_ids': list(self.responsible_directorate_ids),
            'resolved': self.resolved,
        }


class DirectorateAuthorityResolver:
    def __init__(self, query_service: ConstitutionalDirectorateQueryService) -> None:
        self._queries = query_service

    @staticmethod
    def _normalize(path: str) -> str:
        return str(PurePosixPath(path.replace('\\', '/'))).strip('/')

    def _best_domain(self, path: str):
        normalized = self._normalize(path)
        candidates = []
        for domain in self._queries.ownership_domains():
            repository_path = str(domain.attributes.get('repository_path', '')).strip('/')
            if normalized == repository_path or normalized.startswith(repository_path + '/'):
                candidates.append((len(repository_path), domain))
        if not candidates:
            return None
        return sorted(candidates, key=lambda item: (-item[0], item[1].node_id))[0][1]

    def resolve(self, repository_path: str) -> AuthorityResolution:
        domain = self._best_domain(repository_path)
        if domain is None:
            return AuthorityResolution(self._normalize(repository_path), None, None, None, (), (), ())
        owner = self._queries.owner_of_domain(domain.node_id)
        maintainers = self._queries.maintainers_of_domain(domain.node_id)
        certifiers = self._queries.certifiers_of_domain(domain.node_id)
        responsible = self._queries.responsible_directorates_for_domain(domain.node_id)
        return AuthorityResolution(
            repository_path=self._normalize(repository_path),
            ownership_domain_id=domain.node_id,
            owner_directorate_id=owner.node_id if owner else None,
            owner_directorate_key=owner.canonical_key if owner else None,
            maintainer_directorate_ids=tuple(node.node_id for node in maintainers),
            certifier_directorate_ids=tuple(node.node_id for node in certifiers),
            responsible_directorate_ids=tuple(node.node_id for node in responsible),
        )
