from __future__ import annotations

from pathlib import Path

from pytestqt.qtbot import QtBot

from easy_scsmodmanager.core.models.mod_manifest import ModManifest
from easy_scsmodmanager.integrations.scs.detector import ScsFormat
from easy_scsmodmanager.services.mod_scanner import ScannedMod
from easy_scsmodmanager.ui.widgets.mod_card_grid import ModCardGrid


def _mod(name: str, path: str = "/tmp/m.scs") -> ScannedMod:
    return ScannedMod(
        path=Path(path),
        format=ScsFormat.ZIP,
        manifest=ModManifest(display_name=name),
        error=None,
    )


def test_set_mods_creates_one_card_per_mod(qtbot: QtBot) -> None:
    grid = ModCardGrid()
    qtbot.addWidget(grid)

    grid.set_mods([_mod("A"), _mod("B"), _mod("C")])

    assert len(grid.cards()) == 3


def test_set_mods_replaces_previous_cards(qtbot: QtBot) -> None:
    grid = ModCardGrid()
    qtbot.addWidget(grid)

    grid.set_mods([_mod("Old1"), _mod("Old2")])
    grid.set_mods([_mod("New")])

    assert len(grid.cards()) == 1
    assert grid.cards()[0].mod.manifest.display_name == "New"


def test_active_names_set_marks_matching_cards_active(qtbot: QtBot) -> None:
    grid = ModCardGrid()
    qtbot.addWidget(grid)

    grid.set_mods(
        [_mod("Live", path="/tmp/live.scs"), _mod("Off", path="/tmp/off.scs")],
        active_names={"live"},
    )

    cards = grid.cards()
    assert cards[0].is_active is True
    assert cards[1].is_active is False


def test_icon_for_callable_is_invoked_per_card(qtbot: QtBot) -> None:
    grid = ModCardGrid()
    qtbot.addWidget(grid)

    calls: list[ScannedMod] = []

    def icon_for(mod: ScannedMod) -> bytes | None:
        calls.append(mod)
        return None

    grid.set_mods([_mod("A"), _mod("B")], icon_for=icon_for)

    assert len(calls) == 2


def test_selecting_a_card_emits_selection_changed(qtbot: QtBot) -> None:
    grid = ModCardGrid()
    qtbot.addWidget(grid)
    grid.set_mods([_mod("A"), _mod("B")])

    with qtbot.waitSignal(grid.selection_changed, timeout=500) as sig:
        grid._on_card_clicked(0)

    assert len(sig.args[0]) == 1
    assert sig.args[0][0].manifest.display_name == "A"
    assert grid.cards()[0].is_selected is True


def test_selecting_another_card_clears_previous(qtbot: QtBot) -> None:
    grid = ModCardGrid()
    qtbot.addWidget(grid)
    grid.set_mods([_mod("A"), _mod("B")])

    grid._on_card_clicked(0)
    grid._on_card_clicked(1)

    assert grid.cards()[0].is_selected is False
    assert grid.cards()[1].is_selected is True


def test_clear_selection_drops_all_selected(qtbot: QtBot) -> None:
    grid = ModCardGrid()
    qtbot.addWidget(grid)
    grid.set_mods([_mod("A")])
    grid._on_card_clicked(0)

    with qtbot.waitSignal(grid.selection_changed, timeout=500) as sig:
        grid.clear_selection()

    assert sig.args[0] == []
    assert grid.cards()[0].is_selected is False


def test_double_click_emits_card_activated_with_mod(qtbot: QtBot) -> None:
    grid = ModCardGrid()
    qtbot.addWidget(grid)
    grid.set_mods([_mod("Demo")])

    with qtbot.waitSignal(grid.card_activated, timeout=500) as sig:
        grid._on_card_activated(0)

    assert sig.args[0].manifest.display_name == "Demo"
