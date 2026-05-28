"""Right-hand panel listing the profile's active mods in priority order.

Read-only in Phase 2 - no drag/drop, no priority buttons wired yet.
Renders each ActiveMod with the (decoded) display name and the
internal mod name as muted subtitle, plus a status colour dot that
matches the install state (green = installed locally, red = listed in
profile but not on disk).
"""

from __future__ import annotations

from collections.abc import Iterable

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from easy_scsmodmanager.services.profile_reader import ActiveMod
from easy_scsmodmanager.ui.theme import Theme
from easy_scsmodmanager.utils.i18n import t


class ActiveModList(QWidget):
    """Title bar + scrollable list of active mods."""

    selection_changed = pyqtSignal(list)  # list[ActiveMod]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._installed_names: set[str] = set()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        header = QHBoxLayout()
        self._title = QLabel(t("active_panel.title"))
        self._title.setStyleSheet(f"color: {Theme.ACCENT}; font-weight: bold; font-size: 13px;")
        self._count = QLabel(t("active_panel.count", count=0))
        self._count.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px;")
        self._count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(self._title)
        header.addStretch(1)
        header.addWidget(self._count)
        root.addLayout(header)

        self._list = QListWidget()
        self._list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {Theme.SURFACE};
                color: {Theme.TEXT};
                border: 1px solid {Theme.SURFACE_HOVER};
                border-radius: 4px;
                padding: 2px;
            }}
            QListWidget::item {{
                padding: 4px 6px;
                border-radius: 2px;
            }}
            QListWidget::item:selected {{
                background-color: {Theme.PRIMARY};
                color: {Theme.TEXT};
            }}
            """
        )
        self._list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._list.itemSelectionChanged.connect(self._on_selection_changed)
        root.addWidget(self._list)

        self._empty_hint = QLabel(t("active_panel.empty"))
        self._empty_hint.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-style: italic; padding: 8px;"
        )
        self._empty_hint.setWordWrap(True)
        self._empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_hint.hide()
        root.addWidget(self._empty_hint)

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #

    def set_active_mods(
        self,
        mods: Iterable[ActiveMod],
        *,
        installed_names: set[str] | None = None,
    ) -> None:
        """Replace the list. ``installed_names`` is the set of mod stems
        present on disk - mods missing from disk render in red."""
        self._installed_names = installed_names or set()
        self._list.clear()
        # Profile.active_mods stores priority 0 at the bottom; show the
        # highest priority at the top of the list, matching the in-game UI.
        ordered = list(reversed(list(mods)))
        for mod in ordered:
            item = QListWidgetItem(self._format_label(mod))
            item.setData(Qt.ItemDataRole.UserRole, mod)
            item.setIcon(_status_icon(self._status_for(mod)))
            item.setToolTip(f"{mod.name}\n{mod.display_name}")
            self._list.addItem(item)

        self._count.setText(t("active_panel.count", count=len(ordered)))
        self._empty_hint.setVisible(len(ordered) == 0)
        self._list.setVisible(len(ordered) > 0)

    def selected_mods(self) -> list[ActiveMod]:
        return [
            self._list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self._list.count())
            if self._list.item(i).isSelected()
        ]

    # ------------------------------------------------------------------ #
    # internals
    # ------------------------------------------------------------------ #

    def _on_selection_changed(self) -> None:
        self.selection_changed.emit(self.selected_mods())

    def _format_label(self, mod: ActiveMod) -> str:
        if mod.display_name:
            return mod.display_name
        return mod.name

    def _status_for(self, mod: ActiveMod) -> str:
        if mod.name in self._installed_names:
            return "active"
        return "incompatible"


def _status_icon(kind: str) -> QIcon:
    color = QColor(Theme.status_color(kind))
    pix = QPixmap(QSize(10, 10))
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, 10, 10)
    painter.end()
    return QIcon(pix)
