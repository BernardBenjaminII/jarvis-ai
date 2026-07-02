import fitz

from knowledge_engine.extraction.extractors.base import BaseExtractor


class PDFExtractor(BaseExtractor):

    def supports(self, path):
        return path.suffix.lower() == ".pdf"

    def extract(self, path):

        document = fitz.open(path)

        pages = []

        for number, page in enumerate(document):

            text = page.get_text("text").strip()

            pages.append(
                (
                    str(path),
                    number + 1,
                    text,
                )
            )

        return pages
