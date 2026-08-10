import unittest
from core.retrieval.evidence_context.models import EvidenceBundle,EvidenceItem
from core.retrieval.evidence_grounding.adapter import EvidenceBundleQualificationAdapter
from core.retrieval.evidence_grounding.focus import EvidenceFocusService,detect_query_intent
from core.retrieval.grounded_answer import GroundedAnswerEngine

def item(rank,text,*,evidence_id=None,hybrid=.80,lexical=.50,matched=('iterators',),chunk_id=None,role='anchor'):
    return EvidenceItem(evidence_id=evidence_id or f'doc1:chunk{rank}:anchor:{rank}',rank=rank,source_role=role,runtime_chunk_id=chunk_id or rank,runtime_document_id=1,document_title='Reference',file_path='/knowledge/reference.txt',chunk_uuid=f'chunk-{rank}',fragment_uuid=None,hybrid_score=hybrid,semantic_score=.80,lexical_score=lexical,title_score=.5,matched_terms=matched,text=text,chars=len(text))

def bundle(query,evidence,query_terms=('c++','iterators')):
    return EvidenceBundle(query=query,query_terms=query_terms,accepted_candidates=len(evidence),rejected_candidates=0,expanded_neighbors=0,selected_evidence=tuple(evidence),total_chars=sum(x.chars for x in evidence),max_chars=12000)

class GenesisXB24A1Tests(unittest.TestCase):
    def setUp(self): self.focus=EvidenceFocusService(); self.adapter=EvidenceBundleQualificationAdapter()
    def test_detects_mechanism_intent(self): self.assertEqual(detect_query_intent('How do C++ iterators work?'),'mechanism')
    def test_detects_definition_intent(self): self.assertEqual(detect_query_intent('What is a mutex?'),'definition')
    def test_detects_comparison_intent(self): self.assertEqual(detect_query_intent('What is the difference between TCP and UDP?'),'comparison')
    def test_mechanism_evidence_outranks_term_mentions(self):
        generic=item(1,'C++11 introduced several modern language features. Automatic type deduction is useful for iterator types. Range based loops are another C++ feature.',hybrid=.90,lexical=1.0,matched=('c++','iterators'),chunk_id=165)
        mechanism=item(2,'C++ iterators traverse containers. begin() returns an iterator to the first element, incrementing the iterator advances through the container, and dereferencing it accesses the current element. end() marks the position after the final element.',hybrid=.68,lexical=1.0,matched=('c++','iterators'),chunk_id=149)
        r=self.focus.focus_result('How do C++ iterators work?',bundle('How do C++ iterators work?',[generic,mechanism])); self.assertEqual(r.bundle.selected_evidence[0].runtime_chunk_id,149); self.assertGreater(r.utility_scores[mechanism.evidence_id],r.utility_scores[generic.evidence_id])
    def test_utility_propagates_to_qualification_final(self):
        source=item(1,'Iterators traverse containers.',hybrid=.70,evidence_id='ev1'); b=bundle('How do iterators work?',[source],('iterators',)); q=self.adapter.convert(b,utility_scores={'ev1':.91},query_intent='mechanism')
        self.assertAlmostEqual(q.accepted[0].score.final,.91); self.assertAlmostEqual(q.accepted[0].candidate.retrieval_score,.70); self.assertAlmostEqual(q.accepted[0].candidate.metadata['synthesis_utility_score'],.91); self.assertEqual(q.accepted[0].candidate.metadata['query_intent'],'mechanism')
    def test_grounded_engine_ranking_uses_propagated_utility(self):
        weak=item(1,'Iterator is mentioned here.',evidence_id='weak',hybrid=.95,chunk_id=1); strong=item(2,'Iterators traverse containers and dereferencing accesses elements.',evidence_id='strong',hybrid=.60,chunk_id=2); b=bundle('How do iterators work?',[weak,strong],('iterators',)); q=self.adapter.convert(b,utility_scores={'weak':.40,'strong':.95},query_intent='mechanism'); plan=GroundedAnswerEngine().plan('How do iterators work?',q); self.assertEqual(plan.ranked_evidence[0].source_id,'runtime-document:1:chunk:2')
    def test_provenance_survives_intent_focus(self):
        source=item(1,'Iterators traverse a container by advancing from one element to another.',chunk_id=777); r=self.focus.focus_result('How do iterators work?',bundle('How do iterators work?',[source],('iterators',))); f=r.bundle.selected_evidence[0]; self.assertEqual(f.runtime_chunk_id,777); self.assertEqual(f.chunk_uuid,source.chunk_uuid); self.assertEqual(f.file_path,source.file_path)
if __name__=='__main__': unittest.main()
