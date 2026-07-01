from pathlib import Path
import fitz


def read_pdf_pages(path: Path) -> list[dict]:
    doc = fitz.open(path)
    pages = []

    for index, page in enumerate(doc, start=1):
        text = page.get_text().strip()

        if text:
            pages.append(
                {
                    "page_number": index,
                    "text": text,
                }
            )

    return pages
