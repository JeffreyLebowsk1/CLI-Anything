"""QRcoder CLI — QR code generation core logic.

Wraps the qrcode + Pillow libraries to provide agent-friendly generation
with full style customisation (colours, module shapes, logos).
"""

from __future__ import annotations

import io
import os
from typing import Any, Dict, Optional

# ── Validation constants ───────────────────────────────────────────────

ERROR_CORRECTION_LEVELS = {
    "L": "ERROR_CORRECT_L",  # ~7% recovery
    "M": "ERROR_CORRECT_M",  # ~15% recovery
    "Q": "ERROR_CORRECT_Q",  # ~25% recovery
    "H": "ERROR_CORRECT_H",  # ~30% recovery
}

MODULE_STYLES = ("square", "circle", "rounded", "gapped", "diamond")

EXPORT_FORMATS = ("png", "jpg", "jpeg", "svg")

# ── Public API ─────────────────────────────────────────────────────────


def validate_params(
    box_size: int = 10,
    border: int = 4,
    error_correction: str = "M",
    fg_color: str = "#000000",
    bg_color: str = "#FFFFFF",
    module_style: str = "square",
    module_corner_radius: int = 0,
    logo_size_percent: int = 30,
    logo_border: int = 5,
) -> None:
    """Raise ValueError if any parameter is out of range."""
    if box_size < 1 or box_size > 40:
        raise ValueError("box_size must be between 1 and 40")
    if border < 0 or border > 20:
        raise ValueError("border must be between 0 and 20")
    if error_correction.upper() not in ERROR_CORRECTION_LEVELS:
        valid = ", ".join(sorted(ERROR_CORRECTION_LEVELS.keys()))
        raise ValueError(
            f"error_correction must be one of {valid}, got '{error_correction}'"
        )
    if module_style not in MODULE_STYLES:
        valid = ", ".join(MODULE_STYLES)
        raise ValueError(f"module_style must be one of {valid}, got '{module_style}'")
    if module_corner_radius < 0:
        raise ValueError("module_corner_radius must be >= 0")
    if not (1 <= logo_size_percent <= 50):
        raise ValueError("logo_size_percent must be between 1 and 50")
    if logo_border < 0 or logo_border > 20:
        raise ValueError("logo_border must be between 0 and 20")
    _validate_color(fg_color, "fg_color")
    _validate_color(bg_color, "bg_color")


