import unittest

from core.retrieval.hybrid_rerank.query import analyze_query
from core.retrieval.hybrid_rerank.dedup import duplicate_key
from core.retrieval.hybrid_rerank.scoring import (
    lexical_component,
    title_component,
    hybrid_score,
)


class GenesisXB22Tests(unittest.TestCase):
    def test_query_terms_preserve_cpp(self):
        terms = analyze_query("How do C++ iterators work?")
        self.assertIn("c++", terms)
        self.assertIn("iterators", terms)

    def test_duplicate_key_normalizes_whitespace(self):
        a = duplicate_key("C++  iterators\nwork")
        b = duplicate_key("c++ iterators work")
        self.assertEqual(a, b)

    def test_lexical_rewards_both_terms(self):
        terms = ("c++", "iterators")
        good, matched = lexical_component(
            terms,
            "Using iterators with C++ STL algorithms.",
        )
        weak, _ = lexical_component(
            terms,
            "A loop iterator variable increments by one.",
        )
        self.assertGreater(good, weak)
        self.assertEqual(set(matched), {"c++", "iterators"})

    def test_title_component(self):
        terms = ("c++", "iterators")
        self.assertGreater(
            title_component(terms, "Modern C++ Programming"),
            title_component(terms, "Arduino Beginner Guide"),
        )

    def test_hybrid_semantics_not_only_signal(self):
        good = hybrid_score(0.73, 1.0, 0.5, 0.0)
        weak = hybrid_score(0.76, 0.5, 0.0, 0.0)
        self.assertGreater(good, weak)


if __name__ == "__main__":
    unittest.main()
