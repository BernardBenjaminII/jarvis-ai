#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"

"${PYTHON_BIN}" - <<'PY'
from core.retrieval.qualification.lexical import analyze_lexical

cases = [
    ("What is SHA-256?", "calculating Secure Hash Algorithm (SHA)-256 hashes"),
    ("What is AES-256?", "Advanced Encryption Standard AES 256 encryption"),
    ("Explain RFC-9110", "The HTTP semantics specification is RFC 9110."),
    ("What is CVE-2025-12345?", "The vulnerability is tracked as CVE 2025 12345."),
    ("Explain _BitInt(32)", "A _BitInt(32) is a signed 32-bit integer."),
]

for query, text in cases:
    result = analyze_lexical(query, text)
    assert result.score >= 0.90, (query, result)

unrelated = analyze_lexical(
    "What is SHA-256?",
    "Arduino PWM pin configuration and analog input voltage.",
)
assert unrelated.score == 0.0

print("[PASS] Technical identifier normalization")
print("[PASS] SHA-256 runtime case")
print("[PASS] RFC and CVE equivalence")
print("[PASS] _BitInt equivalence")
print("[PASS] Unrelated evidence remains rejected")
PY
