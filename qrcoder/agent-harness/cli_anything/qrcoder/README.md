# cli-anything-qrcoder

An agent-native CLI interface for [QRcoder-v1](https://github.com/JeffreyLebowsk1/QRcoder-v1) —
a feature-rich QR code generator.  Wraps the `qrcode` + `Pillow` libraries
to expose all generation options through a clean, scriptable command line
with JSON output for AI agent consumption.

## Installation

```bash
cd qrcoder/agent-harness
pip install -e .
```

**Runtime dependencies** (installed automatically):

| Package | Purpose |
|---------|---------|
| `qrcode[pil]` | QR code generation |
| `Pillow` | Image rendering |
| `click` | CLI framework |
| `prompt-toolkit` | REPL input |

## Quick Start

```bash
# Generate a simple QR code
cli-anything-qrcoder generate "https://example.com" -o site.png

# Custom style
cli-anything-qrcoder generate "Hello" \
    --fg-color "#1a73e8" \
    --bg-color "#f0f4ff" \
    --module-style circle \
    --output hello.png

# SVG output
cli-anything-qrcoder generate "https://example.com" --format svg -o site.svg

# Batch generation from a file
cli-anything-qrcoder batch urls.txt --output-dir ./qrcodes/

# Persistent style settings
cli-anything-qrcoder style set fg_color "#FF6600"
cli-anything-qrcoder style set module_style rounded
cli-anything-qrcoder generate "Now uses orange rounded style" -o styled.png

# JSON output for agents
cli-anything-qrcoder --json generate "data" -o out.png

# Interactive REPL
cli-anything-qrcoder
```

## Command Reference

### `generate <data>`

Generate a QR code for the given text or URL.

| Option | Default | Description |
|--------|---------|-------------|
| `--output / -o` | `qrcode.png` | Output file path |
| `--format / -f` | `png` | `png`, `jpg`, or `svg` |
| `--box-size` | 10 | Pixel size per module (1–40) |
| `--border` | 4 | Quiet zone modules (0–20) |
| `--error-correction` | `M` | `L`, `M`, `Q`, or `H` |
| `--fg-color` | `#000000` | Foreground hex colour |
| `--bg-color` | `#FFFFFF` | Background hex colour |
| `--module-style` | `square` | `square`, `circle`, `rounded`, `gapped`, `diamond` |
| `--logo` | — | Path to a logo image |
| `--logo-size` | 30 | Logo size as % of QR (1–50) |

### `batch <input-file>`

Generate one QR code per line in `input-file`.  Lines beginning with `#` and
blank lines are ignored.  Files are saved as `<index>_<sanitised-data>.<fmt>`.

### `style set <key> <value>` / `style list` / `style reset`

Manage persistent default style settings for the current session.

### `session status` / `session history`

Inspect session state and view generation history.

### `undo` / `redo`

Undo or redo the last `style set` change.

### `repl`

Interactive REPL mode (also the default when no subcommand is given).

## JSON Output

Pass `--json` before any subcommand to get machine-readable output:

```bash
cli-anything-qrcoder --json generate "https://example.com" -o out.png
```

```json
{
  "status": "ok",
  "output": "/home/user/out.png",
  "data": "https://example.com",
  "path": "/home/user/out.png",
  "format": "png",
  "size_bytes": 1234,
  "width": 290,
  "height": 290
}
```

## Running Tests

```bash
cd qrcoder/agent-harness
pip install -e ".[dev]"
pytest -v
```
