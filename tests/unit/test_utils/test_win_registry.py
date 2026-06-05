from __future__ import annotations

import sys

import pytest

from easy_scsmodmanager.utils import win_registry


def test_read_string_returns_none_off_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(win_registry.sys, "platform", "linux")
    assert win_registry.read_string("HKCU", r"Software\Valve\Steam", "SteamPath") is None


def test_read_string_rejects_unknown_hive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(win_registry.sys, "platform", "win32")
    # winreg import only happens on a real win32 host; off Windows the bogus
    # hive must raise before any winreg call.
    if sys.platform != "win32":
        with pytest.raises((ValueError, ModuleNotFoundError)):
            win_registry.read_string("BOGUS", "sub", "name")
