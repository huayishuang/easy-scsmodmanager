"""Right-hand panel listing the profile's active mods in priority order.

Read-only in Phase 2 - no drag/drop, no priority buttons wired yet.
Renders each ActiveMod with the (decoded) display name and a small
thumbnail when the scanner has cached an icon for that mod. The mod's
internal name lands in the tooltip together with an install hint.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
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

ICON_SIZE = QSize(32, 18)  # 16:9 mini-thumbnail


class ActiveModList(QWidget):
    """Title bar + scrollable list of active mods."""

    selection_changed = pyqtSignal(list)  # list[ActiveMod]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._installed_names: set[str] = set()
        self._placeholder_icon = _placeholder_icon()

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
        self._list.setIconSize(ICON_SIZE)
        self._list.setStyleSheet(f"""
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
            """)
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
        icon_for: Callable[[ActiveMod], bytes | None] | None = None,
    ) -> None:
        """Replace the list.

        ``installed_names`` is the set of mod stems present on disk - the
        tooltip mentions missing ones. ``icon_for`` is an optional
        callable returning cached icon bytes per ActiveMod.
        """
        self._installed_names = installed_names or set()
        self._list.clear()
        # Profile.active_mods stores priority 0 at the bottom; show the
        # highest priority at the top of the list, matching the in-game UI.
        ordered = list(reversed(list(mods)))
        for mod in ordered:
            item = QListWidgetItem(self._format_label(mod))
            item.setData(Qt.ItemDataRole.UserRole, mod)
            item.setIcon(self._icon_for_mod(mod, icon_for))
            item.setToolTip(self._tooltip_for(mod))
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

    def _icon_for_mod(
        self,
        mod: ActiveMod,
        icon_for: Callable[[ActiveMod], bytes | None] | None,
    ) -> QIcon:
        if icon_for is not None:
            data = icon_for(mod)
            if data:
                pix = QPixmap()
                if pix.loadFromData(data):
                    return QIcon(
                        pix.scaled(
                            ICON_SIZE,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )
        return self._placeholder_icon

    def _tooltip_for(self, mod: ActiveMod) -> str:
        lines = [mod.display_name or mod.name, f"id: {mod.name}"]
        if mod.name not in self._installed_names:
            lines.append("(currently missing from disk)")
        return "\n".join(lines)


def _placeholder_icon() -> QIcon:
    """A muted filled rectangle used when no per-mod icon is cached."""
    from PyQt6.QtGui import QColor, QPainter

    pix = QPixmap(ICON_SIZE)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(Theme.SURFACE_HOVER))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(0, 0, ICON_SIZE.width(), ICON_SIZE.height(), 2, 2)
    painter.end()
    return QIcon(pix)
