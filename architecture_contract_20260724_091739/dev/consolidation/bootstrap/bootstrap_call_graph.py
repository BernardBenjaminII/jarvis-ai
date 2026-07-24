from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[3]

BOOTSTRAP = ROOT / "core" / "bootstrap"

FILES = sorted(BOOTSTRAP.glob("*.py"))


class ImportVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports = set()
        self.calls = set()

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.add(node.func.id)

        elif isinstance(node.func, ast.Attribute):
            self.calls.add(node.func.attr)

        self.generic_visit(node)


print("\nBOOTSTRAP CALL GRAPH")
print("=" * 60)

for file in FILES:

    visitor = ImportVisitor()

    tree = ast.parse(file.read_text())

    visitor.visit(tree)

    print()

    print(file.name)

    print("-" * len(file.name))

    print("Imports")

    for item in sorted(visitor.imports):
        print("   ", item)

    print()

    print("Function Calls")

    for item in sorted(visitor.calls):
        print("   ", item)
