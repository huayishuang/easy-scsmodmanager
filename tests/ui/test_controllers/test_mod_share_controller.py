"""Controller logic: payload building, installed map via matcher, apply."""

import pytest

pytest.importorskip("pytestqt")

from pathlib import Path  # noqa: E402

from easy_scsmodmanager.core.game_paths import Game  # noqa: E402
from easy_scsmodmanager.services.mod_share import (  # noqa: E402
    ShareEntry,
    ShareList,
    parse,
    serialize,
)
from easy_scsmodmanager.services.profile_reader import ActiveMod, read_profile  # noqa: E402
from easy_scsmodmanager.ui.controllers.mod_share_controller import (  # noqa: E402
    ModShareController,
)

PROFILE_TEXT = (
    "SiiNunit\n"
    "{\n"
    "user_profile : _nameless.1ad.dead {\n"
    ' profile_name: "Receiver"\n'
    " active_mods: 1\n"
    ' active_mods[0]: "old_mod|Old"\n'
    "}\n"
    "}\n"
)


class _Manifest:
    def __init__(self, version: str) -> None:
        self.package_version = version
        self.display_name = ""


class _Scanned:
    def __init__(self, version: str = "") -> None:
        self.manifest = _Manifest(version) if version else None


class _Matcher:
    """Knows exactly one installed mod: ``have`` with version 1.0."""

    def lookup(self, active: ActiveMod):
        return _Scanned("1.0") if active.name == "have" else None


def _controller(
    tmp_path: Path,
) -> tuple[ModShareController, Path, list[str], list[tuple[str, str]]]:
    profile_path = tmp_path / "profile.sii"
    profile_path.write_text(PROFILE_TEXT, encoding="utf-8")
    statuses: list[str] = []
    pins: list[tuple[str, str]] = []
    controller = ModShareController(
        parent=None,
        current_game=lambda: Game.ETS2,
        current_profile=lambda: read_profile(profile_path),
        profile_sii_path=lambda: profile_path,
        matcher=lambda: _Matcher(),
        local_versions=lambda: {"old_mod": "0.9"},
        group_token_for=lambda mod: "trucks" if mod.name == "have" else "",
        apply_group_pin=lambda mod, token: pins.append((mod.name, token)),
        show_status=statuses.append,
        request_rescan=lambda: False,
        reload_profile=lambda: None,
    )
    return controller, profile_path, statuses, pins


def test_build_share_carries_groups_and_versions(tmp_path: Path, qtbot) -> None:
    controller, _, _, _ = _controller(tmp_path)
    share = controller._build_share()
    assert share is not None
    assert share.game is Game.ETS2
    assert share.profile_name == "Receiver"
    assert share.entries[0].name == "old_mod"
    assert share.entries[0].package_version == "0.9"


def test_installed_map_uses_matcher(tmp_path: Path, qtbot) -> None:
    controller, _, _, _ = _controller(tmp_path)
    share = ShareList(
        game=Game.ETS2,
        profile_name="Sender",
        entries=(ShareEntry(name="have"), ShareEntry(name="missing")),
    )
    installed = controller._installed_map(share)
    assert installed == {"have": "1.0", "missing": None}


def test_apply_writes_profile_and_pins_groups(tmp_path: Path, qtbot) -> None:
    controller, profile_path, statuses, pins = _controller(tmp_path)
    share = ShareList(
        game=Game.ETS2,
        profile_name="Sender",
        entries=(
            ShareEntry(name="have", display_name="Have", group="trucks"),
            ShareEntry(name="missing", display_name="Missing"),
        ),
    )
    controller._apply(share, include_missing=True)
    written = read_profile(profile_path)
    assert [m.name for m in written.active_mods] == ["have", "missing"]
    assert ("have", "trucks") in pins
    assert statuses


def test_apply_can_skip_missing(tmp_path: Path, qtbot) -> None:
    controller, profile_path, _, _ = _controller(tmp_path)
    share = ShareList(
        game=Game.ETS2,
        profile_name="Sender",
        entries=(ShareEntry(name="have"), ShareEntry(name="missing")),
    )
    controller._apply(share, include_missing=False)
    written = read_profile(profile_path)
    assert [m.name for m in written.active_mods] == ["have"]


def test_share_roundtrip_through_build(tmp_path: Path, qtbot) -> None:
    controller, _, _, _ = _controller(tmp_path)
    share = controller._build_share()
    assert share is not None
    assert parse(serialize(share)) == share


def test_stale_fetch_result_is_ignored(tmp_path: Path, qtbot) -> None:
    controller, _, _, _ = _controller(tmp_path)
    controller._open_import("code")

    class _StaleThread:
        code = "OLDOLD"

    controller._fetch_thread = None  # no current lookup anymore
    controller._on_payload({"format": "x"}, source_thread=_StaleThread())
    # nothing presented: dialog still has no share
    assert controller._import_dialog.current_share() is None
