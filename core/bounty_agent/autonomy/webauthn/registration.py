"""R9.15A.11C: verified WebAuthn reviewer registration."""

from __future__ import annotations

from dataclasses import dataclass

from webauthn import (
    generate_registration_options,
    options_to_json,
    verify_registration_response,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
)

from .store import CredentialStore


@dataclass(frozen=True)
class RegistrationConfig:
    rp_id: str = "localhost"
    rp_name: str = "JARVIS Security"
    origin: str = "http://localhost:8000"


class RegistrationService:
    def __init__(
        self,
        store: CredentialStore,
        config: RegistrationConfig,
    ):
        self.store = store
        self.config = config

    def begin(self, reviewer: str):
        challenge_id, challenge = (
            self.store.create_challenge(reviewer)
        )

        options = generate_registration_options(
            rp_id=self.config.rp_id,
            rp_name=self.config.rp_name,
            user_name=reviewer,
            challenge=challenge,
            authenticator_selection=(
                AuthenticatorSelectionCriteria(
                    user_verification=(
                        UserVerificationRequirement.REQUIRED
                    ),
                )
            ),
        )

        return {
            "challenge_id": challenge_id,
            "options": options_to_json(options),
        }

    def complete(
        self,
        reviewer: str,
        challenge_id: str,
        credential: dict,
    ):
        raise PermissionError("Legacy registration disabled")
