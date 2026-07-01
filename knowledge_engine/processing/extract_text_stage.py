from pathlib import Path

from knowledge_engine.readers import read_pdf_pages


class ExtractTextStage:
    def __init__(self, page_store):
        self.page_store = page_store

    def run(self, paths: list[Path]) -> dict:
        extracted = 0
        errors = []

        for path in paths:
            if path.suffix.lower() != ".pdf":
                continue

            try:
                pages = read_pdf_pages(path)

                if not pages:
                    continue

                self.page_store.replace_pages(
                    document_path=str(path.resolve()),
                    pages=pages,
                )

                extracted += 1

            except Exception as exc:
                errors.append((str(path), str(exc)))

        return {
            "text_extracted": extracted,
            "text_errors": errors,
        }
