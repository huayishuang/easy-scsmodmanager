from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pytestqt")

from easy_scsmodmanager.core.game_paths import Game, GameInstall, InstallKind  # noqa: E402
from easy_scsmodmanager.ui.threads.scan_thread import ScanWorker  # noqa: E402


def _install(tmp_path: Path) -> GameInstall:
    return GameInstall(
        game=Game.ETS2,
        kind=InstallKind.LINUX_NATIVE,
        documents_dir=tmp_path,
        workshop_dir=None,
    )


def test_worker_tick_emits_running_count(qtbot, tmp_path) -> None:
    worker = ScanWorker(_install(tmp_path), cache=None)
    seen: list[tuple[int, str]] = []
    worker.progress.connect(lambda n, name: seen.append((n, name)))

    worker._tick(Path("/tmp/first.scs"))
    worker._tick(Path("/tmp/second.scs"))

    assert seen == [(1, "first.scs"), (2, "second.scs")]
