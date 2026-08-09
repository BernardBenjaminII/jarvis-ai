
import unittest
from dev.verification.route_contracts import RouteContract, collect_route_contracts, has_route, require_routes

class FakeRoute:
    def __init__(self, path=None, methods=(), name="", routes=()):
        self.path = path
        self.methods = set(methods)
        self.name = name
        self.routes = list(routes)
class FakeRouter:
    def __init__(self, routes): self.routes = list(routes)
class PrivateIncludedRouter:
    def __init__(self): self.include_context = object()

class CanonicalRouteVerificationTests(unittest.TestCase):
    def setUp(self):
        self.api_router = FakeRouter([
            FakeRoute('/ask', {'POST'}, 'ask'),
            FakeRoute('/api/conversation/query', {'POST'}, 'conversation_query'),
            FakeRoute('/health', {'GET'}, 'health'),
        ])
    def test_collects_public_router_contracts(self):
        contracts = collect_route_contracts(self.api_router)
        self.assertIn(RouteContract('POST', '/ask', 'ask'), contracts)
        self.assertTrue(has_route(contracts, 'POST', '/api/conversation/query'))
    def test_ignores_private_included_router_records(self):
        self.assertEqual(collect_route_contracts(PrivateIncludedRouter()), ())
    def test_supports_nested_public_routes(self):
        nested = FakeRouter([FakeRoute(routes=[FakeRoute('/nested', {'GET'}, 'nested')])])
        self.assertTrue(has_route(collect_route_contracts(nested), 'GET', '/nested'))
    def test_require_routes_returns_contracts(self):
        contracts = require_routes((self.api_router,), (('POST','/ask'),('POST','/api/conversation/query')))
        self.assertEqual(len(contracts), 3)
    def test_require_routes_reports_missing_contract(self):
        with self.assertRaisesRegex(AssertionError, 'DELETE /ask'):
            require_routes((self.api_router,), (('DELETE','/ask'),))
if __name__ == '__main__': unittest.main()
