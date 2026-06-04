from __future__ import annotations

import logging
from pathlib import Path

import pytest

from easy_scsmodmanager.utils.logging_setup import (
    _log_dir_for,
    setup_logging,
)


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    """Keep logs out of the real state dir and reset root handlers per test."""
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "AppData"))
    root = logging.getLogger()
    saved = root.handlers[:]
    root.handlers.clear()
    yield
    for h in root.handlers[:]:
        h.close()
    root.handlers.clear()
    root.handlers.extend(saved)


def test_log_dir_windows_uses_localappdata() -> None:
    d = _log_dir_for("win32", {"LOCALAPPDATA": "C:/Users/x/AppData/Local"})
    assert d == Path("C:/Users/x/AppData/Local") / "easy-scsmodmanager" / "logs"


def test_log_dir_linux_uses_xdg_state() -> None:
    d = _log_dir_for("linux", {"XDG_STATE_HOME": "/home/x/.local/state"})
    assert d == Path("/home/x/.local/state") / "easy-scsmodmanager" / "logs"


def test_log_dir_linux_falls_back_to_home_state() -> None:
    d = _log_dir_for("linux", {})
    assert d == Path.home() / ".local" / "state" / "easy-scsmodmanager" / "logs"


def test_setup_logging_creates_a_log_file_and_returns_it() -> None:
    log_file = setup_logging()
    assert log_file.exists()
    assert log_file.name == "easy-scsmodmanager.log"


def test_setup_logging_survives_without_stderr(monkeypatch) -> None:
    # a windowed exe has sys.stderr == None; setup must not raise
    monkeypatch.setattr("sys.stderr", None)
    log_file = setup_logging()
    assert log_file.exists()


def test_quiets_noisy_http_loggers() -> None:
    setup_logging()
    assert logging.getLogger("httpx").level >= logging.WARNING
    assert logging.getLogger("httpcore").level >= logging.WARNING
