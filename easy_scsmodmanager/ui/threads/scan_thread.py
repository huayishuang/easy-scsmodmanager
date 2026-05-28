"""QThread wrapper around scan_game_install.

The UI cannot block on the cold-scan (12 seconds), so the heavy lifting
runs on a worker thread and signals back to the main thread. The
SQLite cache is opened with check_same_thread=False so it can be
passed across the thread boundary.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from easy_scsmodmanager.core.db.scan_cache import ScanCache
from easy_scsmodmanager.core.game_paths import GameInstall
from easy_scsmodmanager.services.mod_scanner import ScannedMod, scan_game_install

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScanResult:
    install: GameInstall
    mods: list[ScannedMod]
    elapsed_seconds: float


class ScanWorker(QObject):
    """Lives on the worker thread, does the scan, emits the result."""

    finished = pyqtSignal(object)  # ScanResult
    failed = pyqtSignal(str)

    def __init__(self, install: GameInstall, cache: ScanCache | None) -> None:
        super().__init__()
        self._install = install
        self._cache = cache

    def run(self) -> None:
        start = time.monotonic()
        try:
            mods = scan_game_install(self._install, cache=self._cache)
        except Exception as exc:  # pragma: no cover - defensive only
            log.exception("scan failed")
            self.failed.emit(str(exc))
            return
        elapsed = time.monotonic() - start
        self.finished.emit(ScanResult(install=self._install, mods=mods, elapsed_seconds=elapsed))


class ScanThread(QThread):
    """Thin QThread that owns a single ScanWorker.

    Usage::

        thread = ScanThread(install, cache)
        thread.finished_with_result.connect(self._on_done)
        thread.start()
    """

    finished_with_result = pyqtSignal(object)  # ScanResult
    failed = pyqtSignal(str)

    def __init__(self, install: GameInstall, cache: ScanCache | None) -> None:
        super().__init__()
        self._worker = ScanWorker(install, cache)
        self._worker.finished.connect(self.finished_with_result.emit)
        self._worker.failed.connect(self.failed.emit)

    def run(self) -> None:  # noqa: D401
        self._worker.run()
