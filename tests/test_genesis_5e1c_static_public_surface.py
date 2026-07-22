from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

from core.engineering import inventory_package, inventory_target
from core.engineering.public_surface import evaluate_public_surface


class StaticPublicSurfaceTests(unittest.TestCase):
    def _evaluate(self, source: str) -> tuple[str, ...]:
        result = evaluate_public_surface(
            ast.parse(source),
            module_name="core.fixture",
            is_package=True,
        )
        self.assertTrue(result.resolved, result.findings)
        return result.symbols

    def test_literal_list(self) -> None:
        self.assertEqual(
            self._evaluate('__all__ = ["A", "B"]\n'),
            ("A", "B"),
        )

    def test_tuple_and_concatenation(self) -> None:
        self.assertEqual(
            self._evaluate(
                'base = ("A",)\n'
                '__all__ = base + ("B", "C")\n'
            ),
            ("A", "B", "C"),
        )

    def test_managed_export_pattern(self) -> None:
        source = """
__all__ = ["Existing"]

try:
    _existing_all = tuple(__all__)
except NameError:
    _existing_all = ()

__all__ = tuple(
    dict.fromkeys(
        (*_existing_all, "Assumption", "WorkspaceStatus", "Assumption")
    )
)
del _existing_all
"""
        self.assertEqual(
            self._evaluate(source),
            ("Existing", "Assumption", "WorkspaceStatus"),
        )

    def test_inventory_recognizes_managed_package_exports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "core" / "fixture"
            package.mkdir(parents=True)
            (root / "core" / "__init__.py").write_text("", encoding="utf-8")
            (package / "__init__.py").write_text(
                """
from .models import Existing
__all__ = ["Existing"]
_existing_all = tuple(__all__)
from .models import Added
__all__ = tuple(dict.fromkeys((*_existing_all, "Added")))
del _existing_all
""",
                encoding="utf-8",
            )
            (package / "models.py").write_text(
                "class Existing: pass\nclass Added: pass\n",
                encoding="utf-8",
            )

            inventory = inventory_package(root, "core.fixture")
            exported = tuple(item.symbol for item in inventory.exported_symbols)
            self.assertEqual(exported, ("Added", "Existing"))

    def test_compatibility_module_imports_upstream_all(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "core" / "fixture"
            package.mkdir(parents=True)
            (root / "core" / "__init__.py").write_text("", encoding="utf-8")
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "object_model.py").write_text(
                """
class CognitiveObject:
    pass

__all__ = ["CognitiveObject"]
""",
                encoding="utf-8",
            )
            (package / "compatibility.py").write_text(
                """
from .object_model import *
from .object_model import __all__ as __all__
""",
                encoding="utf-8",
            )

            inventory = inventory_target(
                root,
                "core.fixture.compatibility",
            )
            exported = tuple(item.symbol for item in inventory.exported_symbols)
            self.assertEqual(exported, ("CognitiveObject",))


if __name__ == "__main__":
    unittest.main()
