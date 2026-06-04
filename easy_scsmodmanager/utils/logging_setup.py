"""Logging setup that survives a windowed (no-console) build.

In a PyInstaller ``--windowed`` exe ``sys.stderr`` is ``None``, so stderr-only
logging is invisible and crashes vanish silently. We always write to a rotating
log file under a per-platform location, add stderr only when it exists, and
install an excepthook so an uncaught exception lands in the log before the app
dies. ``setup_logging`` returns the log file path so the UI can point users at it.
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Mapping
from logging.handlers import RotatingFileHandler
from pathlib import Path

_APP_DIR = "easy-scsmodmanager"


def _log_dir_for(platform: str, env: Mapping[str, str]) -> Path:
    """The writable log directory for a platform + environment (pure, testable)."""
    if platform == "win32":
        base = Path(env.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return base / _APP_DIR / "logs"
    if platform == "darwin":
        return Path.home() / "Library" / "Logs" / _APP_DIR
    base = Path(env.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    return base / _APP_DIR / "logs"


def default_log_dir() -> Path:
    return _log_dir_for(sys.platform, os.environ)


def setup_logging() -> Path:
    level_name = os.environ.get("ESCSMM_LOG", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    log_dir = default_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "easy-scsmodmanager.log"

    handlers: list[logging.Handler] = [
        # keep a little history so a crash report still has the prior run
        RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    ]
    # stderr is None in a windowed exe; only add it when a console is attached
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler(sys.stderr))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,
    )
    # httpx/httpcore log every request at INFO; too chatty for the workshop fetch
    for noisy in ("httpx", "httpcore", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _install_excepthook()
    return log_file


def _install_excepthook() -> None:
    """Route uncaught exceptions into the log; they are silent otherwise."""

    def hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logging.getLogger("easy_scsmodmanager").critical(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_tb)
        )

    sys.excepthook = hook
