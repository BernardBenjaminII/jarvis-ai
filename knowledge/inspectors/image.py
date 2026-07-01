from pathlib import Path

from PIL import Image

from .base import BaseInspector


class ImageInspector(BaseInspector):

    extensions = (
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
    )

    def inspect(self, path: Path):

        image = Image.open(path)

        return {

            "width": image.width,

            "height": image.height,

            "mode": image.mode,

            "format": image.format,
        }
