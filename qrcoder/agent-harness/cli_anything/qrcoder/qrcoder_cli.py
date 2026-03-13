#!/usr/bin/env python3
"""QRcoder CLI — An agent-native command-line interface for QRcoder-v1.

Wraps the qrcode + Pillow libraries to provide stateful, scriptable QR code
generation with full style customisation.  Supports both one-shot commands
and an interactive REPL mode for agent workflows.

Usage:
    # One-shot commands
    cli-anything-qrcoder generate "https://example.com" --output qr.png
    cli-anything-qrcoder generate "Hello" --fg-color "#FF0000" --module-style circle
    cli-anything-qrcoder batch links.txt --output-dir ./qrcodes/
    cli-anything-qrcoder style set fg_color "#1a73e8"
    cli-anything-qrcoder style list

    # Interactive REPL
    cli-anything-qrcoder
    cli-anything-qrcoder repl
"""

import json
import os
import sys
from typing import Optional

import click

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli_anything.qrcoder.core.session import Session
from cli_anything.qrcoder.core import generate as gen_mod
from cli_anything.qrcoder.core import export as export_mod
from cli_anything.qrcoder.utils.qrcoder_backend import ensure_available

# ── Global state ───────────────────────────────────────────────────────

_session: Optional[Session] = None
_json_output: bool = False
_repl_mode: bool = False


def get_session() -> Session:
    global _session
    if _session is None:
        _session = Session()
    return _session


# ── Output helpers ─────────────────────────────────────────────────────


def output(data, message: str = "") -> None:
    if _json_output:
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        if message:
            click.echo(message)
        if isinstance(data, dict):
            _print_dict(data)
        elif isinstance(data, list):
            _print_list(data)
        elif data is not None:
            click.echo(str(data))


def _print_dict(d: dict, indent: int = 0) -> None:
    prefix = "  " * indent
    for k, v in d.items():
        if isinstance(v, dict):
            click.echo(f"{prefix}{k}:")
            _print_dict(v, indent + 1)
        elif isinstance(v, list):
            click.echo(f"{prefix}{k}:")
            _print_list(v, indent + 1)
        else:
            click.echo(f"{prefix}{k}: {v}")


def _print_list(items: list, indent: int = 0) -> None:
    prefix = "  " * indent
    for i, item in enumerate(items):
        if isinstance(item, dict):
            click.echo(f"{prefix}[{i}]")
            _print_dict(item, indent + 1)
        else:
            click.echo(f"{prefix}- {item}")


def handle_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            if _json_output:
                click.echo(json.dumps({"error": str(e), "type": "file_not_found"}))
            else:
                click.echo(f"Error: {e}", err=True)
            if not _repl_mode:
                sys.exit(1)
        except (ValueError, RuntimeError) as e:
            if _json_output:
                click.echo(json.dumps({"error": str(e), "type": type(e).__name__}))
            else:
                click.echo(f"Error: {e}", err=True)
            if not _repl_mode:
                sys.exit(1)
    wrapper.__name__ = func.__name__
    return wrapper


# ── Root group ─────────────────────────────────────────────────────────


@click.group(invoke_without_command=True)
@click.option("--json", "json_out", is_flag=True, help="Output JSON for agent consumption")
@click.version_option("1.0.0", prog_name="cli-anything-qrcoder")
@click.pass_context
def cli(ctx: click.Context, json_out: bool) -> None:
    """QRcoder CLI — agent-native QR code generation.

    Run without a subcommand to enter interactive REPL mode.
    Use --json for machine-readable output.
    """
    global _json_output
    _json_output = json_out
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_out
    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


# ── generate command ───────────────────────────────────────────────────


@cli.command("generate")
@click.argument("data")
@click.option("--output", "-o", "output_path", default="qrcode.png", show_default=True,
              help="Output file path")
@click.option("--format", "-f", "fmt",
              type=click.Choice(["png", "jpg", "svg"], case_sensitive=False),
              default="png", show_default=True, help="Output format")
@click.option("--box-size", type=int, default=None,
              help="Pixel size of each module (1-40)")
@click.option("--border", type=int, default=None,
              help="Quiet zone in modules (0-20)")
@click.option("--error-correction", type=click.Choice(["L", "M", "Q", "H"],
              case_sensitive=False), default=None,
              help="Error correction level")
@click.option("--fg-color", default=None, help="Foreground colour (#hex)")
@click.option("--bg-color", default=None, help="Background colour (#hex)")
@click.option("--module-style",
              type=click.Choice(["square", "circle", "rounded", "gapped", "diamond"],
                                case_sensitive=False),
              default=None, help="Module shape")
@click.option("--logo", default=None, help="Path to logo image to embed")
@click.option("--logo-size", type=int, default=None,
              help="Logo size as %% of QR size (1-50)")
