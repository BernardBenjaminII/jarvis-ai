from __future__ import annotations
from pathlib import Path
import tempfile

def inspect_pdf(path: Path) -> dict:
    try:
        import fitz
    except Exception as exc:
        return {
            "openable": False,
            "pages": 0,
            "encrypted": False,
            "needs_password": False,
            "error": f"PyMuPDF unavailable: {exc}",
        }

    try:
        doc = fitz.open(path)
    except Exception as exc:
        return {
            "openable": False,
            "pages": 0,
            "encrypted": False,
            "needs_password": False,
            "error": f"{type(exc).__name__}: {exc}",
        }

    try:
        return {
            "openable": True,
            "pages": int(doc.page_count),
            "encrypted": bool(doc.is_encrypted),
            "needs_password": bool(doc.needs_pass),
            "error": None,
        }
    finally:
        doc.close()

def reconstruct_pdf(path: Path, destination: Path) -> tuple[bool, str]:
    try:
        import fitz
    except Exception as exc:
        return False, f"PyMuPDF unavailable: {exc}"

    try:
        doc = fitz.open(path)
    except Exception as exc:
        return False, f"Open failed: {type(exc).__name__}: {exc}"

    try:
        if doc.needs_pass:
            return False, "Encrypted PDF requires password."
        destination.parent.mkdir(parents=True, exist_ok=True)
        doc.save(
            destination,
            garbage=4,
            deflate=True,
            clean=True,
        )
        return True, "Reconstructed with PyMuPDF clean/garbage collection."
    except Exception as exc:
        return False, f"Reconstruction failed: {type(exc).__name__}: {exc}"
    finally:
        doc.close()
