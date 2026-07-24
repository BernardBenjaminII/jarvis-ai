from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.engineering import (
    InventoryTargetKind,
    PythonImportResolver,
    inventory_target,
)


class RepositoryRealityModelingTests(unittest.TestCase):
    def _root(self, directory: str) -> Path:
        root = Path(directory)
        core = root / "core"
        core.mkdir()
        (core / "__init__.py").write_text("", encoding="utf-8")
        return root

    def test_resolves_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            package = root / "core" / "pkg"
            package.mkdir()
            (package / "__init__.py").write_text("", encoding="utf-8")
            result = PythonImportResolver(root).resolve("core.pkg")
            self.assertEqual(result.target.kind, InventoryTargetKind.PACKAGE)

    def test_resolves_and_inventories_module(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            (root / "core" / "item.py").write_text(
                'class Item:\n    pass\n\n__all__ = ["Item"]\n',
                encoding="utf-8",
            )
            result = PythonImportResolver(root).resolve("core.item")
            self.assertEqual(result.target.kind, InventoryTargetKind.MODULE)
            inventory = inventory_target(root, "core.item")
            self.assertEqual(
                tuple(item.symbol for item in inventory.exported_symbols),
                ("Item",),
            )

    def test_resolves_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            namespace = root / "core" / "namespace"
            namespace.mkdir()
            (namespace / "child.py").write_text("VALUE = 1\n", encoding="utf-8")
            result = PythonImportResolver(root).resolve("core.namespace")
            self.assertEqual(
                result.target.kind,
                InventoryTargetKind.NAMESPACE_PACKAGE,
            )

    def test_missing_target_is_inventory_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            result = inventory_target(root, "core.absent")
            self.assertEqual(result.target.kind, InventoryTargetKind.MISSING)
            self.assertEqual(result.exported_symbols, ())

    def test_resolves_alias(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            (root / "core" / "canonical.py").write_text(
                "class Value:\n    pass\n",
                encoding="utf-8",
            )
            result = PythonImportResolver(
                root,
                {"core.legacy": "core.canonical"},
            ).resolve("core.legacy")
            self.assertEqual(
                result.target.kind,
                InventoryTargetKind.COMPATIBILITY_ALIAS,
            )

    def test_resolution_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            (root / "core" / "stable.py").write_text("VALUE = 1\n", encoding="utf-8")
            resolver = PythonImportResolver(root)
            self.assertEqual(
                resolver.resolve("core.stable").fingerprint(),
                resolver.resolve("core.stable").fingerprint(),
            )


if __name__ == "__main__":
    unittest.main()
