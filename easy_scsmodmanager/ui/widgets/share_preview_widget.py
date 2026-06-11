# easy_scsmodmanager/ui/widgets/share_preview_widget.py
# Renders a ShareDiff: installed / missing-workshop / missing-local.
#
# Missing workshop mods get a clickable Subscribe link (opens the Steam page
# in the browser); missing local mods can be copied as a name list so the
# user can hunt them down manually.
#
# TODO: add outdated section once the dialog surfaces it?

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget

from easy_scsmodmanager.services.mod_share import ShareDiff
from easy_scsmodmanager.utils.i18n import t


class SharePreviewWidget(QWidget):
    """Shows a diff: what's installed, what needs subscribing, what's local-only."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._diff: ShareDiff | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._body = QLabel("")
        self._body.setWordWrap(True)
        self._body.setTextFormat(Qt.TextFormat.RichText)
        self._body.setOpenExternalLinks(True)
        self._body.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        layout.addWidget(self._body)

        self._copy_button = QPushButton(t("mod_share.import.copy_names"))
        self._copy_button.clicked.connect(self._copy_missing_local)
        self._copy_button.hide()
        layout.addWidget(self._copy_button)

    # public api

    def set_diff(self, diff: ShareDiff) -> None:
        self._diff = diff
        self._body.setText(self._render(diff))
        self._copy_button.setVisible(bool(diff.missing_local))

    def has_missing(self) -> bool:
        # true if any mod cannot be found locally
        return self._diff is not None and bool(self._diff.missing_names())

    def summary_text(self) -> str:
        return self._body.text()

    def missing_local_names_for_clipboard(self) -> str:
        if self._diff is None:
            return ""
        return "\n".join(e.display_name or e.name for e in self._diff.missing_local)

    # rendering

    def _render(self, diff: ShareDiff) -> str:
        parts: list[str] = []

        if diff.found:
            hdr = t("mod_share.import.found_section", count=len(diff.found))
            parts.append(f"<b>{hdr}</b>")
            parts.extend(f"&#10003; {_esc(e.display_name or e.name)}" for e in diff.found)

        if diff.missing_workshop:
            hdr = t("mod_share.import.missing_workshop_section", count=len(diff.missing_workshop))
            parts.append(f"<b>{hdr}</b>")
            lbl = t("mod_share.import.subscribe_link")
            for e, url in diff.missing_workshop:
                nm = _esc(e.display_name or e.name)
                parts.append(f'&#9888; {nm} - <a href="{url}">{lbl}</a>')
            parts.append(f"<i>{_esc(t('mod_share.import.steam_hint'))}</i>")

        if diff.missing_local:
            hdr = t("mod_share.import.missing_local_section", count=len(diff.missing_local))
            parts.append(f"<b>{hdr}</b>")
            parts.extend(f"&#9888; {_esc(e.display_name or e.name)}" for e in diff.missing_local)
            parts.append(f"<i>{_esc(t('mod_share.import.local_hint'))}</i>")

        return "<br>".join(parts)

    def _copy_missing_local(self) -> None:
        cb = QApplication.clipboard()
        if cb is not None:
            cb.setText(self.missing_local_names_for_clipboard())


def _esc(text: str) -> str:
    # minimal HTML escaping - only what's needed for a QLabel RichText body
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
