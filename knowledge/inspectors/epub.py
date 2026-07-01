from ebooklib import epub

from .base import BaseInspector


class EpubInspector(BaseInspector):

    extensions = (".epub",)

    def inspect(self, path):

        book = epub.read_epub(str(path))

        return {

            "title":
                book.get_metadata(
                    "DC",
                    "title"
                ),

            "language":
                book.get_metadata(
                    "DC",
                    "language"
                ),
        }
