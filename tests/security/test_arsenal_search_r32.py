"""Regression tests for indexed arsenal search R3.2."""

import sqlite3

import pytest

from core.security import arsenal_search_r32 as adapter


@pytest.fixture
def catalog(tmp_path):
    db = tmp_path / "arsenal.sqlite3"

    with sqlite3.connect(db) as connection:
        connection.execute("""
            CREATE TABLE resources (
                library TEXT NOT NULL,
                relative_path TEXT NOT NULL,
                filename TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                PRIMARY KEY (library, relative_path)
            )
        """)

        connection.executemany(
            """
            INSERT INTO resources
            VALUES (?, ?, ?, ?)
            """,
            [
                ("seclists", "Discovery/admin.txt",
                 "admin.txt", 100),
                ("seclists", "Discovery/admin-api.txt",
                 "admin-api.txt", 200),
                ("nuclei_templates", "http/ssrf.yaml",
                 "ssrf.yaml", 300),
            ],
        )

    return db


def test_indexed_search_returns_metadata(
    monkeypatch, tmp_path, catalog
):
    monkeypatch.setattr(
        adapter, "verify_storage", lambda root: True
    )

    result = adapter.indexed_search(
        "admin",
        root=tmp_path,
        database=catalog,
    )

    assert result["state"] == "ready"
    assert len(result["results"]) == 2
    assert result["truncated"] is False
    assert all(
        set(item) == {"library", "path", "name"}
        for item in result["results"]
    )


def test_indexed_search_truncation(
    monkeypatch, tmp_path, catalog
):
    monkeypatch.setattr(
        adapter, "verify_storage", lambda root: True
    )

    result = adapter.indexed_search(
        "admin",
        root=tmp_path,
        database=catalog,
        limit=1,
    )

    assert result["state"] == "ready"
    assert len(result["results"]) == 1
    assert result["truncated"] is True


def test_indexed_search_offline(
    monkeypatch, tmp_path, catalog
):
    monkeypatch.setattr(
        adapter, "verify_storage", lambda root: False
    )

    result = adapter.indexed_search(
        "admin",
        root=tmp_path,
        database=catalog,
    )

    assert result["state"] == "offline"
    assert result["results"] == []


def test_indexed_search_missing_catalog(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        adapter, "verify_storage", lambda root: True
    )

    result = adapter.indexed_search(
        "admin",
        root=tmp_path,
        database=tmp_path / "missing.sqlite3",
    )

    assert result["state"] == "index_unavailable"
    assert result["results"] == []


def test_indexed_search_corrupt_catalog(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        adapter, "verify_storage", lambda root: True
    )

    db = tmp_path / "corrupt.sqlite3"
    db.write_bytes(b"not a sqlite database")

    result = adapter.indexed_search(
        "admin",
        root=tmp_path,
        database=db,
    )

    assert result["state"] == "index_error"
    assert result["results"] == []


@pytest.mark.parametrize(
    "query", ["", "   ", "x" * 101]
)
def test_indexed_search_invalid_query(query):
    with pytest.raises(ValueError):
        adapter.indexed_search(query)
