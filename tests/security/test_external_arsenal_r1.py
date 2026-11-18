from pathlib import Path

from core.security import external_arsenal


def test_unmounted_directory_is_offline(tmp_path):
    status = external_arsenal.snapshot(tmp_path)
    assert status["state"] == "offline"
    assert status["execution_authorized"] is False


def test_offline_search_returns_no_results(tmp_path):
    result = external_arsenal.search(
        "admin", root=tmp_path
    )
    assert result["results"] == []
    assert result["state"] == "offline"


def test_search_only_returns_metadata(tmp_path, monkeypatch):
    for relative in external_arsenal.LIBRARIES.values():
        (tmp_path / relative).mkdir(parents=True)

    sample = (
        tmp_path
        / external_arsenal.LIBRARIES["seclists"]
        / "Discovery"
        / "admin-paths.txt"
    )
    sample.parent.mkdir(parents=True)
    sample.write_text("PRIVATE TEST CONTENT")

    monkeypatch.setattr(
        Path,
        "is_mount",
        lambda self: self == tmp_path,
    )

    result = external_arsenal.search(
        "admin", root=tmp_path
    )

    assert result["state"] == "ready"
    assert len(result["results"]) == 1
    assert result["results"][0]["name"] == "admin-paths.txt"
    assert "PRIVATE TEST CONTENT" not in str(result)


def test_search_rejects_empty_query(tmp_path):
    import pytest

    with pytest.raises(ValueError):
        external_arsenal.search("", root=tmp_path)
