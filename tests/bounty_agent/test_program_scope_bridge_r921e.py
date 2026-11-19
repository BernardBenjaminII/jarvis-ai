"""R9.21E read-only authorization boundary tests."""

from unittest.mock import Mock, patch

from core.bounty_agent.autonomy.program_scope_bridge_r921e import (
    assess_authorization_binding,
)

MODULE = (
    "core.bounty_agent.autonomy."
    "program_scope_bridge_r921e.assess_reviewed_target"
)


def check(
    *,
    hostname="example.org",
    authorization_id="reviewed-auth-id",
    program="Example Program",
    permitted=True,
    assessment=None,
    side_effect=None,
):
    store = Mock()
    scope = Mock()
    scope.program = program
    scope.permits_host.return_value = permitted
    store.live_scope.return_value = scope

    advisory = assessment or {
        "classification": "listed_in_unverified_draft",
        "advisory_eligible": True,
        "execution_authorized": False,
    }

    with patch(
        MODULE, return_value=advisory, side_effect=side_effect
    ):
        outcome = assess_authorization_binding(
            draft={"program": "Example Program"},
            review={"review_status": "operator_attested"},
            hostname=hostname,
            authorization_id=authorization_id,
            authorization_store=store,
        )

    return outcome, store


def test_live_authorization_match_is_still_nonexecuting():
    outcome, store = check()
    assert outcome["authorization_match"] is True
    assert outcome["proposal_ready"] is False
    assert outcome["execution_started"] is False
    assert outcome["submission_authorized"] is False
    store.live_scope.assert_called_once_with("reviewed-auth-id")


def test_imported_policy_alone_cannot_authorize():
    outcome, store = check(authorization_id=None)
    assert outcome["authorization_match"] is False
    assert outcome["reason"] == "separate_authorization_required"
    store.live_scope.assert_not_called()


def test_wildcards_fail_closed():
    outcome, store = check(hostname="*.example.org")
    assert outcome["authorization_match"] is False
    store.live_scope.assert_not_called()


def test_out_of_scope_target_fails_closed():
    outcome, store = check(
        assessment={
            "classification": "excluded",
            "advisory_eligible": False,
            "execution_authorized": False,
        }
    )
    assert outcome["authorization_match"] is False
    store.live_scope.assert_not_called()


def test_expired_policy_review_fails_closed():
    outcome, store = check(
        side_effect=ValueError("Review expired")
    )
    assert outcome["authorization_match"] is False
    store.live_scope.assert_not_called()


def test_authorization_program_mismatch_fails_closed():
    outcome, _ = check(program="Different Program")
    assert outcome["authorization_match"] is False


def test_authorization_target_exclusion_fails_closed():
    outcome, _ = check(permitted=False)
    assert outcome["authorization_match"] is False


def test_revoked_or_expired_authorization_fails_closed():
    outcome, store = check()
    store.live_scope.side_effect = ValueError("Revoked")

    with patch(
        MODULE,
        return_value={
            "classification": "listed_in_unverified_draft",
            "advisory_eligible": True,
            "execution_authorized": False,
        },
    ):
        outcome = assess_authorization_binding(
            draft={"program": "Example Program"},
            review={},
            hostname="example.org",
            authorization_id="reviewed-auth-id",
            authorization_store=store,
        )

    assert outcome["authorization_match"] is False
    assert outcome["execution_started"] is False


def test_advisory_cannot_claim_execution_authorization():
    outcome, store = check(
        assessment={
            "classification": "listed_in_unverified_draft",
            "advisory_eligible": True,
            "execution_authorized": True,
        }
    )
    assert outcome["authorization_match"] is False
    store.live_scope.assert_not_called()
