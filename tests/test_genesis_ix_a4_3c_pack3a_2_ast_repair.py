from __future__ import annotations

import ast
import functools
import unittest

from core.runtime.source_analysis import (
    callable_ast,
    callable_fallback,
    normalized_source,
    parse_source_text,
)


def decorator(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)
    return wrapper


class Fixture:
    def instance_method(self, value):
        return str(value)

    @classmethod
    def class_method(cls, value):
        return cls, value

    @staticmethod
    def static_method(value):
        return value

    @decorator
    def decorated_method(self, value):
        return value


class Tests(unittest.TestCase):
    def test_bound_instance_method(self):
        self.assertEqual(
            callable_ast(Fixture().instance_method).status,
            "parsed",
        )

    def test_class_method(self):
        self.assertEqual(
            callable_ast(Fixture.class_method).status,
            "parsed",
        )

    def test_static_method(self):
        self.assertEqual(
            callable_ast(Fixture.static_method).status,
            "parsed",
        )

    def test_decorated_method(self):
        result = normalized_source(Fixture().decorated_method)
        self.assertEqual(result.status, "available")
        self.assertIn("decorated_method", result.source or "")

    def test_nested_function(self):
        def outer():
            def inner(value):
                return value
            return inner

        self.assertEqual(callable_ast(outer()).status, "parsed")

    def test_indented_source(self):
        tree, error = parse_source_text(
            "    def execute(self):\n"
            "        return self.ground()\n"
        )
        self.assertIsNone(error)
        self.assertIsInstance(tree, ast.AST)

    def test_dedented_source(self):
        tree, error = parse_source_text(
            "def execute(self):\n"
            "    return self.ground()\n"
        )
        self.assertIsNone(error)
        self.assertIsInstance(tree, ast.AST)

    def test_malformed_source(self):
        tree, error = parse_source_text("def broken(:\n")
        self.assertIsNone(tree)
        self.assertIn("SyntaxError", error or "")

    def test_compiled_callable_fallback(self):
        result = callable_fallback(len)
        self.assertIn("signature", result)
        self.assertIn("module", result)


if __name__ == "__main__":
    unittest.main()
