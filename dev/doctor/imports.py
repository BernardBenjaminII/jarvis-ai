import importlib

from .check import HealthCheck


MODULES = [
    "fastapi",
    "uvicorn",
    "requests",
    "openai",
    "psutil",
]


class ImportCheck(HealthCheck):

    name = "Python Dependencies"

    category = "Dependencies"

    order = 30

    description = "Verifies required Python modules."

    fix_hint = "Install missing packages into the active virtual environment."

    documentation = "docs/development/python_environment.md"

    def run(self):

        missing = []

        for module in MODULES:

            try:
                importlib.import_module(module)
            except ImportError:
                missing.append(module)

        if missing:

            for module in missing:
                self.fail(f"Missing module: {module}")

            self.score(0)

        else:

            self.ok("All required modules installed.")
            self.score(100)

        return self.result()
