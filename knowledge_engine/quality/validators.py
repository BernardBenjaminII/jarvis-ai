from __future__ import annotations

import re


TUPLE_PATTERN = re.compile(

    r"^\('.*?',\s*\d+,\s*'.*?'\)$",

    re.MULTILINE,

)


class QualityValidator:

    @staticmethod
    def tuple_leak(text: str) -> bool:

        return bool(TUPLE_PATTERN.search(text))

    @staticmethod
    def empty(text: str) -> bool:

        return not text.strip()

    @staticmethod
    def duplicate(chunks: list[str]) -> bool:

        return len(chunks) != len(set(chunks))
