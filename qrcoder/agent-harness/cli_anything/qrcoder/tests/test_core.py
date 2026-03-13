"""Unit tests for QRcoder CLI core modules.

Tests use synthetic data only — no real images or external dependencies
beyond qrcode + Pillow (which are lightweight and available in CI).
"""

import io
import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cli_anything.qrcoder.core.session import Session
from cli_anything.qrcoder.core.generate import (
    validate_params,
    generate_qr,
    generate_svg,
    MODULE_STYLES,
    ERROR_CORRECTION_LEVELS,
)
from cli_anything.qrcoder.core.export import save_image, save_svg, export_info


# ── Session tests ──────────────────────────────────────────────────────


class TestSession:
    def test_default_style(self):
        s = Session()
        style = s.get_style()
        assert style["box_size"] == 10
        assert style["border"] == 4
        assert style["error_correction"] == "M"
        assert style["fg_color"] == "#000000"
        assert style["bg_color"] == "#FFFFFF"
        assert style["module_style"] == "square"
        assert style["logo_path"] is None

    def test_set_style_valid(self):
        s = Session()
        s.set_style("fg_color", "#FF0000")
        assert s.get_style()["fg_color"] == "#FF0000"
        assert s.status()["modified"] is True

    def test_set_style_invalid_key(self):
        s = Session()
        with pytest.raises(ValueError, match="Unknown style key"):
            s.set_style("nonexistent_key", "value")

    def test_set_style_undo(self):
        s = Session()
        original = s.get_style()["fg_color"]
        s.set_style("fg_color", "#123456")
        s.undo()
        assert s.get_style()["fg_color"] == original

    def test_undo_empty(self):
        s = Session()
        with pytest.raises(RuntimeError, match="Nothing to undo"):
            s.undo()

    def test_redo_after_undo(self):
        s = Session()
        s.set_style("box_size", 20)
        s.undo()
        assert s.get_style()["box_size"] == 10
        s.redo()
        assert s.get_style()["box_size"] == 20

    def test_redo_empty(self):
        s = Session()
        with pytest.raises(RuntimeError, match="Nothing to redo"):
            s.redo()

    def test_reset_style(self):
        s = Session()
        s.set_style("fg_color", "#ABCDEF")
        s.set_style("box_size", 25)
        s.reset_style()
        assert s.get_style() == Session.DEFAULT_STYLE

    def test_snapshot_limit(self):
        s = Session()
        for i in range(Session.MAX_UNDO + 5):
            s.set_style("box_size", i + 1)
        assert len(s._undo_stack) == Session.MAX_UNDO

    def test_record_generation(self):
        s = Session()
        s.record_generation("data1", "/tmp/qr1.png", s.get_style())
        s.record_generation("data2", "/tmp/qr2.png", s.get_style())
        assert len(s.list_history()) == 2

    def test_list_history_order(self):
        s = Session()
        s.record_generation("first", "/tmp/a.png", s.get_style())
        s.record_generation("second", "/tmp/b.png", s.get_style())
        history = s.list_history()
        # Most recent first
        assert history[0]["data"] == "second"
        assert history[1]["data"] == "first"

    def test_status(self):
        s = Session()
        status = s.status()
        assert status["undo_count"] == 0
        assert status["redo_count"] == 0
        assert status["history_count"] == 0
        assert status["modified"] is False

        s.set_style("box_size", 15)
        status = s.status()
        assert status["undo_count"] == 1
        assert status["modified"] is True


# ── validate_params tests ──────────────────────────────────────────────


class TestValidateParams:
    def test_valid_defaults(self):
        # Should not raise
        validate_params()

    def test_box_size_limits(self):
        validate_params(box_size=1)
        validate_params(box_size=40)
        with pytest.raises(ValueError, match="box_size"):
            validate_params(box_size=0)
        with pytest.raises(ValueError, match="box_size"):
            validate_params(box_size=41)

    def test_border_limits(self):
        validate_params(border=0)
        validate_params(border=20)
        with pytest.raises(ValueError, match="border"):
            validate_params(border=-1)
        with pytest.raises(ValueError, match="border"):
            validate_params(border=21)

    def test_error_correction_valid(self):
        for level in ["L", "M", "Q", "H", "l", "m", "q", "h"]:
            validate_params(error_correction=level)

    def test_error_correction_invalid(self):
        with pytest.raises(ValueError, match="error_correction"):
            validate_params(error_correction="X")

    def test_module_style_valid(self):
        for style in MODULE_STYLES:
            validate_params(module_style=style)

    def test_module_style_invalid(self):
        with pytest.raises(ValueError, match="module_style"):
            validate_params(module_style="triangle")

    def test_color_valid(self):
        validate_params(fg_color="#000", bg_color="#fff")
        validate_params(fg_color="#1A2B3C", bg_color="#FFFFFF")

    def test_color_invalid(self):
        with pytest.raises(ValueError, match="fg_color"):
            validate_params(fg_color="red")
        with pytest.raises(ValueError, match="bg_color"):
            validate_params(bg_color="not-a-color")

    def test_logo_size_limits(self):
        validate_params(logo_size_percent=1)
        validate_params(logo_size_percent=50)
        with pytest.raises(ValueError, match="logo_size_percent"):
            validate_params(logo_size_percent=0)
        with pytest.raises(ValueError, match="logo_size_percent"):
            validate_params(logo_size_percent=51)


