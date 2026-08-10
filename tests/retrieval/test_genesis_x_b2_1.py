import unittest
import numpy as np

from core.retrieval.vector_search.math import (
    normalized,
    cosine_scores,
)


class GenesisXB21Tests(unittest.TestCase):
    def test_normalized_unit_length(self):
        v = normalized(np.asarray([3.0, 4.0], dtype=np.float32))
        self.assertAlmostEqual(float(np.linalg.norm(v)), 1.0, places=6)

    def test_cosine_ranking(self):
        q = np.asarray([1.0, 0.0], dtype=np.float32)
        m = np.asarray([
            [1.0, 0.0],
            [0.5, 0.5],
            [0.0, 1.0],
        ], dtype=np.float32)
        scores = cosine_scores(m, q)
        order = list(np.argsort(scores)[::-1])
        self.assertEqual(order, [0, 1, 2])

    def test_zero_query_rejected(self):
        with self.assertRaises(ValueError):
            normalized(np.asarray([0.0, 0.0], dtype=np.float32))


if __name__ == "__main__":
    unittest.main()
