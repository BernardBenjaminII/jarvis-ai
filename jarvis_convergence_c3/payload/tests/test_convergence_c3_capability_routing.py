from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from core.executive.director import ExecutiveDirector
from core.executive.routing import CapabilityRouter


class CapabilityRoutingTests(unittest.TestCase):
    def test_catalog_request_routes_to_knowledge(self):
        with TemporaryDirectory() as temp:
            director=ExecutiveDirector(database_path=Path(temp)/"missions.sqlite")
            routes=CapabilityRouter(director.registry).route("Search the knowledge catalog for Linux security")
            self.assertIn("knowledge", {item.director for item in routes})
            self.assertIn("system", {item.director for item in routes})

    def test_routing_hints_activate_profile_without_keyword(self):
        with TemporaryDirectory() as temp:
            director=ExecutiveDirector(database_path=Path(temp)/"missions.sqlite")
            routes=CapabilityRouter(director.registry).route("Handle this request", hints=("knowledge",))
            self.assertEqual(routes[0].profile, "knowledge")

    def test_unknown_request_falls_back_to_executive(self):
        with TemporaryDirectory() as temp:
            director=ExecutiveDirector(database_path=Path(temp)/"missions.sqlite")
            routes=CapabilityRouter(director.registry).route("What should I do next?")
            self.assertEqual(routes[0].director, "executive")
            self.assertEqual(routes[0].profile, "general")

    def test_mission_records_router_evidence(self):
        with TemporaryDirectory() as temp:
            director=ExecutiveDirector(database_path=Path(temp)/"missions.sqlite")
            mission=director.submit("Search the catalog", execute=False)
            delegated=[task for task in mission.tasks if task.action == "search"]
            self.assertEqual(len(delegated), 1)
            self.assertEqual(delegated[0].routing_evidence["router"], "convergence_c3")
            self.assertEqual(delegated[0].director, "knowledge")

    def test_compound_capability_request_creates_parallel_delegations(self):
        with TemporaryDirectory() as temp:
            director=ExecutiveDirector(database_path=Path(temp)/"missions.sqlite")
            mission=director.submit("Research Linux and create an implementation plan", execute=False)
            delegated=[task for task in mission.tasks if task.director != "executive"]
            self.assertGreaterEqual(len(delegated), 2)
            self.assertIn("knowledge", {task.director for task in delegated})
            self.assertIn("system", {task.director for task in delegated})
