from pathlib import Path

from knowledge.structure.pdf import PDFStructureExtractor


class StructureRegistry:
    def __init__(self):
        self._extractors = {}

        self.register(PDFStructureExtractor())

    def register(self, extractor):
        for ext in extractor.extensions:
            self._extractors[ext.lower()] = extractor

    def get(self, path: Path):
        return self._extractors.get(path.suffix.lower())
