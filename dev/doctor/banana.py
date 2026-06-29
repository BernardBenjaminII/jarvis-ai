from dev.doctor.check import HealthCheck, CheckResult


class BananaCheck(HealthCheck):
    name = "Banana"
    order = 999

    def run(self):
        return CheckResult(
            name=self.name,
            passed=True,
            score=100,
            details=["Auto-discovery works."]
        )
