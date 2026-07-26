class ExecutiveDecisionError(Exception): pass
class InvalidDecisionInputError(ExecutiveDecisionError): pass
class NoAdmissibleCourseOfActionError(ExecutiveDecisionError): pass
class DecisionPolicyError(ExecutiveDecisionError): pass
