import unittest
from core.government.models import ConstitutionalIdentifier, ConstitutionalObjectKind
from core.government.relationships import (
    OrganizationalGraph, OrganizationalGraphError, OrganizationalRelationship,
    RelationshipKind, RelationshipStatus, relationship_from_dict,
)

def ident(kind, namespace, name):
    return ConstitutionalIdentifier(kind, namespace, name)

class GovernmentRelationshipTests(unittest.TestCase):
    def setUp(self):
        self.government = ident(ConstitutionalObjectKind.GOVERNMENT, "jarvis", "government")
        self.executive = ident(ConstitutionalObjectKind.EXECUTIVE, "government", "executive")
        self.knowledge = ident(ConstitutionalObjectKind.DIRECTORATE, "government", "knowledge")
        self.assimilation = ident(ConstitutionalObjectKind.DEPARTMENT, "knowledge", "assimilation")

    def test_identifier_is_deterministic(self):
        a = OrganizationalRelationship(self.knowledge, RelationshipKind.OWNS, self.assimilation)
        b = OrganizationalRelationship(self.knowledge, RelationshipKind.OWNS, self.assimilation)
        self.assertEqual(a.identifier, b.identifier)

    def test_round_trip(self):
        r = OrganizationalRelationship(
            self.knowledge, RelationshipKind.OWNS, self.assimilation,
            status=RelationshipStatus.ACTIVE,
            constitutional_basis=("GOA-0000 Article VIII",),
            metadata={"source": "registry"},
        )
        restored = relationship_from_dict(r.to_dict())
        self.assertEqual(restored, r)
        self.assertEqual(restored.fingerprint, r.fingerprint)

    def test_self_relationship_rejected(self):
        with self.assertRaises(ValueError):
            OrganizationalRelationship(
                self.knowledge, RelationshipKind.DEPENDS_ON, self.knowledge
            )

    def test_duplicate_rejected(self):
        r = OrganizationalRelationship(
            self.knowledge, RelationshipKind.OWNS, self.assimilation
        )
        with self.assertRaises(OrganizationalGraphError):
            OrganizationalGraph.create((r, r))

    def test_multiple_owners_rejected(self):
        engineering = ident(
            ConstitutionalObjectKind.DIRECTORATE, "government", "engineering"
        )
        with self.assertRaises(OrganizationalGraphError):
            OrganizationalGraph.create((
                OrganizationalRelationship(
                    self.knowledge, RelationshipKind.OWNS, self.assimilation
                ),
                OrganizationalRelationship(
                    engineering, RelationshipKind.OWNS, self.assimilation
                ),
            ))

    def test_hierarchical_cycle_rejected(self):
        with self.assertRaises(OrganizationalGraphError):
            OrganizationalGraph.create((
                OrganizationalRelationship(
                    self.executive, RelationshipKind.COMMANDS, self.knowledge
                ),
                OrganizationalRelationship(
                    self.knowledge, RelationshipKind.COMMANDS, self.executive
                ),
            ))

    def test_dependency_cycle_permitted(self):
        planning = ident(
            ConstitutionalObjectKind.DIRECTORATE, "government", "planning"
        )
        graph = OrganizationalGraph.create((
            OrganizationalRelationship(
                self.knowledge, RelationshipKind.DEPENDS_ON, planning
            ),
            OrganizationalRelationship(
                planning, RelationshipKind.DEPENDS_ON, self.knowledge
            ),
        ))
        self.assertEqual(len(graph.relationships), 2)

    def test_queries_and_fingerprint(self):
        graph = OrganizationalGraph.create((
            OrganizationalRelationship(
                self.government, RelationshipKind.OWNS, self.executive
            ),
            OrganizationalRelationship(
                self.executive, RelationshipKind.COMMANDS, self.knowledge
            ),
            OrganizationalRelationship(
                self.knowledge, RelationshipKind.OWNS, self.assimilation
            ),
        ))
        self.assertEqual(
            graph.outgoing(self.knowledge, kind=RelationshipKind.OWNS)[0].target,
            self.assimilation,
        )
        self.assertEqual(graph.fingerprint, graph.fingerprint)

if __name__ == "__main__":
    unittest.main()
