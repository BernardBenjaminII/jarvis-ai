from enum import Enum
class DecisionStatus(str, Enum):
    SELECTED='selected'; ABSTAINED='abstained'; BLOCKED='blocked'
class CandidateDisposition(str, Enum):
    ELIGIBLE='eligible'; REJECTED_CONSTITUTION='rejected_constitution'; REJECTED_AUTHORITY='rejected_authority'; REJECTED_THRESHOLD='rejected_threshold'; NOT_SELECTED='not_selected'; SELECTED='selected'
class ConstitutionalStatus(str, Enum):
    PASS='pass'; FAIL='fail'
class AuthorityStatus(str, Enum):
    AUTHORIZED='authorized'; UNAUTHORIZED='unauthorized'
