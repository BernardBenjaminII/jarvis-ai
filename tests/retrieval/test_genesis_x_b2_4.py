import unittest
from core.retrieval.evidence_context.models import EvidenceBundle, EvidenceItem
from core.retrieval.evidence_grounding.adapter import EvidenceBundleQualificationAdapter
from core.retrieval.grounded_answer import AnswerKnowledgeState, GroundedAnswerEngine

def item(rank=1,hybrid=0.90,semantic=0.88,text="C++ iterators provide a generalized mechanism for traversing containers."):
    return EvidenceItem(
        evidence_id=f"doc1:chunk{rank}:anchor:{rank}",rank=rank,source_role="anchor",
        runtime_chunk_id=rank,runtime_document_id=1,document_title="C++ Reference",
        file_path="/knowledge/cpp/reference.txt",chunk_uuid=f"chunk-{rank}",fragment_uuid=None,
        hybrid_score=hybrid,semantic_score=semantic,lexical_score=1.0,title_score=0.8,
        matched_terms=("c++","iterators"),text=text,chars=len(text),
    )

class GenesisXB24Tests(unittest.TestCase):
    def setUp(self): self.adapter=EvidenceBundleQualificationAdapter()
    def bundle(self,evidence):
        return EvidenceBundle(
            query="How do C++ iterators work?",query_terms=("c++","iterators"),
            accepted_candidates=len(evidence),rejected_candidates=0,expanded_neighbors=0,
            selected_evidence=tuple(evidence),total_chars=sum(x.chars for x in evidence),max_chars=12000,
        )
    def test_adapter_preserves_evidence(self):
        source=item(); result=self.adapter.convert(self.bundle([source]))
        self.assertEqual(len(result.accepted),1)
        c=result.accepted[0].candidate
        self.assertEqual(c.excerpt,source.text)
        self.assertEqual(c.source_path,source.file_path)
        self.assertEqual(c.metadata["runtime_chunk_id"],source.runtime_chunk_id)
    def test_adapter_preserves_score(self):
        source=item(hybrid=0.83); result=self.adapter.convert(self.bundle([source]))
        self.assertAlmostEqual(result.accepted[0].score.final,0.83)
    def test_grounded_engine_accepts_adapter_output(self):
        result=self.adapter.convert(self.bundle([item()]))
        plan=GroundedAnswerEngine().plan("How do C++ iterators work?",result)
        self.assertTrue(plan.ranked_evidence); self.assertTrue(plan.citations)
        self.assertIn(plan.state,(AnswerKnowledgeState.KNOWN,AnswerKnowledgeState.PARTIAL))
    def test_citation_contract_survives_adapter(self):
        result=self.adapter.convert(self.bundle([item(rank=1),item(rank=2,text="Iterator categories describe supported operations and traversal capabilities.")]))
        plan=GroundedAnswerEngine().plan("Q",result)
        self.assertEqual([x.citation_id for x in plan.citations],["C1","C2"])
    def test_empty_bundle_becomes_unknown(self):
        plan=GroundedAnswerEngine().plan("Q",self.adapter.convert(self.bundle([])))
        self.assertEqual(plan.state,AnswerKnowledgeState.UNKNOWN)

if __name__=="__main__":
    unittest.main()
