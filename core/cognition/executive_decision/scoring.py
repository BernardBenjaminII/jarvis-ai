from .contracts import DecisionPolicy, EvaluatedCourseOfAction
def component_scores(c): return {'mission_alignment':c.mission_alignment,'evidence_strength':c.evidence_strength,'confidence':c.confidence,'safety':c.safety,'resource_efficiency':c.resource_efficiency,'time_utility':c.time_utility}
def weighted_score(c,p): return round(c.mission_alignment*p.mission_alignment_weight+c.evidence_strength*p.evidence_strength_weight+c.confidence*p.confidence_weight+c.safety*p.safety_weight+c.resource_efficiency*p.resource_efficiency_weight+c.time_utility*p.time_utility_weight,12)
