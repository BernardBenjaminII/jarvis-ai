from __future__ import annotations

from .models import CertificationPolicy


def default_certification_policy() -> CertificationPolicy:
    return CertificationPolicy()
