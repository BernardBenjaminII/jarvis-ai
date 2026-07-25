# ADR-0031 — Executive Decision Boundary

**Status:** Accepted  
**Date:** 2026-07-24

JARVIS shall separate reasoning from decision synthesis.

`core.cognition.reasoner` determines what is best supported.

`core.cognition.decision` determines which proposed course of action is
recommendable under utility, risk, confidence, and constraint policy.

Decision synthesis shall remain non-executing and shall not create missions or
authorize operations.
