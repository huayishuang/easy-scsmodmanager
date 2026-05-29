from __future__ import annotations

from pathlib import Path

import pytest

from easy_scsmodmanager.integrations.sii.crypto import decrypt_scsc, encrypt_scsc, is_scsc
from easy_scsmodmanager.services.profile_reader import ActiveMod, read_profile
from easy_scsmodmanager.services.profile_writer import replace_active_mods, write_active_mods

PROFILE_TEMPLATE = (
    "SiiNunit\n"
    "{\n"
    "user_profile : _nameless.profile {\n"
    ' profile_name: "Test"\n'
    " active_mods: 2\n"
    ' active_mods[0]: "alpha|Alpha Mod"\n'
    ' active_mods[1]: "beta|Beta Mod"\n'
    " some_other_key: 42\n"
    "}\n"
    "}\n"
)


def test_replace_active_mods_rewrites_count_and_entries() -> None:
    mods = [ActiveMod("z", "Zulu"), ActiveMod("y", "Yankee"), ActiveMod("x", "Xray")]

    out = replace_active_mods(PROFILE_TEMPLATE, mods)

    assert " active_mods: 3" in out
    assert ' active_mods[0]: "z|Zulu"' in out
    assert ' active_mods[2]: "x|Xray"' in out
    assert "alpha|Alpha Mod" not in out  # old entries gone


def test_replace_active_mods_preserves_other_lines() -> None:
    out = replace_active_mods(PROFILE_TEMPLATE, [ActiveMod("only", "Only")])

    assert ' profile_name: "Test"' in out
    assert " some_other_key: 42" in out


def test_replace_active_mods_can_empty_the_list() -> None:
    out = replace_active_mods(PROFILE_TEMPLATE, [])

    assert " active_mods: 0" in out
    assert "active_mods[" not in out


def test_replace_active_mods_round_trips_through_reader(tmp_path: Path) -> None:
    mods = [ActiveMod("first", "First"), ActiveMod("second", "Second")]
    out = replace_active_mods(PROFILE_TEMPLATE, mods)
    sii = tmp_path / "profiles" / "deadbeef" / "profile.sii"
    sii.parent.mkdir(parents=True)
    sii.write_text(out, encoding="utf-8")

    profile = read_profile(sii)

    assert [m.name for m in profile.active_mods] == ["first", "second"]
    assert profile.active_mods[0].display_name == "First"


def test_replace_raises_when_no_active_mods_line() -> None:
    with pytest.raises(ValueError):
        replace_active_mods("SiiNunit\n{\nuser_profile : x {\n}\n}\n", [ActiveMod("a", "A")])


def test_write_active_mods_to_plaintext_profile(tmp_path: Path) -> None:
    sii = tmp_path / "profiles" / "abc" / "profile.sii"
    sii.parent.mkdir(parents=True)
    sii.write_text(PROFILE_TEMPLATE, encoding="utf-8")

    write_active_mods(sii, [ActiveMod("new1", "New One"), ActiveMod("new2", "New Two")])

    assert not is_scsc(sii.read_bytes())  # stays plaintext
    profile = read_profile(sii)
    assert [m.name for m in profile.active_mods] == ["new1", "new2"]


def test_write_active_mods_keeps_scsc_encryption(tmp_path: Path) -> None:
    sii = tmp_path / "profiles" / "abc" / "profile.sii"
    sii.parent.mkdir(parents=True)
    sii.write_bytes(encrypt_scsc(PROFILE_TEMPLATE.encode("utf-8")))

    write_active_mods(sii, [ActiveMod("enc", "Encrypted Mod")])

    raw = sii.read_bytes()
    assert is_scsc(raw)  # still encrypted
    assert b"enc|Encrypted Mod" in decrypt_scsc(raw)
    profile = read_profile(sii)
    assert [m.name for m in profile.active_mods] == ["enc"]


def test_save_active_mods_backs_up_then_writes(tmp_path: Path) -> None:
    from easy_scsmodmanager.services.profile_writer import save_active_mods

    sii = tmp_path / "profiles" / "abc" / "profile.sii"
    sii.parent.mkdir(parents=True)
    sii.write_text(PROFILE_TEMPLATE, encoding="utf-8")
    backup_root = tmp_path / "backups"

    entry = save_active_mods(sii, [ActiveMod("new", "New")], backup=True, backup_root=backup_root)

    assert [m.name for m in read_profile(sii).active_mods] == ["new"]
    assert entry is not None
    assert entry.path.is_file()


def test_save_active_mods_can_skip_backup(tmp_path: Path) -> None:
    from easy_scsmodmanager.services.profile_writer import save_active_mods

    sii = tmp_path / "profiles" / "abc" / "profile.sii"
    sii.parent.mkdir(parents=True)
    sii.write_text(PROFILE_TEMPLATE, encoding="utf-8")
    backup_root = tmp_path / "backups"

    entry = save_active_mods(
        sii, [ActiveMod("solo", "Solo")], backup=False, backup_root=backup_root
    )

    assert entry is None
    assert not backup_root.exists()
    assert [m.name for m in read_profile(sii).active_mods] == ["solo"]
