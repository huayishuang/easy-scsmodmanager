"""Top-right widget that identifies which profile is loaded.

For Phase 2 it shows the avatar (if available), the decoded profile
name and the active-mods count. Profile switching comes later via the
menu bar.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from easy_scsmodmanager.services.profile_reader import Profile
from easy_scsmodmanager.ui.theme import Theme
from easy_scsmodmanager.utils.i18n import t


class ProfileHeader(QWidget):
    AVATAR_SIZE = 48

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._profile: Profile | None = None

        self.setStyleSheet(f"background-color: {Theme.SURFACE}; border-radius: 4px;")

        root = QHBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 6)
        root.setSpacing(10)

        self._avatar = QLabel()
        self._avatar.setFixedSize(QSize(self.AVATAR_SIZE, self.AVATAR_SIZE))
        self._avatar.setStyleSheet(f"background-color: {Theme.BACKGROUND}; border-radius: 24px;")
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._avatar)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)
        self._name_label = QLabel(t("profile_header.no_profile"))
        self._name_label.setStyleSheet(
            f"color: {Theme.ACCENT}; font-weight: bold; font-size: 13px;"
        )
        self._meta_label = QLabel("")
        self._meta_label.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px;")
        text_col.addWidget(self._name_label)
        text_col.addWidget(self._meta_label)
        root.addLayout(text_col, 1)

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #

    def set_profile(
        self,
        profile: Profile | None,
        *,
        avatar_path: Path | None = None,
        meta_text: str = "",
    ) -> None:
        self._profile = profile

        if profile is None:
            self._name_label.setText(t("profile_header.no_profile"))
            self._meta_label.setText("")
            self._avatar.clear()
            return

        self._name_label.setText(profile.profile_name or profile.dir_name)
        self._meta_label.setText(meta_text)

        if avatar_path is not None and avatar_path.is_file():
            pix = QPixmap(str(avatar_path))
            if not pix.isNull():
                self._avatar.setPixmap(
                    pix.scaled(
                        self.AVATAR_SIZE,
                        self.AVATAR_SIZE,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                return
        self._avatar.clear()
