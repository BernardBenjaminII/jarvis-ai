import unittest

from core.retrieval.evidence_context.models import EvidenceBundle, EvidenceItem
from core.retrieval.evidence_grounding.focus import EvidenceFocusService


def item(
    rank,
    text,
    *,
    hybrid=0.80,
    lexical=0.50,
    matched=("iterators",),
    chunk_id=None,
):
    return EvidenceItem(
        evidence_id=f"doc1:chunk{rank}:anchor:{rank}",
        rank=rank,
        source_role="anchor",
        runtime_chunk_id=chunk_id or rank,
        runtime_document_id=1,
        document_title="Reference",
        file_path="/knowledge/reference.txt",
        chunk_uuid=f"chunk-{rank}",
        fragment_uuid=None,
        hybrid_score=hybrid,
        semantic_score=0.80,
        lexical_score=lexical,
        title_score=0.5,
        matched_terms=matched,
        text=text,
        chars=len(text),
    )


def bundle(query, evidence):
    return EvidenceBundle(
        query=query,
        query_terms=tuple(query.lower().replace("?", "").split()),
        accepted_candidates=len(evidence),
        rejected_candidates=0,
        expanded_neighbors=0,
        selected_evidence=tuple(evidence),
        total_chars=sum(x.chars for x in evidence),
        max_chars=12000,
    )


class GenesisXB24ATests(unittest.TestCase):
    def setUp(self):
        self.focus = EvidenceFocusService()

    def test_query_relevant_passage_can_outrank_generic_passage(self):
        generic = item(
            1,
            "Modern C++ includes auto and nullptr. "
            "Range based loops and lambdas are useful language features.",
            hybrid=0.90,
            lexical=0.20,
        )

        direct = item(
            2,
            "C++ iterators are used to traverse containers. "
            "begin() returns an iterator to the first element and end() "
            "marks the position after the final element. "
            "Incrementing the iterator moves through the container and "
            "dereferencing it accesses the current element.",
            hybrid=0.82,
            lexical=1.0,
            matched=("c++", "iterators"),
        )

        result = self.focus.focus(
            "How do C++ iterators work?",
            bundle("How do C++ iterators work?", [generic, direct]),
        )

        self.assertEqual(result.selected_evidence[0].runtime_chunk_id, 2)

    def test_irrelevant_passage_material_is_trimmed(self):
        source = item(
            1,
            "Unrelated introductory material about compilation.\n\n"
            "C++ iterators are used to traverse containers and access "
            "elements without exposing the container representation.\n\n"
            "Another unrelated discussion about build systems.",
            matched=("c++", "iterators"),
        )

        result = self.focus.focus(
            "How do C++ iterators work?",
            bundle("How do C++ iterators work?", [source]),
        )

        text = result.selected_evidence[0].text.lower()
        self.assertIn("iterators", text)
        self.assertIn("traverse", text)

    def test_provenance_survives_focus(self):
        source = item(
            1,
            "Iterators traverse a container.",
            chunk_id=777,
        )

        result = self.focus.focus(
            "What are iterators?",
            bundle("What are iterators?", [source]),
        )

        focused = result.selected_evidence[0]

        self.assertEqual(focused.runtime_chunk_id, 777)
        self.assertEqual(focused.runtime_document_id, source.runtime_document_id)
        self.assertEqual(focused.file_path, source.file_path)
        self.assertEqual(focused.chunk_uuid, source.chunk_uuid)

    def test_focus_is_deterministic(self):
        evidence = [
            item(1, "Iterators traverse containers."),
            item(2, "Iterators can be dereferenced to access elements."),
        ]
        b = bundle("How do iterators work?", evidence)

        first = self.focus.focus(b.query, b)
        second = self.focus.focus(b.query, b)

        self.assertEqual(first.to_dict(), second.to_dict())

    def test_focus_does_not_add_evidence(self):
        evidence = [
            item(1, "Iterators traverse containers."),
            item(2, "Iterator categories define supported operations."),
        ]
        b = bundle("How do iterators work?", evidence)

        result = self.focus.focus(b.query, b)

        self.assertEqual(
            {x.runtime_chunk_id for x in result.selected_evidence},
            {x.runtime_chunk_id for x in evidence},
        )


if __name__ == "__main__":
    unittest.main()
