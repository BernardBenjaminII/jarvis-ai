from pathlib import Path

from bs4 import BeautifulSoup

from .base import BaseInspector


class HtmlInspector(BaseInspector):

    extensions = (
        ".html",
        ".htm",
    )

    def inspect(self, path: Path):

        soup = BeautifulSoup(
            path.read_text(errors="ignore"),
            "html.parser",
        )

        text = soup.get_text()

        return {

            "title":
                soup.title.string
                if soup.title
                else None,

            "words":
                len(text.split()),

            "characters":
                len(text),
        }
