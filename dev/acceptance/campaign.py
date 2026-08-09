from dataclasses import dataclass
from typing import Iterable
from .test_case import AcceptanceTestCase

@dataclass(frozen=True, slots=True)
class CampaignDefinition:
    campaign_id: str
    name: str
    version: str
    tests: tuple[AcceptanceTestCase, ...]

    @classmethod
    def create(cls, *, campaign_id, name, version, tests: Iterable[AcceptanceTestCase]):
        return cls(campaign_id, name, version, tuple(tests))
