#!/usr/bin/env bash

###############################################################################
#
# JARVIS GENESIS
#
# Genesis Domain Verification Orchestrator
#
###############################################################################

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

exec ./dev/run_verification_manifest.sh \
    "GENESIS DOMAIN" \
    "dev/verification/manifests/genesis.manifest"
