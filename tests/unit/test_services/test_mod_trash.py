from __future__ import annotations

from pathlib import Path

from easy_scsmodmanager.integrations.scs.detector import ScsFormat
from easy_scsmodmanager.services import mod_trash
from easy_scsmodmanager.services.mod_scanner import ScannedMod
from easy_scsmodmanager.services.profile_reader import ActiveMod, Profile


def _mod(path: Path) -> ScannedMod:
    return ScannedMod(path=path, format=ScsFormat.ZIP, manifest=None, error=None)


def _profile(name: str, *active: str) -> Profile:
    return Profile(
        dir_name="aa",
        profile_name=name,
        active_mods=tuple(ActiveMod.parse(a) for a in active),
    )


def test_move_path_to_trash_returns_bool(tmp_path: Path) -> None:
    f = tmp_path / "mod_a.scs"
    f.write_text("x")
    result = mod_trash.move_path_to_trash(f)
    assert isinstance(result, bool)


def test_move_directory_to_trash_returns_bool(tmp_path: Path) -> None:
    d = tmp_path / "unpacked_mod"
    d.mkdir()
    (d / "manifest.sii").write_text("x")
    assert isinstance(mod_trash.move_path_to_trash(d), bool)


def test_active_profiles_for_stem_match() -> None:
    mod = _mod(Path("/mods/realistic_physics.scs"))
    profiles = [_profile("Heike Logistics", "realistic_physics|Realistic Physics")]
    assert mod_trash.active_profiles_for(mod, profiles) == ["Heike Logistics"]


def test_active_profiles_for_display_name_match() -> None:
    from easy_scsmodmanager.core.models.mod_manifest import ModManifest

    mod = ScannedMod(
        path=Path("/mods/abc.scs"),
        format=ScsFormat.ZIP,
        manifest=ModManifest(display_name="Better Flares", author="x"),
        error=None,
    )
    profiles = [_profile("Heike", "somethingelse|Better Flares")]
    assert mod_trash.active_profiles_for(mod, profiles) == ["Heike"]


def test_active_profiles_for_no_match() -> None:
    mod = _mod(Path("/mods/realistic_physics.scs"))
    profiles = [_profile("Heike", "other_mod|Other")]
    assert mod_trash.active_profiles_for(mod, profiles) == []


def test_active_profiles_for_multiple_profiles() -> None:
    mod = _mod(Path("/mods/sound_fixes.scs"))
    profiles = [
        _profile("Heike", "sound_fixes|Sound Fixes"),
        _profile("Westkueste", "sound_fixes|Sound Fixes"),
        _profile("Leer", "nope|Nope"),
    ]
    assert mod_trash.active_profiles_for(mod, profiles) == ["Heike", "Westkueste"]


def test_active_profiles_for_directory_slot_mod(tmp_path: Path) -> None:
    d = tmp_path / "my_unpacked_mod"
    d.mkdir()
    mod = _mod(d)
    profiles = [_profile("Heike", "my_unpacked_mod|My Mod")]
    assert mod_trash.active_profiles_for(mod, profiles) == ["Heike"]


def test_module_has_no_hard_delete() -> None:
    # never fall back to os.remove/unlink - trash or nothing
    src = Path(mod_trash.__file__).read_text()
    assert "os.remove" not in src
    assert ".unlink(" not in src
    assert "shutil.rmtree" not in src
