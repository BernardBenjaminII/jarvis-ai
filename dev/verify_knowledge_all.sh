#!/usr/bin/env bash

###############################################################################
#
# JARVIS GEN 2
#
# Knowledge Domain Verification Orchestrator
#
###############################################################################

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

exec ./dev/run_verification_manifest.sh \
    "KNOWLEDGE DOMAIN" \
    "dev/verification/manifests/knowledge.manifest"
