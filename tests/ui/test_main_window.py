"""Smoke test that the main window can be constructed and shown.

Uses pytest-qt's qtbot to manage the QApplication lifecycle.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pytestqt")

from easy_scsmodmanager.ui.main_window import MainWindow  # noqa: E402


def test_main_window_constructs(qtbot) -> None:
    window = MainWindow(auto_scan=False)
    qtbot.addWidget(window)
    assert window.windowTitle().startswith("Easy SCSModManager")
    assert window.minimumWidth() >= 1000


_PROFILE_TEMPLATE = (
    "SiiNunit\n{\nuser_profile : _nameless.x {\n" ' profile_name: "T"\n active_mods: 0\n}\n}\n'
)


def test_save_writes_active_list_to_profile(qtbot, tmp_path, monkeypatch) -> None:
    from PyQt6.QtWidgets import QMessageBox

    from easy_scsmodmanager.services.profile_reader import ActiveMod, read_profile

    window = MainWindow(auto_scan=False)
    qtbot.addWidget(window)

    sii = tmp_path / "profiles" / "abc" / "profile.sii"
    sii.parent.mkdir(parents=True)
    sii.write_text(_PROFILE_TEMPLATE, encoding="utf-8")
    window._profile_sii_path = sii
    window._profile = read_profile(sii)
    window._active_list.set_active_mods([ActiveMod("a", "A"), ActiveMod("b", "B")])

    # user declines the pre-save backup
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.No)
    window._on_save_clicked()

    assert [m.name for m in read_profile(sii).active_mods] == ["a", "b"]


def test_save_aborts_on_cancel(qtbot, tmp_path, monkeypatch) -> None:
    from PyQt6.QtWidgets import QMessageBox

    from easy_scsmodmanager.services.profile_reader import ActiveMod, read_profile

    window = MainWindow(auto_scan=False)
    qtbot.addWidget(window)

    sii = tmp_path / "profiles" / "abc" / "profile.sii"
    sii.parent.mkdir(parents=True)
    sii.write_text(_PROFILE_TEMPLATE, encoding="utf-8")
    window._profile_sii_path = sii
    window._profile = read_profile(sii)
    window._active_list.set_active_mods([ActiveMod("a", "A")])

    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Cancel)
    window._on_save_clicked()

    # nothing written - still zero active mods on disk
    assert list(read_profile(sii).active_mods) == []
