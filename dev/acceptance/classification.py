from enum import Enum

class FailureClassification(str, Enum):
    ARCHITECTURE = "ARCH"
    INTEGRATION = "INTEG"
    RETRIEVAL = "RETR"
    QUALIFICATION = "QUAL"
    GROUNDING = "GRND"
    PROMPT = "PROMPT"
    MODEL = "LLM"
    RUNTIME = "RUNTIME"
    CONFIGURATION = "CONFIG"
    DATA = "DATA"
    TELEMETRY = "TELEM"
    MISSION_CONTROL = "UI"
    PERFORMANCE = "PERF"
    REGRESSION = "REG"
    OPERATOR = "OPERATOR"
    UNKNOWN = "UNKNOWN"

class FailureSeverity(str, Enum):
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"
    S4 = "S4"
