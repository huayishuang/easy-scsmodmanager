"""Drives profile backup + restore from the profile header buttons.

Pulled out of MainWindow. Holds no state itself: it asks the window for the
current profile path and display name through callables, and tells it to
reload after a restore. Restore must work even when the profile no longer
parses - that is exactly when a user needs it.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from PyQt6.QtWidgets import QWidget

from easy_scsmodmanager.services.profile_backup import (
    create_backup,
    list_backups,
    restore_backup,
)
from easy_scsmodmanager.ui.dialogs.restore_backup_dialog import RestoreBackupDialog
from easy_scsmodmanager.utils.i18n import t

log = logging.getLogger(__name__)


class ProfileBackupController:
    def __init__(
        self,
        *,
        parent: QWidget,
        current_path: Callable[[], Path | None],
        restore_name: Callable[[], str],
        show_status: Callable[[str, int], None],
        on_restored: Callable[[], None],
    ) -> None:
        self._parent = parent
        self._current_path = current_path
        self._restore_name = restore_name
        self._show_status = show_status
        self._on_restored = on_restored

    def backup(self) -> None:
        path = self._current_path()
        if path is None:
            return
        try:
            entry = create_backup(path)
        except Exception as exc:
            log.warning("backup failed: %s", exc)
            self._show_status(t("status_bar.backup_failed", reason=str(exc)), 5000)
            return
        self._show_status(t("status_bar.backup_created", label=entry.label), 5000)

    def restore(self) -> None:
        path = self._current_path()
        if path is None:
            return
        backups = list_backups(path)
        if not backups:
            self._show_status(t("status_bar.no_backups"), 5000)
            return
        dialog = RestoreBackupDialog(self._restore_name(), backups, parent=self._parent)
        if dialog.exec() != dialog.DialogCode.Accepted or dialog.selected is None:
            return
        try:
            restore_backup(dialog.selected, path)
        except Exception as exc:
            log.warning("restore failed: %s", exc)
            self._show_status(t("status_bar.restore_failed", reason=str(exc)), 5000)
            return
        self._on_restored()
        self._show_status(t("status_bar.restore_done", label=dialog.selected.label), 5000)
