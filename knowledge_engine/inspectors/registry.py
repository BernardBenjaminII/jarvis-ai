from pathlib import Path

from .pdf import PDFInspector
from .text import TextInspector
from .markdown import MarkdownInspector
from .docx import DocxInspector
from .html import HtmlInspector
from .epub import EpubInspector
from .image import ImageInspector
from .zim import ZimInspector


class InspectorRegistry:

    def __init__(self):

        self._inspectors = {}

        self.register(PDFInspector())
        self.register(TextInspector())
        self.register(MarkdownInspector())
        self.register(DocxInspector())
        self.register(HtmlInspector())
        self.register(EpubInspector())
        self.register(ImageInspector())
        self.register(ZimInspector())

    def register(self, inspector):

        for ext in inspector.extensions:
            self._inspectors[ext.lower()] = inspector

    def get(self, path: Path):

        return self._inspectors.get(path.suffix.lower())
