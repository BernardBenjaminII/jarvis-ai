from __future__ import annotations
import os
import subprocess
import tempfile
import time
from pathlib import Path

from .models import OCRPolicy
from .quality import quality_score

def _render_page(page, *, dpi: int, max_pixels: int, target: Path) -> None:
    scale = dpi / 72.0
    matrix = None
    import fitz
    rect = page.rect
    expected = int(rect.width * scale) * int(rect.height * scale)
    if expected > max_pixels and expected > 0:
        scale *= (max_pixels / expected) ** 0.5
    matrix = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    pix.save(str(target))

def ocr_pdf(path: Path, policy: OCRPolicy, *, tesseract_path: str) -> tuple[str, dict]:
    import fitz

    doc = fitz.open(path)
    try:
        total = int(doc.page_count)
        attempted = 0
        recovered = 0
        parts = []

        for index in range(min(total, policy.max_pages)):
            page = doc.load_page(index)
            native = ""
            try:
                native = (page.get_text("text") or "").strip()
            except Exception:
                native = ""

            if len(native) >= policy.minimum_chars:
                parts.append(native)
                recovered += 1
                continue

            attempted += 1
            with tempfile.TemporaryDirectory(prefix="jarvis_x_a2_1_") as td:
                image_path = Path(td) / f"page_{index+1:05d}.png"
                _render_page(
                    page,
                    dpi=policy.dpi,
                    max_pixels=policy.max_render_pixels,
                    target=image_path,
                )
                cmd = [
                    tesseract_path,
                    str(image_path),
                    "stdout",
                    "-l",
                    policy.languages,
                    "--psm",
                    "3",
                ]
                try:
                    run = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=policy.max_seconds_per_page,
                        check=False,
                    )
                except subprocess.TimeoutExpired:
                    continue

                text = (run.stdout or "").strip()
                if len(text) < policy.minimum_chars:
                    continue

                if quality_score(text) < policy.minimum_quality:
                    continue

                parts.append(text)
                recovered += 1

        text = "\n\n".join(parts)
        return text, {
            "pages_total": total,
            "pages_attempted": attempted,
            "pages_recovered": recovered,
            "quality_score": quality_score(text),
        }
    finally:
        doc.close()
