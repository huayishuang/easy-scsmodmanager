"""The Share menu exists with its five actions."""

from __future__ import annotations

import pytest

pytest.importorskip("pytestqt")

from easy_scsmodmanager.ui.main_window import MainWindow  # noqa: E402
from easy_scsmodmanager.utils.i18n import t  # noqa: E402


def test_share_menu_actions(qtbot) -> None:
    window = MainWindow(auto_scan=False)
    qtbot.addWidget(window)

    menus = [a.text() for a in window.menuBar().actions()]
    assert t("menu.share") in menus
    share_menu = next(a.menu() for a in window.menuBar().actions() if a.text() == t("menu.share"))
    labels = [a.text() for a in share_menu.actions()]
    assert labels == [
        t("menu.share.create_code"),
        t("menu.share.redeem_code"),
        t("menu.share.export_file"),
        t("menu.share.import_file"),
        t("menu.share.from_profile"),
    ]
