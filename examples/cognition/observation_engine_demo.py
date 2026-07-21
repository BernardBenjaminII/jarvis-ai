from __future__ import annotations

from core.cognition.common.object_model import ProvenanceReference
from core.cognition.layers.observation import (
    ObservationDirector,
    ObservationInput,
    ObservationSourceMode,
)


def main() -> None:
    director = ObservationDirector()

    observation = director.observe(
        ObservationInput(
            content="Primary runtime health is nominal.",
            subject="primary-runtime",
            confidence=0.98,
            source_mode=ObservationSourceMode.SYSTEM,
            provenance=(
                ProvenanceReference(
                    source_id="runtime-health-check",
                    source_type="system",
                    locator="local://health",
                ),
            ),
        )
    )

    print(observation.to_canonical_json())
    print(f"hash={observation.deterministic_hash}")


if __name__ == "__main__":
    main()
