from __future__ import annotations

import sys
from pathlib import Path


def resource_path(relative: str) -> Path:
    """Resolve bundled resources both from source and PyInstaller onefile."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / relative


def load_stylesheet() -> str:
    path = resource_path("ui/styles.qss")
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""
