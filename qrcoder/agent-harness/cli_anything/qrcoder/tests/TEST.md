# Test Plan: cli-anything-qrcoder

## Scope

Unit tests for core modules (session, generate, export).  All tests use
synthetic data and do **not** require a display.  Tests are run with
`pytest -v` from within `qrcoder/agent-harness/`.

## Test Suites

### TestSession (test_core.py)

| Test | What it checks |
|------|---------------|
| `test_default_style` | Session initialises with correct defaults |
| `test_set_style_valid` | `set_style` updates value and marks modified |
| `test_set_style_invalid_key` | Raises ValueError for unknown keys |
| `test_set_style_undo` | `undo()` restores previous style |
| `test_undo_empty` | `undo()` on empty stack raises RuntimeError |
| `test_redo_after_undo` | `redo()` re-applies the undone change |
| `test_redo_empty` | `redo()` on empty stack raises RuntimeError |
| `test_reset_style` | `reset_style()` restores all defaults |
| `test_snapshot_limit` | Stack is capped at MAX_UNDO entries |
| `test_record_generation` | History grows with each `record_generation` call |
| `test_list_history_order` | `list_history()` returns most-recent first |
| `test_status` | `status()` returns correct counts |

### TestValidateParams (test_core.py)

| Test | What it checks |
|------|---------------|
| `test_valid_defaults` | Default params pass validation |
| `test_box_size_limits` | box_size 1-40 valid; 0 and 41 raise ValueError |
| `test_border_limits` | border 0-20 valid; -1 and 21 raise ValueError |
| `test_error_correction_valid` | L/M/Q/H all accepted (case-insensitive) |
| `test_error_correction_invalid` | Unknown level raises ValueError |
| `test_module_style_valid` | All five styles accepted |
| `test_module_style_invalid` | Unknown style raises ValueError |
| `test_color_valid` | 3- and 6-char hex strings accepted |
| `test_color_invalid` | Non-hex string raises ValueError |
| `test_logo_size_limits` | 1-50 valid; 0 and 51 raise ValueError |

### TestGenerateQR (test_core.py — requires qrcode + Pillow)

| Test | What it checks |
|------|---------------|
| `test_generate_returns_image` | Returns a PIL Image |
| `test_image_dimensions` | Image is larger for bigger box_size |
| `test_default_params` | Generates successfully with all defaults |
| `test_all_module_styles` | Each style runs without error |
| `test_empty_data_raises` | Empty data raises ValueError |
| `test_logo_missing_raises` | Non-existent logo raises FileNotFoundError |
| `test_logo_embed` | Logo path → logo appears in centre region |

### TestGenerateSVG (test_core.py — requires qrcode)

| Test | What it checks |
|------|---------------|
| `test_svg_returns_string` | Returns a string |
| `test_svg_starts_with_xml` | Output is valid SVG markup |
| `test_svg_empty_data_raises` | Empty data raises ValueError |

### TestExport (test_core.py)

| Test | What it checks |
|------|---------------|
| `test_save_png` | PNG file written; magic bytes `\x89PNG` |
| `test_save_jpg` | JPEG file written; magic bytes `\xff\xd8` |
| `test_save_unsupported_format` | Raises ValueError for `bmp` |
| `test_save_svg` | SVG file written with correct content |
| `test_export_info_png` | Returns dict with path/format/size/width/height |
| `test_export_info_missing` | Raises FileNotFoundError |

## Test Results

<!--  Updated by: pytest -v --tb=short  -->

```
PASSED  tests/test_core.py::TestSession::test_default_style
PASSED  tests/test_core.py::TestSession::test_set_style_valid
PASSED  tests/test_core.py::TestSession::test_set_style_invalid_key
PASSED  tests/test_core.py::TestSession::test_set_style_undo
PASSED  tests/test_core.py::TestSession::test_undo_empty
PASSED  tests/test_core.py::TestSession::test_redo_after_undo
PASSED  tests/test_core.py::TestSession::test_redo_empty
PASSED  tests/test_core.py::TestSession::test_reset_style
PASSED  tests/test_core.py::TestSession::test_snapshot_limit
PASSED  tests/test_core.py::TestSession::test_record_generation
PASSED  tests/test_core.py::TestSession::test_list_history_order
PASSED  tests/test_core.py::TestSession::test_status
PASSED  tests/test_core.py::TestValidateParams::test_valid_defaults
PASSED  tests/test_core.py::TestValidateParams::test_box_size_limits
PASSED  tests/test_core.py::TestValidateParams::test_border_limits
PASSED  tests/test_core.py::TestValidateParams::test_error_correction_valid
PASSED  tests/test_core.py::TestValidateParams::test_error_correction_invalid
PASSED  tests/test_core.py::TestValidateParams::test_module_style_valid
PASSED  tests/test_core.py::TestValidateParams::test_module_style_invalid
PASSED  tests/test_core.py::TestValidateParams::test_color_valid
PASSED  tests/test_core.py::TestValidateParams::test_color_invalid
PASSED  tests/test_core.py::TestValidateParams::test_logo_size_limits
PASSED  tests/test_core.py::TestGenerateQR::test_generate_returns_image
PASSED  tests/test_core.py::TestGenerateQR::test_image_dimensions
PASSED  tests/test_core.py::TestGenerateQR::test_default_params
PASSED  tests/test_core.py::TestGenerateQR::test_all_module_styles
PASSED  tests/test_core.py::TestGenerateQR::test_empty_data_raises
PASSED  tests/test_core.py::TestGenerateQR::test_logo_missing_raises
PASSED  tests/test_core.py::TestGenerateSVG::test_svg_returns_string
PASSED  tests/test_core.py::TestGenerateSVG::test_svg_starts_with_xml
PASSED  tests/test_core.py::TestGenerateSVG::test_svg_empty_data_raises
PASSED  tests/test_core.py::TestExport::test_save_png
PASSED  tests/test_core.py::TestExport::test_save_jpg
PASSED  tests/test_core.py::TestExport::test_save_unsupported_format
PASSED  tests/test_core.py::TestExport::test_save_svg
PASSED  tests/test_core.py::TestExport::test_export_info_png
PASSED  tests/test_core.py::TestExport::test_export_info_missing
```