@click.pass_context
@handle_error
def generate(
    ctx: click.Context,
    data: str,
    output_path: str,
    fmt: str,
    box_size: Optional[int],
    border: Optional[int],
    error_correction: Optional[str],
    fg_color: Optional[str],
    bg_color: Optional[str],
    module_style: Optional[str],
    logo: Optional[str],
    logo_size: Optional[int],
) -> None:
    """Generate a QR code for DATA.

    DATA can be any text — a URL, plain text, contact info, etc.

    Example:
        cli-anything-qrcoder generate "https://example.com" -o site.png
    """
    sess = get_session()
    style = sess.get_style()

    # CLI flags override session style
    if box_size is not None:
        style["box_size"] = box_size
    if border is not None:
        style["border"] = border
    if error_correction is not None:
        style["error_correction"] = error_correction.upper()
    if fg_color is not None:
        style["fg_color"] = fg_color
    if bg_color is not None:
        style["bg_color"] = bg_color
    if module_style is not None:
        style["module_style"] = module_style
    if logo is not None:
        style["logo_path"] = logo
    if logo_size is not None:
        style["logo_size_percent"] = logo_size

    if fmt.lower() == "svg":
        svg = gen_mod.generate_svg(
            data=data,
            box_size=style["box_size"],
            border=style["border"],
            error_correction=style["error_correction"],
        )
        saved_path = export_mod.save_svg(svg, output_path)
    else:
        img = gen_mod.generate_qr(
            data=data,
            box_size=style["box_size"],
            border=style["border"],
            error_correction=style["error_correction"],
            fg_color=style["fg_color"],
            bg_color=style["bg_color"],
            module_style=style["module_style"],
            module_corner_radius=style["module_corner_radius"],
            logo_path=style["logo_path"],
            logo_size_percent=style["logo_size_percent"],
            logo_border=style["logo_border"],
        )
        saved_path = export_mod.save_image(img, output_path, fmt=fmt)

    info = export_mod.export_info(saved_path)
    sess.record_generation(data, saved_path, style)

    result = {"status": "ok", "output": saved_path, "data": data, **info}
    output(result, f"QR code saved to {saved_path}")


# ── batch command ──────────────────────────────────────────────────────


@cli.command("batch")
@click.argument("input_file")
@click.option("--output-dir", "-d", default=".", show_default=True,
              help="Directory for output files")
@click.option("--format", "-f", "fmt",
              type=click.Choice(["png", "jpg", "svg"], case_sensitive=False),
              default="png", show_default=True)
@click.pass_context
@handle_error
def batch(
    ctx: click.Context,
    input_file: str,
    output_dir: str,
    fmt: str,
) -> None:
    """Generate QR codes for every line in INPUT_FILE.

    INPUT_FILE should be a plain text file with one item per line.
    Empty lines and lines beginning with '#' are skipped.

    Example:
        cli-anything-qrcoder batch urls.txt --output-dir ./qrcodes/
    """
    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    sess = get_session()
    style = sess.get_style()
    os.makedirs(output_dir, exist_ok=True)

    results = []
    with open(input_file, encoding="utf-8") as fh:
        lines = [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]

    for i, data in enumerate(lines):
        safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in data[:40])
        out_name = os.path.join(output_dir, f"{i:04d}_{safe_name}.{fmt}")

        if fmt == "svg":
            svg = gen_mod.generate_svg(
                data=data,
                box_size=style["box_size"],
                border=style["border"],
                error_correction=style["error_correction"],
            )
            saved = export_mod.save_svg(svg, out_name)
        else:
            img = gen_mod.generate_qr(
                data=data,
                box_size=style["box_size"],
                border=style["border"],
                error_correction=style["error_correction"],
                fg_color=style["fg_color"],
                bg_color=style["bg_color"],
                module_style=style["module_style"],
                module_corner_radius=style["module_corner_radius"],
                logo_path=style["logo_path"],
                logo_size_percent=style["logo_size_percent"],
                logo_border=style["logo_border"],
            )
            saved = export_mod.save_image(img, out_name, fmt=fmt)

        sess.record_generation(data, saved, style)
        results.append({"index": i, "data": data, "output": saved})

    summary = {"status": "ok", "count": len(results), "output_dir": output_dir, "files": results}
    output(summary, f"Generated {len(results)} QR codes in {output_dir}")


# ── style group ────────────────────────────────────────────────────────


@cli.group("style")
def style_group() -> None:
    """Manage default style settings for QR code generation."""


@style_group.command("list")
@click.pass_context
def style_list(ctx: click.Context) -> None:
    """Show current default style settings."""
    sess = get_session()
    output(sess.get_style(), "Current style settings:")


