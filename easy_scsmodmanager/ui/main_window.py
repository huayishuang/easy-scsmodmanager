"""Phase 2 read-only main window.

Layout::

    +-----------------------------------------------------------+
    |  MenuBar                                                  |
    +----------------------------------------+------------------+
    |  FilterToolbar                         | ProfileHeader    |
    |  ----------------------------------    | ---------------- |
    |  ModCardGrid (scroll)                  | ActiveModList    |
    |                                        |                  |
    |                                        |                  |
    +----------------------------------------+------------------+
    |  StatusBar: scan progress / counts / selection info       |
    +-----------------------------------------------------------+
"""

from __future__ import annotations

import logging
import webbrowser
from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from easy_scsmodmanager import __app_name__, __version__
from easy_scsmodmanager.core.db.scan_cache import ScanCache, default_cache_path
from easy_scsmodmanager.core.game_paths import Game, GameInstall, detect_game_installs
from easy_scsmodmanager.services.mod_scanner import ScannedMod
from easy_scsmodmanager.services.profile_reader import Profile, discover_profiles, read_profile
from easy_scsmodmanager.ui.theme import Theme
from easy_scsmodmanager.ui.threads.scan_thread import ScanResult, ScanThread
from easy_scsmodmanager.ui.widgets.active_mod_list import ActiveModList
from easy_scsmodmanager.ui.widgets.filter_toolbar import FilterState, FilterToolbar, SortKey
from easy_scsmodmanager.ui.widgets.mod_card_grid import ModCardGrid
from easy_scsmodmanager.ui.widgets.profile_header import ProfileHeader
from easy_scsmodmanager.utils.i18n import t

log = logging.getLogger(__name__)

GITHUB_ISSUES_URL = "https://github.com/Switch-Bros/easy-scsmodmanager/issues"


