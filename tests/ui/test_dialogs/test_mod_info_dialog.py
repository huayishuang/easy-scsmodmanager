from __future__ import annotations

from pathlib import Path

from pytestqt.qtbot import QtBot

from easy_scsmodmanager.core.models.mod_manifest import ModManifest
from easy_scsmodmanager.integrations.scs.detector import ScsFormat
from easy_scsmodmanager.services.mod_scanner import ScannedMod
from easy_scsmodmanager.ui.dialogs.mod_info_dialog import ModInfoDialog


def _scanned(
    *,
    manifest: ModManifest | None = None,
    description: str | None = None,
    path: Path = Path("/tmp/mod.scs"),
) -> ScannedMod:
    return ScannedMod(
        path=path, format=ScsFormat.ZIP, manifest=manifest, error=None, description=description
    )


def test_shows_description_text(qtbot: QtBot) -> None:
    mod = _scanned(
        manifest=ModManifest(display_name="Map X", author="Mapper"),
        description="A big map with new roads.",
    )
    dlg = ModInfoDialog(mod)
    qtbot.addWidget(dlg)

    assert "A big map with new roads." in dlg.description_text()


def test_shows_fallback_when_no_description(qtbot: QtBot) -> None:
    mod = _scanned(manifest=ModManifest(display_name="Map X"), description=None)
    dlg = ModInfoDialog(mod)
    qtbot.addWidget(dlg)

    assert dlg.description_text().strip() != ""


def test_header_uses_display_name(qtbot: QtBot) -> None:
    mod = _scanned(manifest=ModManifest(display_name="My Cool Mod", author="Me"))
    dlg = ModInfoDialog(mod)
    qtbot.addWidget(dlg)

    assert "My Cool Mod" in dlg._header.text()


def test_falls_back_to_filename_without_manifest(qtbot: QtBot) -> None:
    mod = _scanned(manifest=None, path=Path("/tmp/some_mod.scs"))
    dlg = ModInfoDialog(mod)
    qtbot.addWidget(dlg)

    assert "some_mod" in dlg._header.text()
