from enum import Enum
class StableStringEnum(str,Enum):
    def __str__(self): return self.value
class RealityClass(StableStringEnum): LIVE="live"; RECORDED="recorded"; EXECUTIVE="executive"; HUMAN="human"
class ObservationDomain(StableStringEnum): SYSTEM="system"; PLATFORM="platform"; SERVICE="service"; MISSION="mission"; KNOWLEDGE="knowledge"; CAPABILITY="capability"; USER="user"; NETWORK="network"; SECURITY="security"; RESOURCE="resource"; EXECUTION="execution"; COGNITION="cognition"; WORKFLOW="workflow"; CUSTOM="custom"
class ObservationKind(StableStringEnum): STATE="state"; EVENT="event"; MEASUREMENT="measurement"; TELEMETRY="telemetry"; KNOWLEDGE="knowledge"; DOCUMENT="document"; CONTENT="content"; RELATIONSHIP="relationship"; CAPABILITY="capability"; EXECUTION="execution"; HUMAN_REPORT="human_report"; CUSTOM="custom"
class SourceType(StableStringEnum): PLATFORM="platform"; SERVICE="service"; NETWORK="network"; SENSOR="sensor"; API="api"; DATABASE="database"; REPOSITORY="repository"; KNOWLEDGE_DOCUMENT="knowledge_document"; BOOK="book"; PAPER="paper"; FILE="file"; SOURCE_CODE="source_code"; IMAGE="image"; AUDIO="audio"; VIDEO="video"; TRANSCRIPT="transcript"; WEB_ARCHIVE="web_archive"; EXECUTIVE_SUBSYSTEM="executive_subsystem"; HUMAN="human"; CUSTOM="custom"
class SourceAuthority(StableStringEnum): UNKNOWN="unknown"; SYSTEM="system"; PRIMARY="primary"; SECONDARY="secondary"; TERTIARY="tertiary"; HUMAN="human"; DERIVED="derived"
class ObservationSeverity(StableStringEnum): NONE="none"; INFO="info"; NOTICE="notice"; WARNING="warning"; ERROR="error"; CRITICAL="critical"
class ObservationPriority(StableStringEnum): ROUTINE="routine"; LOW="low"; NORMAL="normal"; HIGH="high"; URGENT="urgent"; IMMEDIATE="immediate"
class ObservationStatus(StableStringEnum): ACTIVE="active"; SUPERSEDED="superseded"; RETRACTED="retracted"
