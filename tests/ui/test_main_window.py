"""Smoke test that the main window can be constructed and shown.

Uses pytest-qt's qtbot to manage the QApplication lifecycle.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pytestqt")

from easy_scsmodmanager.ui.main_window import MainWindow


def test_main_window_constructs(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.windowTitle().startswith("Easy SCSModManager")
    assert window.minimumWidth() >= 1000
