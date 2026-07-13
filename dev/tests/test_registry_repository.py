"""
KnowledgeRegistryRepository contract and integration verification.

All database operations use a temporary SQLite catalog.
"""

from __future__ import annotations

import inspect
import sqlite3
import tempfile
from dataclasses import FrozenInstanceError
from inspect import Parameter
from pathlib import Path

from knowledge_engine.assimilation.repositories import (
    KnowledgeRegistryRepository,
)
from knowledge_engine.assimilation.repositories.knowledge_registry import (
    KnowledgeRegistryObject,
)
from knowledge_engine.storage.database import (
    KnowledgeDatabase,
)


EMPTY = inspect.Signature.empty


def assert_frozen(
    instance: object,
    attribute_name: str,
    replacement: object,
) -> None:
    try:
        setattr(instance, attribute_name, replacement)
    except FrozenInstanceError:
        return

    raise AssertionError(
        f"{type(instance).__name__} must remain immutable"
    )


def create_database(path: Path) -> None:
    connection = sqlite3.connect(path)

    connection.execute(
        """
        CREATE TABLE knowledge_registry (
            object_uuid TEXT PRIMARY KEY,
            object_path TEXT NOT NULL,
            object_type TEXT NOT NULL,
            lifecycle_state TEXT NOT NULL,
            assimilation_state TEXT NOT NULL,
            updated_at TEXT
        )
        """
    )

    connection.executemany(
        """
        INSERT INTO knowledge_registry (
            object_uuid,
            object_path,
            object_type,
            lifecycle_state,
            assimilation_state,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "collection-001",
                "/tmp/source-collection",
                "source_collection",
                "validated",
                "queued",
                "2026-07-13 12:00:00",
            ),
            (
                "document-001",
                "/tmp/document.txt",
                "single_document",
                "validated",
                "queued",
                None,
            ),
        ],
    )

    connection.commit()
    connection.close()


def verify_constructor_contract() -> None:
    signature = inspect.signature(
        KnowledgeRegistryRepository.__init__,
    )

    parameters = list(signature.parameters.values())

    assert [
        parameter.name
        for parameter in parameters
    ] == [
        "self",
        "db",
    ]

    assert parameters[0].kind == Parameter.POSITIONAL_OR_KEYWORD
    assert parameters[1].kind == Parameter.POSITIONAL_OR_KEYWORD

    try:
        KnowledgeRegistryRepository(None)
    except ValueError as exc:
        assert "db" in str(exc)
    else:
        raise AssertionError("Repository accepted db=None")

    try:
        KnowledgeRegistryRepository(object())
    except TypeError as exc:
        assert "connect" in str(exc)
    else:
        raise AssertionError(
            "Repository accepted an object without connect()"
        )

    print("[PASS] Repository constructor contract")


def verify_public_signatures() -> None:
    database = KnowledgeDatabase(":memory:")
    repository = KnowledgeRegistryRepository(database)

    get_object = inspect.signature(repository.get_object)
    get_source_collection = inspect.signature(
        repository.get_source_collection
    )

    object_parameters = list(
        get_object.parameters.values()
    )

    assert [
        parameter.name
        for parameter in object_parameters
    ] == [
        "object_uuid",
        "object_type",
    ]

    assert all(
        parameter.kind == Parameter.KEYWORD_ONLY
        for parameter in object_parameters
    )

    assert object_parameters[0].default is EMPTY
    assert object_parameters[1].default is None

    collection_parameters = list(
        get_source_collection.parameters.values()
    )

    assert [
        parameter.name
        for parameter in collection_parameters
    ] == [
        "object_uuid",
    ]

    assert (
        collection_parameters[0].kind
        == Parameter.KEYWORD_ONLY
    )
    assert collection_parameters[0].default is EMPTY

    print("[PASS] Repository exact public signatures")


def verify_repository_behavior() -> None:
    with tempfile.TemporaryDirectory(
        prefix="jarvis-registry-repository-"
    ) as temporary:
        root = Path(temporary)
        database_path = root / "catalog.sqlite"

        create_database(database_path)

        database = KnowledgeDatabase(database_path)
        repository = KnowledgeRegistryRepository(database)

        collection = repository.get_source_collection(
            object_uuid="collection-001",
        )

        assert isinstance(
            collection,
            KnowledgeRegistryObject,
        )

        assert collection.object_uuid == "collection-001"
        assert collection.object_path == "/tmp/source-collection"
        assert collection.object_type == "source_collection"
        assert collection.lifecycle_state == "validated"
        assert collection.assimilation_state == "queued"
        assert collection.updated_at == "2026-07-13 12:00:00"

        as_dict = collection.to_dict()

        assert as_dict == {
            "object_uuid": "collection-001",
            "object_path": "/tmp/source-collection",
            "object_type": "source_collection",
            "lifecycle_state": "validated",
            "assimilation_state": "queued",
            "updated_at": "2026-07-13 12:00:00",
        }

        assert_frozen(
            collection,
            "object_uuid",
            "changed",
        )

        document = repository.get_object(
            object_uuid="document-001",
        )

        assert document is not None
        assert document.object_type == "single_document"
        assert document.updated_at is None

        mismatched = repository.get_object(
            object_uuid="document-001",
            object_type="source_collection",
        )

        assert mismatched is None

        missing = repository.get_source_collection(
            object_uuid="missing-object",
        )

        assert missing is None

        for invalid_uuid in (
            "",
            "   ",
        ):
            try:
                repository.get_object(
                    object_uuid=invalid_uuid,
                )
            except ValueError as exc:
                assert "object_uuid" in str(exc)
            else:
                raise AssertionError(
                    "Blank object_uuid was accepted"
                )

        try:
            repository.get_object(
                object_uuid="document-001",
                object_type="   ",
            )
        except ValueError as exc:
            assert "object_type" in str(exc)
        else:
            raise AssertionError(
                "Blank object_type was accepted"
            )

    print("[PASS] Repository source-collection lookup")
    print("[PASS] Repository generic object lookup")
    print("[PASS] Repository object-type filtering")
    print("[PASS] Repository missing-object behavior")
    print("[PASS] Repository input validation")
    print("[PASS] Registry object immutable mapping")


def main() -> None:
    verify_constructor_contract()
    verify_public_signatures()
    verify_repository_behavior()

    print("----------------------------------------------------------------------")
    print("[PASS] Knowledge Registry Repository verified")


if __name__ == "__main__":
    main()
