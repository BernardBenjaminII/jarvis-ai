from dataclasses import dataclass


@dataclass
class QualityReport:

    passed: bool

    score: int

    errors: list[str]

    warnings: list[str]
