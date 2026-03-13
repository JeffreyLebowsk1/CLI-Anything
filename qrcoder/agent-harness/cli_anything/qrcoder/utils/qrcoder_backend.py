"""QRcoder CLI — backend wrapper.

Checks for required dependencies and provides high-level helper functions
used by the CLI commands.  Separates import-time checks from generation
logic so tests that mock the qrcode library work correctly.
"""

from __future__ import annotations

import shutil
from typing import Optional


def check_qrcode_available() -> bool:
    """Return True if the qrcode library is importable."""
    try:
        import qrcode  # noqa: F401
        return True
    except ImportError:
        return False


def check_pillow_available() -> bool:
    """Return True if Pillow is importable."""
    try:
        from PIL import Image  # noqa: F401
        return True
    except ImportError:
        return False


def ensure_available() -> None:
    """Raise RuntimeError with install instructions if deps are missing."""
    missing = []
    if not check_qrcode_available():
        missing.append("qrcode[pil]")
    if not check_pillow_available():
        missing.append("Pillow")
    if missing:
        packages = " ".join(missing)
        raise RuntimeError(
            f"Required packages not found: {packages}.\n"
            f"Install with: pip install {packages}"
        )


def get_dependency_status() -> dict:
    """Return a dict describing the availability of all runtime deps."""
    return {
        "qrcode": check_qrcode_available(),
        "Pillow": check_pillow_available(),
        "all_ok": check_qrcode_available() and check_pillow_available(),
    }
