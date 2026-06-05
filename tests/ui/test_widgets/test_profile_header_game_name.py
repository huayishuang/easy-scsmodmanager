from __future__ import annotations

from pytestqt.qtbot import QtBot

from easy_scsmodmanager.ui.widgets.profile_header import ProfileHeader


def test_set_game_name_updates_backup_tooltip(qtbot: QtBot) -> None:
    header = ProfileHeader()
    qtbot.addWidget(header)

    header.set_game_name("ATS")
    tip = header._backup_btn.toolTip()

    assert "ATS" in tip
    assert "ETS2" not in tip