@style_group.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
@handle_error
def style_set(ctx: click.Context, key: str, value: str) -> None:
    """Set a default style setting KEY to VALUE.

    Keys: box_size, border, error_correction, fg_color, bg_color,
          module_style, module_corner_radius, logo_path,
          logo_size_percent, logo_border

    Examples:
        cli-anything-qrcoder style set fg_color "#1a73e8"
        cli-anything-qrcoder style set module_style circle
        cli-anything-qrcoder style set box_size 15
    """
    sess = get_session()
    # Coerce numeric values
    int_keys = {"box_size", "border", "module_corner_radius",
                "logo_size_percent", "logo_border"}
    if key in int_keys:
        try:
            value = int(value)  # type: ignore[assignment]
        except ValueError:
            raise ValueError(f"'{key}' must be an integer, got '{value}'")
    elif key == "logo_path" and value.lower() in ("none", "null", ""):
        value = None  # type: ignore[assignment]

    sess.set_style(key, value)
    result = {"status": "ok", "key": key, "value": value}
    output(result, f"Style '{key}' set to '{value}'")


@style_group.command("reset")
@click.pass_context
def style_reset(ctx: click.Context) -> None:
    """Reset all style settings to defaults."""
    sess = get_session()
    sess.reset_style()
    output({"status": "ok", "style": sess.get_style()}, "Style reset to defaults")


# ── session group ──────────────────────────────────────────────────────


@cli.group("session")
def session_group() -> None:
    """Inspect and manage the current session."""


@session_group.command("status")
def session_status() -> None:
    """Show current session status."""
    sess = get_session()
    output(sess.status(), "Session status:")


@session_group.command("history")
@click.option("--limit", default=10, show_default=True,
              help="Maximum number of entries to show")
def session_history(limit: int) -> None:
    """Show recent QR code generation history."""
    sess = get_session()
    history = sess.list_history()[:limit]
    if not history:
        click.echo("No generation history yet.")
        return
    output(history, f"Last {len(history)} generated QR codes:")


# ── undo / redo ────────────────────────────────────────────────────────


@cli.command("undo")
@handle_error
def undo() -> None:
    """Undo the last style change."""
    sess = get_session()
    description = sess.undo()
    output({"status": "ok", "undone": description}, f"Undone: {description}")


@cli.command("redo")
@handle_error
def redo() -> None:
    """Redo the last undone style change."""
    sess = get_session()
    description = sess.redo()
    output({"status": "ok", "redone": description}, f"Redone: {description}")


# ── REPL ───────────────────────────────────────────────────────────────


@cli.command("repl")
def repl() -> None:
    """Start the interactive REPL (default when no subcommand is given).

    Type 'help' for a list of commands, 'quit' to exit.
    """
    global _repl_mode
    _repl_mode = True

    from cli_anything.qrcoder.utils.repl_skin import ReplSkin

    skin = ReplSkin("qrcoder", version="1.0.0")
    skin.print_banner()
    skin.info("Wraps JeffreyLebowsk1/QRcoder-v1 as an agent-native CLI")
    skin.hint("Type 'help' for commands, 'quit' to exit")
    print()

    pt_session = skin.create_prompt_session()

    commands_help = {
        "generate <data>": "Generate a QR code",
        "generate <data> --output <path>": "Save to a specific file",
        "generate <data> --format svg": "Output as SVG",
        "generate <data> --fg-color '#hex'": "Custom foreground colour",
        "generate <data> --module-style circle": "Change module shape",
        "batch <file>": "Generate QR codes for every line in a file",
        "style list": "Show current style settings",
        "style set <key> <value>": "Update a style setting",
        "style reset": "Reset style to defaults",
        "session status": "Show session status",
        "session history": "Show generation history",
        "undo": "Undo last style change",
        "redo": "Redo last undone style change",
        "help": "Show this help",
        "quit": "Exit the REPL",
    }

    while True:
        try:
            sess = get_session()
            line = skin.get_input(pt_session, context="qrcoder")
        except (KeyboardInterrupt, EOFError):
            skin.print_goodbye()
            break

        line = line.strip()
        if not line:
            continue
        if line in ("quit", "exit", "q"):
            skin.print_goodbye()
            break
        if line in ("help", "?", "h"):
            skin.help(commands_help)
            continue

        # Parse and dispatch the command through Click
        try:
            args = _split_args(line)
            cli.main(args=args, standalone_mode=False, obj={})
        except SystemExit:
            pass
        except Exception as exc:
            skin.error(str(exc))

    _repl_mode = False


def _split_args(line: str) -> list:
    """Split a REPL line into argv tokens, respecting quoted strings."""
    import shlex
    try:
        return shlex.split(line)
    except ValueError:
        return line.split()


# ── Entry point ────────────────────────────────────────────────────────


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
