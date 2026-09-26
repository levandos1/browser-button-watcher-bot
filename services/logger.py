from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.config import app_data_dir


def configure_logging() -> None:
    log_dir = app_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if root.handlers:
        return
    handler = RotatingFileHandler(
        log_dir / "button_watcher.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
    )
    root.addHandler(handler)
