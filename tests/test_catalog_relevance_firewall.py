from __future__ import annotations

import sqlite3

from core.conversation.catalog_status import (
    catalog_status_request,
    catalog_topic_request,
    inspect_catalog,
    inspect_catalog_topic,
    render_catalog_status,
    render_catalog_topic,
)
from core.retrieval.qualification import EvidenceCandidate, QualificationEngine


def test_shared_storage_path_cannot_create_topical_relevance():
    candidate = EvidenceCandidate(
        source_id="labor-1",
        source_path="/media/abdullah/JARVISDATA/Knowledge/economics/labor.txt",
        title="Labor Market Statistics",
        subject="economics",
        excerpt="Employment and wage statistics for the civilian labor force.",
        backend="runtime_fts",
        retrieval_score=0.95,
    )

    result = QualificationEngine().evaluate(
        "Can you see the Knowledge Catalog in JARVISDATA?",
        (candidate,),
    )

    assert result.accepted == ()
    assert len(result.rejected) == 1


def test_catalog_status_intent_is_narrow():
    assert catalog_status_request("Can you see the Knowledge Catalog in JARVISDATA?")
    assert catalog_status_request("What is the catalog health?")
    assert not catalog_status_request("What does the catalog say about labor markets?")
    assert not catalog_status_request("Explain network hardening")


def test_catalog_topic_inventory_intent():
    assert catalog_topic_request(
        "do you have any documents that cover the topic of agriculture in Knowledge Catalog?"
    ) == "agriculture"
    assert catalog_topic_request("Explain agriculture") is None


def test_catalog_status_uses_database_metadata_not_passages(tmp_path):
    database = tmp_path / "catalog.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE catalog_documents (id INTEGER PRIMARY KEY, title TEXT)")
        connection.executemany(
            "INSERT INTO catalog_documents(title) VALUES (?)",
            (("Alpha",), ("Beta",)),
        )

    result = inspect_catalog(database)
    answer = render_catalog_status(result)

    assert result["status"] == "available"
    assert result["counts"]["catalog_documents"] == 2
    assert "Yes. I can access" in answer
    assert "catalog_documents: 2" in answer


def test_missing_catalog_never_claims_visibility(tmp_path):
    result = inspect_catalog(tmp_path / "missing.sqlite")
    answer = render_catalog_status(result)

    assert result["status"] == "unavailable"
    assert answer.startswith("No.")


def test_topic_inventory_does_not_depend_on_content_chunks(tmp_path):
    database = tmp_path / "catalog.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE document_subjects (file_path TEXT, subject TEXT)")
        connection.execute(
            "INSERT INTO document_subjects VALUES (?, ?)",
            ("/Knowledge/agriculture/soil.pdf", "agriculture"),
        )
    result = inspect_catalog_topic(database, "agriculture")
    answer = render_catalog_topic(result)
    assert result["status"] == "found"
    assert "soil.pdf" in answer


def test_topic_inventory_absence_is_calibrated(tmp_path):
    database = tmp_path / "catalog.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE document_subjects (file_path TEXT, subject TEXT)")
    answer = render_catalog_topic(inspect_catalog_topic(database, "agriculture"))
    assert "no catalog metadata matching" in answer
    assert "does not prove" in answer
