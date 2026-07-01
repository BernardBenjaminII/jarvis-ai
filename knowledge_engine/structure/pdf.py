from pathlib import Path
import fitz

from knowledge_engine.structure.base import StructureNode


class PDFStructureExtractor:
    extensions = (".pdf",)

    def extract(self, path: Path) -> list[StructureNode]:
        doc = fitz.open(path)
        toc = doc.get_toc(simple=True)

        nodes: list[StructureNode] = []

        if not toc:
            return nodes

        stack: list[StructureNode] = []

        for index, item in enumerate(toc):
            level, title, page = item

            parent_title = None

            while stack and stack[-1].level >= level:
                stack.pop()

            if stack:
                parent_title = stack[-1].title

            node = StructureNode(
                document_path=str(path.resolve()),
                title=title.strip(),
                level=level,
                page=page,
                order_index=index,
                parent_title=parent_title,
                source="pdf_toc",
            )

            nodes.append(node)
            stack.append(node)

        return nodes
