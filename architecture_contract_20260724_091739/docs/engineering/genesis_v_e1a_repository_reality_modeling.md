# Genesis V-E1A — Repository Reality Modeling

## Mission

Replace the package-directory assumption with an explicit model of Python
repository reality.

## Target Kinds

- package
- module
- namespace package
- compatibility alias
- missing target

## Resolution

For `core.example.item`, static resolution checks:

1. `core/example/item/__init__.py`
2. `core/example/item.py`
3. `core/example/item/` as a namespace
4. configured compatibility aliases
5. a first-class missing target

No analyzed module is imported or executed.

## Engineering Principle

Reality precedes the model. Unexpected repository states become evidence rather
than unhandled exceptions.

## Compatibility Integration

V-E1 now inventories import targets rather than assuming every test import names
a package directory. Module imports such as
`core.cognition.common.cognitive_object` are therefore analyzed correctly.
