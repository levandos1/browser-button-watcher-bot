from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.constants import (
    DEFAULT_COOLDOWN_SECONDS,
    DEFAULT_ENDPOINT,
    DEFAULT_INTERVAL_MS,
)
from app.models import MatchMode


def app_data_dir() -> Path:
    base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    path = base / "ButtonWatcher"
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass(slots=True)
class AppConfig:
    endpoint: str = DEFAULT_ENDPOINT
    target_text: str = ""
    match_mode: str = MatchMode.EXACT.value
    interval_ms: int = DEFAULT_INTERVAL_MS
    cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS
    close_launched_browser_on_exit: bool = True
    window_width: int = 1040
    window_height: int = 760

    @classmethod
    def load(cls) -> "AppConfig":
        path = app_data_dir() / "config.json"
        if not path.exists():
            return cls()
        try:
            raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            allowed = set(cls.__dataclass_fields__)
            return cls(**{k: v for k, v in raw.items() if k in allowed})
        except (OSError, ValueError, TypeError):
            return cls()

    def save(self) -> None:
        path = app_data_dir() / "config.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(path)
