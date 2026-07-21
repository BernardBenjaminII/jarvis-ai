#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
rm -f "$PROJECT_ROOT/core/cognition/common/object_model.py" "$PROJECT_ROOT/core/cognition/common/cognitive_object.py" "$PROJECT_ROOT/tests/cognition/test_genesis_4r1_cognitive_object_model.py" "$PROJECT_ROOT/docs/architecture/cognition/01_cognitive_object_model.md" "$PROJECT_ROOT/docs/decisions/ADR-0021-cognitive-object-model.md" "$PROJECT_ROOT/dev/verification/verify_genesis_4r1_cognitive_object_model.py" "$PROJECT_ROOT/dev/verify_genesis_4r1.sh"
echo 'Genesis IV-R1 additive files removed.'
