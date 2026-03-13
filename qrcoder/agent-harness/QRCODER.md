# Agent Harness: QRcoder-v1 → CLI-Anything

## Source Repository

**JeffreyLebowsk1/QRcoder-v1** — A feature-rich Windows QR code generator with GUI and web interface.

## Phase 1: Codebase Analysis

### Backend Engine

- **Primary**: `qrcode` Python library (pure Python QR code generation)
- **Rendering**: `Pillow` (PIL) for raster output; `qrcode.image.svg` for SVG
- **Web layer**: FastAPI (`src/api_server.py`) — already headless-capable
- **GUI layer**: Tkinter (`src/qr_generator.py`) — not needed for CLI

### Key Source Files

| File | Purpose |
|------|---------|
| `src/qr_core.py` | Core generation logic — `QRGeneratorCore.generate_qr_image()` |
| `src/qr_generator.py` | Tkinter GUI — wraps qr_core |
| `src/api_server.py` | FastAPI REST endpoints |
| `src/launcher.py` | App launcher |

### GUI Action → API Mapping

| GUI Action | CLI Command |
|-----------|-------------|
| Enter text / URL | `generate <data>` |
| Set box size slider | `--box-size N` |
| Set border slider | `--border N` |
| Error correction dropdown | `--error-correction L/M/Q/H` |
| Module style dropdown | `--module-style square/circle/...` |
| Foreground colour picker | `--fg-color '#hex'` |
| Background colour picker | `--bg-color '#hex'` |
| Add logo button | `--logo <path>` |
| Save QR Code button | `--output <path>` |

### Data Model

QRcoder-v1 is **stateless by design** — each button press generates a fresh
image.  The CLI harness adds statefulness through a session layer that
persists default style settings across commands, enabling agents to set style
once and generate many codes without repeating every flag.

## Phase 2: CLI Architecture Design

### Interaction Model

- **One-shot mode**: single `generate` command ideal for scripting
- **REPL mode**: interactive session for iterative style exploration
- **Both** implemented (default is REPL when no subcommand given)

### Command Groups

```
cli-anything-qrcoder
  generate <data>        # Core operation
  batch <file>           # Bulk generation
  style
    list                 # Show current defaults
    set <key> <value>    # Mutate a setting
    reset                # Restore defaults
  session
    status               # Session metadata
    history              # Recent generations
  undo                   # Undo last style change
  redo                   # Redo last undone change
  repl                   # Interactive REPL
```

### State Model

```json
{
  "style": {
    "box_size": 10,
    "border": 4,
    "error_correction": "M",
    "fg_color": "#000000",
    "bg_color": "#FFFFFF",
    "module_style": "square",
    "module_corner_radius": 0,
    "logo_path": null,
    "logo_size_percent": 30,
    "logo_border": 5
  },
  "undo_stack": [...],
  "history": [{"data": "...", "output": "...", "timestamp": "..."}]
}
```

### Output Format

- Human-readable by default (path printed on success)
- JSON via `--json` flag — structured for agent consumption

## Phase 3: Implementation Notes

### Backend Integration

The CLI harness wraps `qrcode` + `Pillow` directly (same libraries used by
QRcoder-v1's `qr_core.py`).  This avoids importing the GUI/Tkinter layer
entirely, making the harness headless and cross-platform.

### SVG Support

`qrcode.image.svg.SvgImage` factory is used for SVG output, matching the
vector output path in the original `api_server.py`.

### Logo Embedding

Logo embedding mirrors `QRGeneratorCore._add_logo_to_qr()`:
1. Open logo with Pillow
2. Resize to `logo_size_percent`% of QR dimensions
3. Paste with a white border onto the centre of the QR image

## Phase 4–5: Tests

See `cli_anything/qrcoder/tests/test_core.py` and `tests/TEST.md`.

## Applying CLI-Anything to Other Repos

The same methodology applies to:

- **worker** (private): Once the repo is accessible, run
  `/cli-anything:cli-anything <path-to-worker>` from Claude Code or follow
  the HARNESS.md SOP to analyse the codebase and generate a harness.

- **urban-invention** (private): Same approach.  If the project has a GUI or
  a rich API, the cli-anything framework can expose it as a stateful,
  agent-controllable CLI with JSON output.

The key steps are always:
1. Identify the backend engine (library/framework that powers the GUI)
2. Map GUI actions to function calls
3. Build Click commands around those function calls
4. Add session state, undo/redo, and REPL for interactive use
5. Add unit + E2E tests
