import importlib
import inspect
import pkgutil

from dev.doctor.check import HealthCheck

PACKAGE = "dev.doctor"

SKIP = {
    "__init__",
    "check",
    "doctor",
    "registry",
    "report",
}


def discover():
    checks = []

    package = importlib.import_module(PACKAGE)

    for module in pkgutil.iter_modules(package.__path__):

        if module.name in SKIP:
            continue

        mod = importlib.import_module(f"{PACKAGE}.{module.name}")

        for _, obj in inspect.getmembers(mod, inspect.isclass):

            if (
                issubclass(obj, HealthCheck)
                and obj is not HealthCheck
            ):
                checks.append(obj)

    return sorted(checks, key=lambda c: c.order)