class MainWindow(QMainWindow):
    def __init__(self, *, game: Game = Game.ETS2, auto_scan: bool = True) -> None:
        super().__init__()
        self._game = game
        self._install: GameInstall | None = None
        self._profile: Profile | None = None
        self._all_mods: list[ScannedMod] = []
        self._filter = FilterState()
        self._cache = ScanCache(default_cache_path())
        self._scan_thread: ScanThread | None = None

        self.setWindowTitle(f"{__app_name__} {__version__}")
        self.setMinimumSize(QSize(1280, 760))
        self.setStyleSheet(f"QMainWindow {{ background-color: {Theme.BACKGROUND}; }}")

        self._build_menu_bar()
        self._build_central()
        self.statusBar().setStyleSheet(f"color: {Theme.TEXT_DIM};")

        if auto_scan:
            self._detect_install_and_scan()

    # ------------------------------------------------------------------ #
    # building
    # ------------------------------------------------------------------ #

    def _build_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu(t("menu.file"))
        refresh = QAction(t("menu.file.refresh"), self)
        refresh.setShortcut("F5")
        refresh.triggered.connect(self._on_refresh)
        file_menu.addAction(refresh)

        clear_cache = QAction(t("menu.file.clear_cache"), self)
        clear_cache.triggered.connect(self._on_clear_cache)
        file_menu.addAction(clear_cache)

        file_menu.addSeparator()
        quit_action = QAction(t("menu.file.quit"), self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(QApplication.instance().quit)
        file_menu.addAction(quit_action)

        help_menu = menu_bar.addMenu(t("menu.help"))
        about = QAction(t("menu.help.about"), self)
        about.triggered.connect(self._show_about)
        help_menu.addAction(about)

        issues = QAction(t("menu.help.report_issue"), self)
        issues.triggered.connect(lambda: webbrowser.open(GITHUB_ISSUES_URL))
        help_menu.addAction(issues)

    def _build_central(self) -> None:
        central = QWidget()
        central.setStyleSheet(f"background-color: {Theme.BACKGROUND};")
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 0)
        root.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)

        # Left side: filter + grid
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        self._filter_toolbar = FilterToolbar()
        self._filter_toolbar.filter_changed.connect(self._on_filter_changed)
        self._grid = ModCardGrid(columns=4)
        self._grid.selection_changed.connect(self._on_grid_selection_changed)
        left_layout.addWidget(self._filter_toolbar)
        left_layout.addWidget(self._grid, 1)

        # Right side: profile header + active list
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        self._profile_header = ProfileHeader()
        self._active_list = ActiveModList()
        right_layout.addWidget(self._profile_header)
        right_layout.addWidget(self._active_list, 1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter, 1)
        self.setCentralWidget(central)

    # ------------------------------------------------------------------ #
    # data flow
    # ------------------------------------------------------------------ #

    def _detect_install_and_scan(self) -> None:
        installs = detect_game_installs(self._game)
        if not installs:
            self.statusBar().showMessage(t("status_bar.no_install"))
            return
        # Prefer the proton install when available because that is where
        # most users have their workshop subscriptions linked.
        proton = next((i for i in installs if i.kind.value == "proton"), None)
        self._install = proton or installs[0]
        self._load_profile()
        self._start_scan()

    def _load_profile(self) -> None:
        if self._install is None:
            return
        paths = discover_profiles(self._install)
        if not paths:
            self._profile = None
            self._profile_header.set_profile(None)
            return
        # Pick the most recently modified profile - typically the active one.
        path = max(paths, key=lambda p: p.stat().st_mtime)
        try:
            self._profile = read_profile(path)
        except Exception as exc:
            log.warning("failed to read profile %s: %s", path, exc)
            self._profile = None
            self._profile_header.set_profile(None)
            return
        avatar = path.parent / "online_avatar.png"
        self._profile_header.set_profile(
            self._profile,
            avatar_path=avatar if avatar.exists() else None,
            meta_text=t("active_panel.count", count=len(self._profile.active_mods)),
        )

    def _start_scan(self) -> None:
        if self._install is None:
            return
        self.statusBar().showMessage(
            t("status_bar.scanning", path=str(self._install.documents_dir))
        )
        if self._scan_thread is not None and self._scan_thread.isRunning():
            self._scan_thread.wait()
        self._scan_thread = ScanThread(self._install, self._cache)
        self._scan_thread.finished_with_result.connect(self._on_scan_finished)
        self._scan_thread.failed.connect(self._on_scan_failed)
        self._scan_thread.start()

    def _on_scan_finished(self, result: ScanResult) -> None:
        self._all_mods = result.mods
        active_names = self._active_names()
        installed_names = {mod.path.stem for mod in self._all_mods}

        self._refresh_grid()
        if self._profile is not None:
            self._active_list.set_active_mods(
                self._profile.active_mods,
                installed_names=installed_names,
                icon_for=self._active_icon_for,
            )

        active_count = sum(1 for m in self._all_mods if m.path.stem in active_names)
        errors = sum(1 for m in self._all_mods if m.manifest is None and m.error is not None)
        self.statusBar().showMessage(
            t(
                "status_bar.scan_done",
                total=len(self._all_mods),
                active=active_count,
                errors=errors,
                elapsed=result.elapsed_seconds,
            )
        )
        self._populate_categories()

    def _on_scan_failed(self, message: str) -> None:
        self.statusBar().showMessage(message)

    def _populate_categories(self) -> None:
        cats: set[str] = set()
        for mod in self._all_mods:
            if mod.manifest is not None:
                cats.update(mod.manifest.categories)
        self._filter_toolbar.set_categories(sorted(cats))

    def _refresh_grid(self) -> None:
        filtered = self._apply_filter(self._all_mods, self._filter)
        self._grid.set_mods(
            filtered,
            active_names=self._active_names(),
            icon_for=self._icon_for,
        )

    def _icon_for(self, mod: ScannedMod) -> bytes | None:
        entry = self._cache.get(mod.path)
        if entry is None:
            return None
        return entry.icon_bytes

    def _active_icon_for(self, active_mod) -> bytes | None:
        # The cache is keyed by mod-file path; the profile only knows the
        # stem. Look up the scanned mod whose path matches and return its
        # cached icon bytes if any.
        match = next((m for m in self._all_mods if m.path.stem == active_mod.name), None)
        if match is None:
            return None
        entry = self._cache.get(match.path)
        if entry is None:
            return None
        return entry.icon_bytes

    def _active_names(self) -> set[str]:
        if self._profile is None:
            return set()
        return {m.name for m in self._profile.active_mods}

    def _apply_filter(self, mods: list[ScannedMod], state: FilterState) -> list[ScannedMod]:
        needle = state.search.lower().strip()
        result: list[ScannedMod] = []
        for mod in mods:
            display = (mod.manifest.display_name if mod.manifest else mod.path.stem).lower()
            author = (mod.manifest.author if mod.manifest else "").lower()
            cats = list(mod.manifest.categories) if mod.manifest else []
            if needle and not (
                needle in display
                or needle in author
                or needle in mod.path.name.lower()
                or any(needle in c.lower() for c in cats)
            ):
                continue
            if state.category is not None and state.category not in cats:
                continue
            result.append(mod)

        result.sort(key=lambda m: self._sort_key(m, state.sort_key), reverse=state.sort_descending)
        return result

    def _sort_key(self, mod: ScannedMod, key: SortKey) -> tuple[int, str | float]:
        # Tuple sort with a category index so the secondary string stays
        # comparable across all keys (mypy needs a single return type).
        if key is SortKey.NAME:
            return (0, (mod.manifest.display_name if mod.manifest else mod.path.stem).lower())
        if key is SortKey.AUTHOR:
            return (0, (mod.manifest.author if mod.manifest else "").lower())
        if key is SortKey.DATE:
            return (0, mod.path.stat().st_mtime)
        if key is SortKey.STATUS:
            return (0 if mod.path.stem in self._active_names() else 1, mod.path.name.lower())
        return (0, mod.path.name.lower())

    # ------------------------------------------------------------------ #
    # signal handlers
    # ------------------------------------------------------------------ #

    def _on_filter_changed(self, state: FilterState) -> None:
        self._filter = state
        self._refresh_grid()

    def _on_grid_selection_changed(self, mods: list[ScannedMod]) -> None:
        if not mods:
            self.statusBar().clearMessage()
            return
        self.statusBar().showMessage(t("status_bar.selection", count=len(mods)))

    def _on_refresh(self) -> None:
        if self._install is None:
            self._detect_install_and_scan()
            return
        self._start_scan()

    def _on_clear_cache(self) -> None:
        removed = self._cache.clear()
        self.statusBar().showMessage(f"Cleared {removed} cache entries")
        if self._install is not None:
            self._start_scan()

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            t("dialog.about.title"),
            t("dialog.about.body", version=__version__),
        )

    # ------------------------------------------------------------------ #
    # lifecycle
    # ------------------------------------------------------------------ #

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._scan_thread is not None and self._scan_thread.isRunning():
            self._scan_thread.wait(5000)
        self._cache.close()
        super().closeEvent(event)


# Reference avoidance for unused-import linters
_ = Path
