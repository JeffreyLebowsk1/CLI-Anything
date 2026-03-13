"""QRcoder CLI — session management with undo/redo."""

import copy
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class Session:
    """Manages QR generation session state with undo/redo history.

    The session tracks default style settings (colors, module style, etc.)
    so that repeated generate commands inherit the current style without
    repeating every flag each time.  A history of generated QR codes is
    also maintained for inspection.
    """

    MAX_UNDO = 50

    # ── Default style settings ─────────────────────────────────────────
    DEFAULT_STYLE: Dict[str, Any] = {
        "box_size": 10,
        "border": 4,
        "error_correction": "M",
        "fg_color": "#000000",
        "bg_color": "#FFFFFF",
        "module_style": "square",
        "module_corner_radius": 0,
        "logo_path": None,
        "logo_size_percent": 30,
        "logo_border": 5,
    }

    def __init__(self) -> None:
        self.style: Dict[str, Any] = copy.deepcopy(self.DEFAULT_STYLE)
        self._undo_stack: List[Dict[str, Any]] = []
        self._redo_stack: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []  # generation log
        self._modified: bool = False

    # ── Undo/redo ──────────────────────────────────────────────────────

    def snapshot(self, description: str = "") -> None:
        """Save current style to undo stack before a mutation."""
        state = {
            "style": copy.deepcopy(self.style),
            "description": description,
            "timestamp": datetime.now().isoformat(),
        }
        self._undo_stack.append(state)
        if len(self._undo_stack) > self.MAX_UNDO:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        self._modified = True

    def undo(self) -> str:
        """Undo the last style change. Returns description."""
        if not self._undo_stack:
            raise RuntimeError("Nothing to undo.")
        self._redo_stack.append({
            "style": copy.deepcopy(self.style),
            "description": "redo point",
            "timestamp": datetime.now().isoformat(),
        })
        state = self._undo_stack.pop()
        self.style = state["style"]
        self._modified = True
        return state.get("description", "")

    def redo(self) -> str:
        """Redo the last undone style change. Returns description."""
        if not self._redo_stack:
            raise RuntimeError("Nothing to redo.")
        self._undo_stack.append({
            "style": copy.deepcopy(self.style),
            "description": "undo point",
            "timestamp": datetime.now().isoformat(),
        })
        state = self._redo_stack.pop()
        self.style = state["style"]
        self._modified = True
        return state.get("description", "")

    # ── Style management ───────────────────────────────────────────────

    def get_style(self) -> Dict[str, Any]:
        """Return a copy of the current style settings."""
        return copy.deepcopy(self.style)

    def set_style(self, key: str, value: Any) -> None:
        """Update a single style setting."""
        if key not in self.DEFAULT_STYLE:
            valid = ", ".join(sorted(self.DEFAULT_STYLE.keys()))
            raise ValueError(f"Unknown style key '{key}'. Valid keys: {valid}")
        self.snapshot(f"style set {key}={value}")
        self.style[key] = value

    def reset_style(self) -> None:
        """Reset all style settings to defaults."""
        self.snapshot("style reset")
        self.style = copy.deepcopy(self.DEFAULT_STYLE)

    # ── Generation history ─────────────────────────────────────────────

    def record_generation(self, data: str, output_path: str,
                          style: Dict[str, Any]) -> None:
        """Record a QR generation event in the history log."""
        self._history.append({
            "index": len(self._history),
            "data": data,
            "output": output_path,
            "style": copy.deepcopy(style),
            "timestamp": datetime.now().isoformat(),
        })

    def list_history(self) -> List[Dict[str, Any]]:
        """Return the generation history (most recent first)."""
        return list(reversed(self._history))

    # ── Session status ─────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Return a summary of the current session state."""
        return {
            "modified": self._modified,
            "undo_count": len(self._undo_stack),
            "redo_count": len(self._redo_stack),
            "history_count": len(self._history),
            "style": copy.deepcopy(self.style),
        }
