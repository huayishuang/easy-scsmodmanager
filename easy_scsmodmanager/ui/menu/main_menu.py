"""Builds the main window's menu bar.

Pulled out of MainWindow so the window class stays focused on coordination.
The actions bind straight to the window's handlers, so the builder takes the
window itself (typed under TYPE_CHECKING to avoid an import cycle).
"""

from __future__ import annotations

import webbrowser
from typing import TYPE_CHECKING

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication

from easy_scsmodmanager.utils.i18n import t

if TYPE_CHECKING:
    from easy_scsmodmanager.ui.main_window import MainWindow

GITHUB_ISSUES_URL = "https://github.com/Switch-Bros/easy-scsmodmanager/issues"


def build_menu_bar(window: MainWindow) -> None:
    menu_bar = window.menuBar()

    file_menu = menu_bar.addMenu(t("menu.file"))
    refresh = QAction(t("menu.file.refresh"), window)
    refresh.setShortcut("F5")
    refresh.triggered.connect(window._on_refresh)
    file_menu.addAction(refresh)

    clear_cache = QAction(t("menu.file.clear_cache"), window)
    clear_cache.triggered.connect(window._on_clear_cache)
    file_menu.addAction(clear_cache)

    settings = QAction(t("menu.file.settings"), window)
    settings.triggered.connect(window._on_open_settings)
    file_menu.addAction(settings)

    file_menu.addSeparator()
    quit_action = QAction(t("menu.file.quit"), window)
    quit_action.setShortcut("Ctrl+Q")
    quit_action.triggered.connect(QApplication.instance().quit)
    file_menu.addAction(quit_action)

    tools_menu = menu_bar.addMenu(t("menu.tools"))
    extract = QAction(t("menu.tools.extract"), window)
    extract.triggered.connect(window._on_open_extract)
    tools_menu.addAction(extract)

    help_menu = menu_bar.addMenu(t("menu.help"))
    about = QAction(t("menu.help.about"), window)
    about.triggered.connect(window._show_about)
    help_menu.addAction(about)

    issues = QAction(t("menu.help.report_issue"), window)
    issues.triggered.connect(lambda: webbrowser.open(GITHUB_ISSUES_URL))
    help_menu.addAction(issues)
