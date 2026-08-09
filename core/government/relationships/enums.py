from enum import Enum

class RelationshipKind(str, Enum):
    OWNS = "owns"
    COMMANDS = "commands"
    REPORTS_TO = "reports_to"
    DEPENDS_ON = "depends_on"
    SUPPORTS = "supports"
    ASSIGNED_TO = "assigned_to"
    MEMBER_OF = "member_of"
    OBSERVES = "observes"
    GOVERNS = "governs"
    IMPLEMENTS = "implements"

class RelationshipStatus(str, Enum):
    PROPOSED = "proposed"
    CERTIFIED = "certified"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RETIRED = "retired"
