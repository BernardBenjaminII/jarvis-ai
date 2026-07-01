from pathlib import Path

from .base import BaseInspector


class ZimInspector(BaseInspector):

    extensions = (".zim",)

    def inspect(self, path: Path):

        return {

            "filename": path.name,

            "size_bytes": path.stat().st_size,

            "status": "inspection_not_implemented",
        }
