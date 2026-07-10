from __future__ import annotations

import re


class TextNormalizer:
    """
    Produces canonical text suitable for chunking,
    embeddings and retrieval.
    """

    @staticmethod
    def normalize(text: str) -> str:

        if not text:
            return ""

        #
        # Fix newlines
        #

        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        #
        # Collapse spaces
        #

        text = re.sub(r"[ \t]+", " ", text)

        #
        # Collapse blank lines
        #

        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()
