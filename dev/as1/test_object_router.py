from pathlib import Path

from dev.as1.object_router import (
    ObjectRole,
    route_object,
)


def check(
    path: str,
    role: ObjectRole,
    handler: str,
    text: bool,
):
    decision = route_object(Path(path))

    assert decision.role == role, (
        path,
        decision,
    )

    assert decision.handler == handler, (
        path,
        decision,
    )

    assert (
        decision.admissible_to_text_pipeline
        is text
    ), (
        path,
        decision,
    )


def main():
    root = (
        "/media/abdullah/JARVISDATA/Knowledge"
    )

    check(
        root + "/military/doctrine/FM.pdf",
        ObjectRole.DOCUMENT,
        "document_text",
        True,
    )

    check(
        root + "/books/manual.epub",
        ObjectRole.DOCUMENT,
        "document_text",
        True,
    )

    check(
        root + "/programming/example.py",
        ObjectRole.SOURCE_CODE,
        "source_code",
        False,
    )

    check(
        root + "/offline/wikipedia.zim",
        ObjectRole.WEB_ARCHIVE,
        "web_archive_provider",
        False,
    )

    check(
        root + "/geography/maps/map.tif",
        ObjectRole.DATASET,
        "geospatial_dataset",
        False,
    )

    check(
        root
        + "/geography/geodata/elevation/usa/"
        + "Copernicus_DSM_COG_30_N25_00_W077_00_DEM/"
        + "Copernicus_DSM_30_N25_00_W077_00.xml",
        ObjectRole.METADATA,
        "dataset_metadata",
        False,
    )

    check(
        root + "/datasets/data.csv",
        ObjectRole.DATASET,
        "structured_dataset",
        False,
    )

    check(
        root + "/misc/config.json",
        ObjectRole.UNKNOWN,
        "review_structured",
        False,
    )

    check(
        root + "/website/article.html",
        ObjectRole.DOCUMENT,
        "html_document",
        True,
    )

    print("GENESIS AS1 PACK 1A ROUTER TESTS: PASS")


if __name__ == "__main__":
    main()
