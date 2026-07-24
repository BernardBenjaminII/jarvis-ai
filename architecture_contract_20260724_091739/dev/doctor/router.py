from dev.doctor.check import HealthCheck

from knowledge_engine.director.router.intent_router import IntentRouter


class IntentRouterCheck(HealthCheck):
    name = "Intent Router"
    category = "Knowledge"
    order = 60

    description = "Verifies rule-based routing into Director intents."
    documentation = "docs/architecture/architecture_blueprint.md"

    CASES = [
        ("find JARVIS integration sample", "search"),
        ("search SQLite notes", "search"),
        ("what do I know about embeddings", "search"),
        ("", "unknown"),
    ]

    def run(self):
        router = IntentRouter()
        failures = 0

        for text, expected in self.CASES:
            routed = router.route(text)

            if routed.intent == expected:
                self.detail(
                    f"✓ {text!r} -> {routed.intent} "
                    f"({routed.reason}, {routed.confidence:.2f})"
                )
            else:
                failures += 1
                self.fail(
                    f"{text!r}: expected {expected}, got {routed.intent}"
                )

        total = len(self.CASES)
        passed = total - failures
        self.score(round((passed / total) * 100))

        return self.result()
