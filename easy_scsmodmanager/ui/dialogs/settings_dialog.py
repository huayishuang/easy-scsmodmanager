"""Settings dialog: UI language and manual game-path overrides.

Writes through a :class:`SettingsStore`. The language change only takes effect
on the next start (``t()`` resolves at widget construction), so the dialog says
so rather than pretending to switch live. An empty path means "auto-detect".
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from easy_scsmodmanager.core.game_paths import Game
from easy_scsmodmanager.core.settings_store import SettingsStore
from easy_scsmodmanager.ui.theme import Theme
from easy_scsmodmanager.utils.i18n import available_languages, current_language, t

_DOCUMENT_GAMES = (
    (Game.ETS2, "settings.paths.ets2_documents"),
    (Game.ATS, "settings.paths.ats_documents"),
)


class SettingsDialog(QDialog):
    def __init__(self, store: SettingsStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = store
        self._doc_paths: dict[Game, Path | None] = {
            game: store.get_documents_override(game) for game, _ in _DOCUMENT_GAMES
        }
        self._doc_edits: dict[Game, QLineEdit] = {}

        self.setWindowTitle(t("dialog.settings.title"))
        self.setMinimumWidth(560)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {Theme.BACKGROUND}; }}
            QLabel {{ color: {Theme.TEXT}; }}
            QLineEdit, QComboBox {{
                background-color: {Theme.SURFACE}; color: {Theme.TEXT};
                border: 1px solid {Theme.SURFACE_HOVER}; border-radius: 3px;
                padding: 4px 6px;
            }}
            QPushButton {{
                background-color: {Theme.SURFACE}; color: {Theme.TEXT};
                border: 1px solid {Theme.SURFACE_HOVER}; border-radius: 3px;
                padding: 4px 10px;
            }}
            QPushButton:hover {{ background-color: {Theme.SURFACE_HOVER}; }}
        """)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        form = QFormLayout()
        self._lang_combo = QComboBox()
        for code, name in available_languages().items():
            self._lang_combo.addItem(name, code)
        idx = self._lang_combo.findData(self._store.get_language() or current_language())
        self._lang_combo.setCurrentIndex(max(idx, 0))
        form.addRow(t("settings.language.label"), self._lang_combo)
        root.addLayout(form)

        hint = QLabel(t("settings.language.restart_hint"))
        hint.setStyleSheet(f"color: {Theme.TEXT_DIM};")
        root.addWidget(hint)

        heading = QLabel(t("settings.paths.heading"))
        heading.setStyleSheet(f"color: {Theme.TEXT_DIM}; margin-top: 6px;")
        root.addWidget(heading)
        for game, label_key in _DOCUMENT_GAMES:
            root.addLayout(self._build_path_row(game, label_key))

        buttons = QDialogButtonBox()
        buttons.addButton(t("dialog.settings.save"), QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton(t("dialog.settings.cancel"), QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _build_path_row(self, game: Game, label_key: str) -> QHBoxLayout:
        row = QHBoxLayout()
        label = QLabel(t(label_key))
        label.setMinimumWidth(170)

        edit = QLineEdit()
        edit.setReadOnly(True)
        edit.setPlaceholderText(t("settings.paths.auto"))
        path = self._doc_paths[game]
        if path is not None:
            edit.setText(str(path))
        self._doc_edits[game] = edit

        browse = QPushButton(t("settings.paths.browse"))
        browse.clicked.connect(lambda: self._on_browse(game))
        reset = QPushButton(t("settings.paths.reset"))
        reset.clicked.connect(lambda: self._on_reset(game))

        row.addWidget(label)
        row.addWidget(edit, 1)
        row.addWidget(browse)
        row.addWidget(reset)
        return row

    def _on_browse(self, game: Game) -> None:
        chosen = QFileDialog.getExistingDirectory(self, t("settings.browse_caption"))
        if chosen:
            self._doc_paths[game] = Path(chosen)
            self._doc_edits[game].setText(chosen)

    def _on_reset(self, game: Game) -> None:
        self._doc_paths[game] = None
        self._doc_edits[game].setText("")

    def selected_language(self) -> str:
        return str(self._lang_combo.currentData())

    def accept(self) -> None:
        self._store.set_language(self._lang_combo.currentData())
        for game, _ in _DOCUMENT_GAMES:
            self._store.set_documents_override(game, self._doc_paths[game])
        super().accept()
