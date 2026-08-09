from __future__ import annotations

import unittest

from core.retrieval.qualification.lexical import (
    analyze_lexical,
    canonicalize_token,
    normalize_text,
    tokenize,
)


class GenesisIXA45Pack2B1Tests(unittest.TestCase):
    def assertStrongMatch(self, query: str, candidate: str) -> None:
        result = analyze_lexical(query, candidate)
        self.assertGreaterEqual(result.score, 0.90, msg=result)

    def test_sha_parenthetical_hyphen(self) -> None:
        self.assertStrongMatch(
            "What is SHA-256?",
            "calculating Secure Hash Algorithm (SHA)-256 hashes",
        )

    def test_sha_compact_equivalence(self) -> None:
        self.assertEqual(
            tokenize("SHA256"),
            tokenize("SHA-256"),
        )

    def test_sha_spaced_equivalence(self) -> None:
        self.assertStrongMatch(
            "SHA 256",
            "SHA-256 cryptographic hash",
        )

    def test_aes_equivalence(self) -> None:
        self.assertStrongMatch(
            "What is AES-256?",
            "Advanced Encryption Standard AES 256 encryption",
        )

    def test_rfc_equivalence(self) -> None:
        self.assertStrongMatch(
            "Explain RFC-9110",
            "The HTTP semantics specification is RFC 9110.",
        )

    def test_cve_equivalence(self) -> None:
        self.assertStrongMatch(
            "What is CVE-2025-12345?",
            "The vulnerability is tracked as CVE 2025 12345.",
        )

    def test_bitint_equivalence(self) -> None:
        result = analyze_lexical(
            "Explain _BitInt(32)",
            "A _BitInt(32) is a signed 32-bit integer.",
        )
        self.assertIn("bitint32", result.matched_tokens)
        self.assertGreaterEqual(result.score, 0.90)

    def test_cpp_preserved(self) -> None:
        self.assertIn("c++", tokenize("Explain C++ templates"))

    def test_csharp_preserved(self) -> None:
        self.assertIn("c#", tokenize("Explain C# delegates"))

    def test_unrelated_evidence_remains_rejected(self) -> None:
        result = analyze_lexical(
            "What is SHA-256?",
            "Arduino PWM pin configuration and analog input voltage.",
        )
        self.assertEqual(result.score, 0.0)
        self.assertEqual(result.matched_tokens, ())


if __name__ == "__main__":
    unittest.main()