# ── generate_qr tests (require qrcode + Pillow) ────────────────────────


class TestGenerateQR:
    def test_generate_returns_image(self):
        pytest.importorskip("qrcode")
        pytest.importorskip("PIL")
        from PIL import Image
        img = generate_qr("https://example.com")
        assert isinstance(img, Image.Image)

    def test_image_dimensions(self):
        pytest.importorskip("qrcode")
        pytest.importorskip("PIL")
        img_small = generate_qr("hi", box_size=5)
        img_large = generate_qr("hi", box_size=15)
        assert img_large.width > img_small.width

    def test_default_params(self):
        pytest.importorskip("qrcode")
        pytest.importorskip("PIL")
        img = generate_qr("hello world")
        assert img.width > 0
        assert img.height > 0
        assert img.width == img.height

    def test_all_module_styles(self):
        pytest.importorskip("qrcode")
        pytest.importorskip("PIL")
        for style in MODULE_STYLES:
            img = generate_qr("test", module_style=style)
            assert img.width > 0, f"style '{style}' produced empty image"

    def test_empty_data_raises(self):
        pytest.importorskip("qrcode")
        pytest.importorskip("PIL")
        with pytest.raises(ValueError):
            generate_qr("")

    def test_logo_missing_raises(self):
        pytest.importorskip("qrcode")
        pytest.importorskip("PIL")
        with pytest.raises(FileNotFoundError):
            generate_qr("data", logo_path="/nonexistent/logo.png")


# ── generate_svg tests (require qrcode) ───────────────────────────────


class TestGenerateSVG:
    def test_svg_returns_string(self):
        pytest.importorskip("qrcode")
        result = generate_svg("https://example.com")
        assert isinstance(result, str)

    def test_svg_starts_with_xml(self):
        pytest.importorskip("qrcode")
        result = generate_svg("https://example.com")
        assert "<svg" in result.lower() or "<?xml" in result.lower()

    def test_svg_empty_data_raises(self):
        pytest.importorskip("qrcode")
        with pytest.raises(ValueError):
            generate_svg("")


# ── export tests ───────────────────────────────────────────────────────


class TestExport:
    def _make_image(self):
        pytest.importorskip("PIL")
        from PIL import Image
        return Image.new("RGB", (100, 100), "#FFFFFF")

    def test_save_png(self):
        img = self._make_image()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "test.png")
            saved = save_image(img, path, fmt="png")
            assert os.path.isfile(saved)
            with open(saved, "rb") as f:
                assert f.read(4) == b"\x89PNG"

    def test_save_jpg(self):
        img = self._make_image()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "test.jpg")
            saved = save_image(img, path, fmt="jpg")
            assert os.path.isfile(saved)
            with open(saved, "rb") as f:
                assert f.read(2) == b"\xff\xd8"

    def test_save_unsupported_format(self):
        img = self._make_image()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "test.bmp")
            with pytest.raises(ValueError, match="Unsupported"):
                save_image(img, path, fmt="bmp")

    def test_save_svg(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "test.svg")
            content = "<svg><rect/></svg>"
            saved = save_svg(content, path)
            assert os.path.isfile(saved)
            with open(saved) as f:
                assert f.read() == content

    def test_export_info_png(self):
        img = self._make_image()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "info_test.png")
            saved = save_image(img, path, fmt="png")
            info = export_info(saved)
            assert info["format"] == "png"
            assert info["size_bytes"] > 0
            assert info["width"] == 100
            assert info["height"] == 100

    def test_export_info_missing(self):
        with pytest.raises(FileNotFoundError):
            export_info("/nonexistent/file.png")
