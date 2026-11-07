"""R9.15A.11G: verified first-key registration."""

from __future__ import annotations

import time

from webauthn import verify_registration_response

from .first_key import FirstKeyEnrollment
from .registration import RegistrationConfig, RegistrationService


class VerifiedFirstKeyEnrollment:
    def __init__(self, store, config=None):
        self.store = store
        self.config = config or RegistrationConfig()
        self.first_key = FirstKeyEnrollment(store)
        self.registration = RegistrationService(
            store, self.config
        )

    def begin(self, reviewer, ticket):
        # Challenge creation alone does not grant enrollment.
        result = self.registration.begin(reviewer)

        self.first_key.bind_challenge(
            ticket,
            reviewer,
            result["challenge_id"],
        )

        return result

    def complete(self, reviewer, challenge_id, credential):
        # Read the challenge without consuming it.
        # Verification must succeed before registration.
        with self.store.connection() as db:
            row = db.execute(
                """
                SELECT challenge, expires_at
                FROM challenges
                WHERE id = ? AND reviewer = ?
                """,
                (challenge_id, reviewer),
            ).fetchone()

        if row is None or row[1] <= int(time.time()):
            raise ValueError("Unknown or expired challenge")

        verified = verify_registration_response(
            credential=credential,
            expected_challenge=row[0],
            expected_rp_id=self.config.rp_id,
            expected_origin=self.config.origin,
            require_user_presence=True,
            require_user_verification=True,
        )

        # Register only cryptographically verified credential data.
        # The first-key state machine enforces ticket binding.
        self.first_key.register_verified_first_key(
            reviewer=reviewer,
            challenge_id=challenge_id,
            expected_challenge=row[0],
            credential_id=verified.credential_id,
            public_key=verified.credential_public_key,
            sign_count=verified.sign_count,
        )

        return {
            "status": "registered",
            "reviewer": reviewer,
        }
