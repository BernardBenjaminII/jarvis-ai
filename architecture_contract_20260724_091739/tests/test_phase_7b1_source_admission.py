"""Tests for JARVIS Gen 2 Phase VII-B1 source admission."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from knowledge_engine.acquisition_control import (
    AdmissionPolicy,
    AdmissionReason,
    AdmissionStatus,
    SourceAdmissionService,
    SourceKind,
    SourceProposal,
    SourceTrustTier,
    normalize_source,
)


class SourceNormalizationTests(unittest.TestCase):
    def test_https_source_is_canonicalized(self) -> None:
        source = normalize_source(
            SourceProposal(
                source_id="nist-csrc",
                display_name="  NIST   CSRC  ",
                location=(
                    "HTTPS://CSRC.NIST.GOV:443/publications/../publications/"
                    "?z=9&a=2#ignored-fragment"
                ),
                kind=SourceKind.HTTPS,
                trust_tier=SourceTrustTier.OFFICIAL,
            )
        )

        self.assertEqual(source.display_name, "NIST CSRC")
        self.assertEqual(source.host, "csrc.nist.gov")
        self.assertEqual(
            source.canonical_location,
            "https://csrc.nist.gov/publications/?a=2&z=9",
        )
        self.assertEqual(len(source.fingerprint), 64)

    def test_equivalent_urls_have_same_fingerprint(self) -> None:
        first = normalize_source(
            SourceProposal(
                source_id="example",
                display_name="Example",
                location="https://EXAMPLE.com:443/docs?b=2&a=1",
                kind=SourceKind.HTTPS,
                trust_tier=SourceTrustTier.INSTITUTIONAL,
            )
        )
        second = normalize_source(
            SourceProposal(
                source_id="example",
                display_name="Example",
                location="https://example.com/docs?a=1&b=2#fragment",
                kind=SourceKind.HTTPS,
                trust_tier=SourceTrustTier.INSTITUTIONAL,
            )
        )

        self.assertEqual(
            first.canonical_location,
            second.canonical_location,
        )
        self.assertEqual(first.fingerprint, second.fingerprint)

    def test_url_credentials_are_rejected(self) -> None:
        decision = SourceAdmissionService().evaluate(
            SourceProposal(
                source_id="credential-source",
                display_name="Credential Source",
                location="https://user:password@example.com/private",
                kind=SourceKind.HTTPS,
                trust_tier=SourceTrustTier.OFFICIAL,
            )
        )

        self.assertEqual(decision.status, AdmissionStatus.REJECTED)
        self.assertEqual(
            decision.reason,
            AdmissionReason.URL_CREDENTIALS_FORBIDDEN,
        )

    def test_http_is_not_supported(self) -> None:
        decision = SourceAdmissionService().evaluate(
            SourceProposal(
                source_id="insecure-source",
                display_name="Insecure Source",
                location="http://example.com",
                kind=SourceKind.HTTPS,
            )
        )

        self.assertEqual(decision.status, AdmissionStatus.REJECTED)
        self.assertEqual(
            decision.reason,
            AdmissionReason.UNSUPPORTED_SCHEME,
        )

    def test_invalid_source_id_is_rejected(self) -> None:
        decision = SourceAdmissionService().evaluate(
            SourceProposal(
                source_id="../bad identifier",
                display_name="Invalid Source",
                location="https://example.com",
                kind=SourceKind.HTTPS,
            )
        )

        self.assertEqual(decision.status, AdmissionStatus.REJECTED)
        self.assertEqual(
            decision.reason,
            AdmissionReason.INVALID_SOURCE_ID,
        )

    def test_contracts_are_immutable(self) -> None:
        proposal = SourceProposal(
            source_id="immutable",
            display_name="Immutable",
            location="https://example.com",
            kind=SourceKind.HTTPS,
        )

        with self.assertRaises(FrozenInstanceError):
            proposal.source_id = "changed"  # type: ignore[misc]

        with self.assertRaises(TypeError):
            proposal.metadata["changed"] = True  # type: ignore[index]


class SourceAdmissionPolicyTests(unittest.TestCase):
    def test_official_source_is_accepted(self) -> None:
        decision = SourceAdmissionService().evaluate(
            SourceProposal(
                source_id="nist",
                display_name="NIST",
                location="https://www.nist.gov/publications",
                kind=SourceKind.HTTPS,
                trust_tier=SourceTrustTier.OFFICIAL,
            )
        )

        self.assertTrue(decision.accepted)
        self.assertEqual(
            decision.reason,
            AdmissionReason.ACCEPTED_BY_POLICY,
        )

    def test_unknown_source_requires_review(self) -> None:
        decision = SourceAdmissionService().evaluate(
            SourceProposal(
                source_id="unknown",
                display_name="Unknown",
                location="https://example.com",
                kind=SourceKind.HTTPS,
                trust_tier=SourceTrustTier.UNKNOWN,
            )
        )

        self.assertTrue(decision.requires_review)
        self.assertEqual(
            decision.reason,
            AdmissionReason.UNKNOWN_TRUST_REQUIRES_REVIEW,
        )

    def test_community_source_requires_review(self) -> None:
        decision = SourceAdmissionService().evaluate(
            SourceProposal(
                source_id="community",
                display_name="Community",
                location="https://community.example.com",
                kind=SourceKind.HTTPS,
                trust_tier=SourceTrustTier.COMMUNITY,
            )
        )

        self.assertTrue(decision.requires_review)
        self.assertEqual(
            decision.reason,
            AdmissionReason.COMMUNITY_SOURCE_REQUIRES_REVIEW,
        )

    def test_restricted_source_is_rejected(self) -> None:
        decision = SourceAdmissionService().evaluate(
            SourceProposal(
                source_id="restricted",
                display_name="Restricted",
                location="https://example.com/restricted",
                kind=SourceKind.HTTPS,
                trust_tier=SourceTrustTier.RESTRICTED,
            )
        )

        self.assertTrue(decision.rejected)
        self.assertEqual(
            decision.reason,
            AdmissionReason.RESTRICTED_SOURCE,
        )

    def test_network_sources_can_be_disabled(self) -> None:
        service = SourceAdmissionService(
            AdmissionPolicy(allow_network_sources=False)
        )

        decision = service.evaluate(
            SourceProposal(
                source_id="network",
                display_name="Network",
                location="https://example.com",
                kind=SourceKind.HTTPS,
                trust_tier=SourceTrustTier.OFFICIAL,
            )
        )

        self.assertEqual(
            decision.reason,
            AdmissionReason.NETWORK_SOURCE_DISABLED,
        )

    def test_host_allowlist_permits_subdomain(self) -> None:
        service = SourceAdmissionService(
            AdmissionPolicy(
                allowed_hosts=frozenset({"nist.gov"}),
            )
        )

        decision = service.evaluate(
            SourceProposal(
                source_id="nist-csrc",
                display_name="NIST CSRC",
                location="https://csrc.nist.gov/publications",
                kind=SourceKind.HTTPS,
                trust_tier=SourceTrustTier.OFFICIAL,
            )
        )

        self.assertTrue(decision.accepted)

    def test_host_allowlist_rejects_unlisted_host(self) -> None:
        service = SourceAdmissionService(
            AdmissionPolicy(
                allowed_hosts=frozenset({"nist.gov"}),
            )
        )

        decision = service.evaluate(
            SourceProposal(
                source_id="example",
                display_name="Example",
                location="https://example.com",
                kind=SourceKind.HTTPS,
                trust_tier=SourceTrustTier.OFFICIAL,
            )
        )

        self.assertEqual(
            decision.reason,
            AdmissionReason.HOST_NOT_ALLOWED,
        )

    def test_blocklist_overrides_general_admission(self) -> None:
        service = SourceAdmissionService(
            AdmissionPolicy(
                blocked_hosts=frozenset({"blocked.example.com"}),
            )
        )

        decision = service.evaluate(
            SourceProposal(
                source_id="blocked",
                display_name="Blocked",
                location="https://blocked.example.com",
                kind=SourceKind.HTTPS,
                trust_tier=SourceTrustTier.OFFICIAL,
            )
        )

        self.assertEqual(
            decision.reason,
            AdmissionReason.HOST_BLOCKED,
        )

    def test_local_source_within_allowed_root_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            source_path = root / "incoming" / "manual.pdf"

            service = SourceAdmissionService(
                AdmissionPolicy(
                    allowed_local_roots=(str(root),),
                )
            )

            decision = service.evaluate(
                SourceProposal(
                    source_id="local-manual",
                    display_name="Local Manual",
                    location=str(source_path),
                    kind=SourceKind.LOCAL_FILE,
                    trust_tier=SourceTrustTier.INSTITUTIONAL,
                )
            )

            self.assertTrue(decision.accepted)

    def test_local_source_outside_allowed_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as allowed:
            with tempfile.TemporaryDirectory() as outside:
                service = SourceAdmissionService(
                    AdmissionPolicy(
                        allowed_local_roots=(allowed,),
                    )
                )

                decision = service.evaluate(
                    SourceProposal(
                        source_id="outside",
                        display_name="Outside",
                        location=str(Path(outside) / "manual.pdf"),
                        kind=SourceKind.LOCAL_FILE,
                        trust_tier=SourceTrustTier.OFFICIAL,
                    )
                )

                self.assertEqual(
                    decision.reason,
                    AdmissionReason.PATH_OUTSIDE_ALLOWED_ROOTS,
                )


class DeterminismTests(unittest.TestCase):
    def test_repeated_evaluation_is_identical(self) -> None:
        proposal = SourceProposal(
            source_id="deterministic-source",
            display_name="Deterministic Source",
            location="https://example.com/archive?year=2026&type=pdf",
            kind=SourceKind.HTTPS,
            trust_tier=SourceTrustTier.INSTITUTIONAL,
            metadata={"owner": "test"},
        )

        service = SourceAdmissionService()
        first = service.evaluate(proposal)
        second = service.evaluate(proposal)

        self.assertEqual(first, second)
        self.assertEqual(
            first.source.fingerprint,
            second.source.fingerprint,
        )


if __name__ == "__main__":
    unittest.main()