def generate_qr(
    data: str,
    box_size: int = 10,
    border: int = 4,
    error_correction: str = "M",
    fg_color: str = "#000000",
    bg_color: str = "#FFFFFF",
    module_style: str = "square",
    module_corner_radius: int = 0,
    logo_path: Optional[str] = None,
    logo_size_percent: int = 30,
    logo_border: int = 5,
) -> "PIL.Image.Image":  # noqa: F821
    """Generate a QR code PIL Image.

    Args:
        data: The text or URL to encode.
        box_size: Pixel size of each QR module (1-40).
        border: Number of module-widths of quiet zone (0-20).
        error_correction: Error correction level — L, M, Q, or H.
        fg_color: Foreground (module) colour as hex string.
        bg_color: Background colour as hex string.
        module_style: Shape of modules — square, circle, rounded, gapped,
                      or diamond.
        module_corner_radius: Corner radius for square/gapped styles (px).
        logo_path: Optional path to an image to embed in the centre.
        logo_size_percent: Logo size as percentage of QR size (1-50).
        logo_border: White border around the logo in pixels (0-20).

    Returns:
        A PIL Image object (RGB or RGBA).

    Raises:
        RuntimeError: If the qrcode or Pillow libraries are not installed.
        ValueError: If any parameter is invalid.
        FileNotFoundError: If logo_path is specified but does not exist.
    """
    _ensure_deps()
    import qrcode
    from PIL import Image, ImageDraw

    if not data:
        raise ValueError("data must not be empty")
    validate_params(
        box_size=box_size,
        border=border,
        error_correction=error_correction,
        fg_color=fg_color,
        bg_color=bg_color,
        module_style=module_style,
        module_corner_radius=module_corner_radius,
        logo_size_percent=logo_size_percent,
        logo_border=logo_border,
    )

    ec_attr = ERROR_CORRECTION_LEVELS[error_correction.upper()]
    qr = qrcode.QRCode(
        version=1,
        error_correction=getattr(qrcode.constants, ec_attr),
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    modules = qr.modules
    size = len(modules)
    img_size = size * box_size

    img = Image.new("RGB", (img_size, img_size), bg_color)
    draw = ImageDraw.Draw(img)

    for y, row in enumerate(modules):
        for x, is_dark in enumerate(row):
            if is_dark:
                x0, y0 = x * box_size, y * box_size
                x1, y1 = x0 + box_size, y0 + box_size
                _draw_module(
                    draw, x0, y0, x1, y1,
                    fg_color, module_style, module_corner_radius,
                )

    if logo_path is not None:
        img = _embed_logo(img, logo_path, logo_size_percent, logo_border)

    return img


def generate_svg(
    data: str,
    box_size: int = 10,
    border: int = 4,
    error_correction: str = "M",
) -> str:
    """Generate a QR code as an SVG string.

    Args:
        data: The text or URL to encode.
        box_size: Pixel size of each QR module.
        border: Quiet zone in modules.
        error_correction: Error correction level — L, M, Q, or H.

    Returns:
        SVG markup string.

    Raises:
        RuntimeError: If qrcode is not installed.
        ValueError: If any parameter is invalid.
    """
    _ensure_deps()
    import qrcode
    import qrcode.image.svg

    if not data:
        raise ValueError("data must not be empty")
    ec_attr = ERROR_CORRECTION_LEVELS[error_correction.upper()]
    factory = qrcode.image.svg.SvgImage
    qr = qrcode.QRCode(
        version=1,
        error_correction=getattr(qrcode.constants, ec_attr),
        box_size=box_size,
        border=border,
        image_factory=factory,
    )
    qr.add_data(data)
    qr.make(fit=True)
    svg_img = qr.make_image()
    buf = io.BytesIO()
    svg_img.save(buf)
    return buf.getvalue().decode("utf-8")


# ── Private helpers ────────────────────────────────────────────────────


def _ensure_deps() -> None:
    """Raise RuntimeError with install instructions if deps are missing."""
    missing = []
    try:
        import qrcode  # noqa: F401
    except ImportError:
        missing.append("qrcode[pil]")
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        missing.append("Pillow")
    if missing:
        packages = " ".join(missing)
        raise RuntimeError(
            f"Required packages not found: {packages}.\n"
            f"Install with: pip install {packages}"
        )


def _validate_color(color: str, name: str) -> None:
    """Raise ValueError if color is not a valid hex string."""
    c = color.lstrip("#")
    if len(c) not in (3, 6) or not all(ch in "0123456789abcdefABCDEF" for ch in c):
        raise ValueError(
            f"{name} must be a hex colour string like '#000000', got '{color}'"
        )


def _draw_module(
    draw: "ImageDraw.Draw",
    x0: int, y0: int, x1: int, y1: int,
    color: str,
    style: str,
    corner_radius: int,
) -> None:
    """Draw a single QR module in the given style."""
    if style == "square":
        if corner_radius > 0:
            draw.rounded_rectangle(
                [x0, y0, x1 - 1, y1 - 1], radius=corner_radius, fill=color
            )
        else:
            draw.rectangle([x0, y0, x1, y1], fill=color)
    elif style == "circle":
        draw.ellipse([x0, y0, x1, y1], fill=color)
    elif style == "rounded":
        radius = max(1, (x1 - x0) // 3)
        draw.rounded_rectangle([x0, y0, x1 - 1, y1 - 1], radius=radius, fill=color)
    elif style == "gapped":
        margin = (x1 - x0) // 4
        if corner_radius > 0:
            draw.rounded_rectangle(
                [x0 + margin, y0 + margin, x1 - margin - 1, y1 - margin - 1],
                radius=corner_radius, fill=color,
            )
        else:
            draw.rectangle(
                [x0 + margin, y0 + margin, x1 - margin, y1 - margin], fill=color
            )
    elif style == "diamond":
        import math
        w = x1 - x0
        h = y1 - y0
        points = [
            (x0 + w // 2, y0),
            (x1, y0 + h // 2),
            (x0 + w // 2, y1),
            (x0, y0 + h // 2),
        ]
        draw.polygon(points, fill=color)
    else:
        draw.rectangle([x0, y0, x1, y1], fill=color)


def _embed_logo(
    img: "PIL.Image.Image",
    logo_path: str,
    logo_size_percent: int,
    logo_border: int,
) -> "PIL.Image.Image":
    """Embed a logo image in the centre of a QR PIL Image."""
    from PIL import Image

    if not os.path.isfile(logo_path):
        raise FileNotFoundError(f"Logo file not found: {logo_path}")

    logo = Image.open(logo_path).convert("RGBA")
    qr_w, qr_h = img.size

    logo_max = int(min(qr_w, qr_h) * logo_size_percent / 100)
    logo.thumbnail((logo_max - 2 * logo_border, logo_max - 2 * logo_border))

    # Create a white background box
    box_w = logo.width + 2 * logo_border
    box_h = logo.height + 2 * logo_border
    box = Image.new("RGB", (box_w, box_h), "#FFFFFF")

    # Centre of QR
    paste_x = (qr_w - box_w) // 2
    paste_y = (qr_h - box_h) // 2

    result = img.convert("RGBA")
    result.paste(box, (paste_x, paste_y))
    result.paste(logo, (paste_x + logo_border, paste_y + logo_border), logo)
    return result.convert("RGB")
