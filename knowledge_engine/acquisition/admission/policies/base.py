"""
Base admission policy contract.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from knowledge_engine.acquisition.models import SourceCandidate

from ..models import AdmissionContext
from ..models import PolicyEvaluation


class AdmissionPolicy(ABC):
    """
    One deterministic admission rule.
    """

    policy_id: str

    priority: int

    @abstractmethod
    def evaluate(
        self,
        *,
        candidate: SourceCandidate,
        context: AdmissionContext,
    ) -> PolicyEvaluation:
        ...
