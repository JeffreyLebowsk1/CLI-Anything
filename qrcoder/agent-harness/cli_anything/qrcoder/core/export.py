"""QRcoder CLI — export helpers.

Handles writing QR code output to disk in PNG, JPEG, and SVG formats.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

SUPPORTED_FORMATS = ("png", "jpg", "jpeg", "svg")


def save_image(
    img: "PIL.Image.Image",  # noqa: F821
    output_path: str,
    fmt: str = "png",
) -> str:
    """Save a PIL Image to disk.

    Args:
        img: PIL Image object to save.
        output_path: Destination file path.  The extension is added
                     automatically if the path has no recognised extension.
        fmt: Output format — "png", "jpg"/"jpeg".

    Returns:
        The resolved absolute path written to.

    Raises:
        ValueError: If the format is not supported.
    """
    fmt = fmt.lower().lstrip(".")
    if fmt not in ("png", "jpg", "jpeg"):
        raise ValueError(
            f"Unsupported raster format '{fmt}'. Use png or jpg. "
            "For SVG use save_svg()."
        )

    # Ensure the file has the right extension
    root, ext = os.path.splitext(output_path)
    canonical_ext = ".jpg" if fmt in ("jpg", "jpeg") else ".png"
    if ext.lower() not in (".png", ".jpg", ".jpeg"):
        output_path = root + canonical_ext

    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    pil_fmt = "JPEG" if fmt in ("jpg", "jpeg") else "PNG"
    if pil_fmt == "JPEG":
        img = img.convert("RGB")
    img.save(output_path, format=pil_fmt)
    return output_path


def save_svg(svg_content: str, output_path: str) -> str:
    """Save SVG markup to disk.

    Args:
        svg_content: SVG string to write.
        output_path: Destination file path.

    Returns:
        The resolved absolute path written to.
    """
    root, ext = os.path.splitext(output_path)
    if ext.lower() != ".svg":
        output_path = root + ".svg"

    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(svg_content)
    return output_path


def export_info(path: str) -> Dict[str, Any]:
    """Return metadata about a saved QR file.

    Args:
        path: Path to the QR image file.

    Returns:
        Dict with path, format, size_bytes, and (for rasters) dimensions.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Output file not found: {path}")

    info: Dict[str, Any] = {
        "path": os.path.abspath(path),
        "format": os.path.splitext(path)[1].lstrip(".").lower(),
        "size_bytes": os.path.getsize(path),
    }

    ext = info["format"]
    if ext in ("png", "jpg", "jpeg"):
        try:
            from PIL import Image
            with Image.open(path) as img:
                info["width"], info["height"] = img.size
        except Exception:
            pass

    return info
