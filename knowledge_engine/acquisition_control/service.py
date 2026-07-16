"""
Source-admission policy service for JARVIS Phase VII-B1.
"""

from __future__ import annotations

from .contracts import (
    AdmissionDecision,
    AdmissionPolicy,
    AdmissionReason,
    AdmissionStatus,
    NormalizedSource,
    SourceKind,
    SourceProposal,
    SourceTrustTier,
)
from .normalization import (
    SourceNormalizationError,
    is_within_root,
    normalize_source,
)


class SourceAdmissionService:
    """
    Normalize and evaluate source proposals against an immutable policy.

    The service does not connect to a network, inspect remote content,
    mutate the filesystem, or write to the knowledge catalog.
    """

    def __init__(
        self,
        policy: AdmissionPolicy | None = None,
    ) -> None:
        if policy is not None and not isinstance(policy, AdmissionPolicy):
            raise TypeError("policy must be an AdmissionPolicy or None")

        self._policy = policy or AdmissionPolicy()

    @property
    def policy(self) -> AdmissionPolicy:
        """Return the active immutable admission policy."""

        return self._policy

    def evaluate(
        self,
        proposal: SourceProposal,
    ) -> AdmissionDecision:
        """Normalize and evaluate one proposal."""

        if not isinstance(proposal, SourceProposal):
            raise TypeError("proposal must be a SourceProposal")

        try:
            source = normalize_source(proposal)
        except SourceNormalizationError as exc:
            return exc.to_decision()

        return self.evaluate_normalized(source)

    def evaluate_normalized(
        self,
        source: NormalizedSource,
    ) -> AdmissionDecision:
        """Evaluate an already normalized source."""

        if not isinstance(source, NormalizedSource):
            raise TypeError("source must be a NormalizedSource")

        policy = self._policy

        if source.trust_tier is SourceTrustTier.RESTRICTED:
            return self._reject(
                source,
                AdmissionReason.RESTRICTED_SOURCE,
                "Restricted sources cannot enter acquisition planning",
            )

        if source.kind is SourceKind.HTTPS:
            network_decision = self._evaluate_network_source(source)
            if network_decision is not None:
                return network_decision
        else:
            local_decision = self._evaluate_local_source(source)
            if local_decision is not None:
                return local_decision

        if (
            source.trust_tier is SourceTrustTier.UNKNOWN
            and policy.review_unknown_sources
        ):
            return self._review(
                source,
                AdmissionReason.UNKNOWN_TRUST_REQUIRES_REVIEW,
                "Unknown-trust source requires manual approval",
            )

        if (
            source.trust_tier is SourceTrustTier.COMMUNITY
            and policy.review_community_sources
        ):
            return self._review(
                source,
                AdmissionReason.COMMUNITY_SOURCE_REQUIRES_REVIEW,
                "Community source requires manual approval",
            )

        return AdmissionDecision(
            status=AdmissionStatus.ACCEPTED,
            reason=AdmissionReason.ACCEPTED_BY_POLICY,
            message="Source satisfies the active admission policy",
            source=source,
            diagnostics={
                "fingerprint": source.fingerprint,
                "kind": source.kind.value,
                "trust_tier": source.trust_tier.value,
            },
        )

    def _evaluate_network_source(
        self,
        source: NormalizedSource,
    ) -> AdmissionDecision | None:
        policy = self._policy

        if not policy.allow_network_sources:
            return self._reject(
                source,
                AdmissionReason.NETWORK_SOURCE_DISABLED,
                "Network sources are disabled by policy",
            )

        host = source.host
        if not host:
            return self._reject(
                source,
                AdmissionReason.INVALID_LOCATION,
                "Normalized network source has no hostname",
            )

        if self._host_matches(host, policy.blocked_hosts):
            return self._reject(
                source,
                AdmissionReason.HOST_BLOCKED,
                "Source hostname is blocked by policy",
                diagnostics={"host": host},
            )

        if (
            policy.allowed_hosts
            and not self._host_matches(host, policy.allowed_hosts)
        ):
            return self._reject(
                source,
                AdmissionReason.HOST_NOT_ALLOWED,
                "Source hostname is not included in the policy allowlist",
                diagnostics={"host": host},
            )

        return None

    def _evaluate_local_source(
        self,
        source: NormalizedSource,
    ) -> AdmissionDecision | None:
        policy = self._policy

        if not policy.allow_local_sources:
            return self._reject(
                source,
                AdmissionReason.LOCAL_SOURCE_DISABLED,
                "Local sources are disabled by policy",
            )

        if policy.allowed_local_roots and not any(
            is_within_root(source.canonical_location, root)
            for root in policy.allowed_local_roots
        ):
            return self._reject(
                source,
                AdmissionReason.PATH_OUTSIDE_ALLOWED_ROOTS,
                "Local source is outside every allowed source root",
                diagnostics={
                    "path": source.canonical_location,
                    "allowed_roots": policy.allowed_local_roots,
                },
            )

        return None

    @staticmethod
    def _host_matches(
        host: str,
        configured_hosts: frozenset[str],
    ) -> bool:
        """
        Match an exact host or one of its subdomains.

        An allowlist entry of ``nist.gov`` permits both ``nist.gov`` and
        ``csrc.nist.gov``. It does not permit ``notnist.gov``.
        """

        normalized = host.lower().rstrip(".")

        return any(
            normalized == configured
            or normalized.endswith(f".{configured}")
            for configured in configured_hosts
        )

    @staticmethod
    def _reject(
        source: NormalizedSource,
        reason: AdmissionReason,
        message: str,
        *,
        diagnostics: dict | None = None,
    ) -> AdmissionDecision:
        payload = {
            "fingerprint": source.fingerprint,
            "kind": source.kind.value,
        }
        payload.update(diagnostics or {})

        return AdmissionDecision(
            status=AdmissionStatus.REJECTED,
            reason=reason,
            message=message,
            source=source,
            diagnostics=payload,
        )

    @staticmethod
    def _review(
        source: NormalizedSource,
        reason: AdmissionReason,
        message: str,
    ) -> AdmissionDecision:
        return AdmissionDecision(
            status=AdmissionStatus.REVIEW_REQUIRED,
            reason=reason,
            message=message,
            source=source,
            diagnostics={
                "fingerprint": source.fingerprint,
                "kind": source.kind.value,
                "trust_tier": source.trust_tier.value,
            },
        )
