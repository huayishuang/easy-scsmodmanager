"""Tests for the sk-zk/Extractor integration.

Real extraction tests need the binary present, so they are guarded
behind ``pytest.mark.integration`` and skip when the runtime is
missing. The pure-Python path-resolution + command-construction logic
is covered by unit tests that mock the subprocess call.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from easy_scsmodmanager.integrations.scs.hashfs_extractor import (
    HashFsExtractorNotAvailable,
    extract_manifest_files,
    find_extractor_binary,
    is_available,
)

REAL_HASHFS_FIXTURE = Path(
    "/home/heikesfootslave/.local/share/Euro Truck Simulator 2/mod/51ROEXcore.scs"
)


def _dest_from_cmd(cmd: list[str]) -> Path:
    return Path(cmd[cmd.index("--dest") + 1])


# ---------------------------------------------------------------------------
# find_extractor_binary
# ---------------------------------------------------------------------------


def test_find_extractor_binary_checks_env_var_first(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    candidate = tmp_path / "custom_extractor"
    candidate.write_bytes(b"fake")
    monkeypatch.setenv("ESCSMM_HASHFS_EXTRACTOR", str(candidate))

    assert find_extractor_binary() == candidate


def test_find_extractor_binary_falls_back_to_tools_extractor_subdir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    home = tmp_path / "home"
    tools_dir = home / "Tools" / "ets2_sii" / "Extractor"
    tools_dir.mkdir(parents=True)
    binary = tools_dir / "extractor"
    binary.write_bytes(b"fake")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("ESCSMM_HASHFS_EXTRACTOR", raising=False)

    assert find_extractor_binary() == binary


def test_find_extractor_binary_also_picks_up_exe_variant(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    home = tmp_path / "home"
    tools_dir = home / "Tools" / "ets2_sii"
    tools_dir.mkdir(parents=True)
    binary = tools_dir / "extractor.exe"
    binary.write_bytes(b"fake")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("ESCSMM_HASHFS_EXTRACTOR", raising=False)

    assert find_extractor_binary() == binary


def test_find_extractor_binary_returns_none_when_not_present(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "empty"))
    monkeypatch.delenv("ESCSMM_HASHFS_EXTRACTOR", raising=False)

    assert find_extractor_binary() is None


# ---------------------------------------------------------------------------
# is_available
# ---------------------------------------------------------------------------


def test_is_available_true_for_native_binary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    binary = tmp_path / "extractor"  # no .exe -> native, no wine needed
    binary.write_bytes(b"fake")
    monkeypatch.setenv("ESCSMM_HASHFS_EXTRACTOR", str(binary))

    assert is_available() is True


def test_is_available_requires_wine_for_exe_on_linux(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    binary = tmp_path / "extractor.exe"
    binary.write_bytes(b"fake")
    monkeypatch.setenv("ESCSMM_HASHFS_EXTRACTOR", str(binary))

    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/wine" if name == "wine" else None)
    assert is_available() is True

    monkeypatch.setattr(shutil, "which", lambda name: None)
    assert is_available() is False


def test_is_available_false_when_extractor_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "empty"))
    monkeypatch.delenv("ESCSMM_HASHFS_EXTRACTOR", raising=False)

    assert is_available() is False


# ---------------------------------------------------------------------------
# extract_manifest_files
# ---------------------------------------------------------------------------


def test_extract_manifest_files_raises_when_unavailable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "empty"))
    monkeypatch.delenv("ESCSMM_HASHFS_EXTRACTOR", raising=False)

    with pytest.raises(HashFsExtractorNotAvailable):
        extract_manifest_files(tmp_path / "mod.scs")


def test_extract_manifest_files_uses_partial_flag_and_returns_results(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    binary = tmp_path / "extractor"
    binary.write_bytes(b"fake")
    monkeypatch.setenv("ESCSMM_HASHFS_EXTRACTOR", str(binary))

    captured: dict = {}

    def fake_run(cmd: list[str], *args: object, **kwargs: object) -> subprocess.CompletedProcess:
        captured["cmd"] = cmd
        dest = _dest_from_cmd(cmd)
        (dest / "manifest.sii").write_text("SiiNunit\n{\nmod_package: .p\n{\n}\n}\n")
        (dest / "icon.jpg").write_bytes(b"\xff\xd8fakejpg")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = extract_manifest_files(tmp_path / "mod.scs")

    assert result.manifest_text is not None
    assert "SiiNunit" in result.manifest_text
    assert result.icon_bytes == b"\xff\xd8fakejpg"
    cmd = captured["cmd"]
    assert cmd[0] == str(binary)
    assert "--partial" in cmd
    assert "--quiet" in cmd
    partial_value = cmd[cmd.index("--partial") + 1]
    assert "/manifest.sii" in partial_value


def test_extract_manifest_files_prepends_wine_for_exe_binary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    binary = tmp_path / "extractor.exe"
    binary.write_bytes(b"fake")
    monkeypatch.setenv("ESCSMM_HASHFS_EXTRACTOR", str(binary))
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/wine")

    captured: dict = {}

    def fake_run(cmd: list[str], *args: object, **kwargs: object) -> subprocess.CompletedProcess:
        captured["cmd"] = cmd
        dest = _dest_from_cmd(cmd)
        (dest / "manifest.sii").write_text("SiiNunit\n{\nx: .y\n{\n}\n}\n")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    extract_manifest_files(tmp_path / "mod.scs")

    assert captured["cmd"][0] == "wine"
    assert captured["cmd"][1] == str(binary)


def test_extract_manifest_files_returns_empty_when_no_manifest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    binary = tmp_path / "extractor"
    binary.write_bytes(b"fake")
    monkeypatch.setenv("ESCSMM_HASHFS_EXTRACTOR", str(binary))

    def fake_run(cmd: list[str], *args: object, **kwargs: object) -> subprocess.CompletedProcess:
        # Empty destination - the partial paths were not present in the archive.
        return subprocess.CompletedProcess(cmd, 1, "", "1 not found")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = extract_manifest_files(tmp_path / "mod.scs")

    assert result.manifest_text is None
    assert result.icon_bytes is None


def test_extract_manifest_files_raises_on_hard_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    binary = tmp_path / "extractor"
    binary.write_bytes(b"fake")
    monkeypatch.setenv("ESCSMM_HASHFS_EXTRACTOR", str(binary))

    def fake_run(cmd: list[str], *args: object, **kwargs: object) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(
            cmd, 1, "", "Probably not a HashFS file (corrupt header)"
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="HashFS"):
        extract_manifest_files(tmp_path / "mod.scs")


def test_extract_manifest_files_returns_manifest_even_when_icon_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # extractor returns non-zero whenever a partial path is not in the archive.
    # Common case: mod with manifest.sii but no icon. Still a success for us.
    binary = tmp_path / "extractor"
    binary.write_bytes(b"fake")
    monkeypatch.setenv("ESCSMM_HASHFS_EXTRACTOR", str(binary))

    def fake_run(cmd: list[str], *args: object, **kwargs: object) -> subprocess.CompletedProcess:
        dest = _dest_from_cmd(cmd)
        (dest / "manifest.sii").write_text("SiiNunit\n{\nmod_package: .p\n{\n}\n}\n")
        return subprocess.CompletedProcess(
            cmd, 1, "", "Path /icon.jpg was not found\n1 extracted, 1 not found"
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = extract_manifest_files(tmp_path / "mod.scs")

    assert result.manifest_text is not None
    assert result.icon_bytes is None


# ---------------------------------------------------------------------------
# Integration test - only runs when the real extractor + fixture are present
# ---------------------------------------------------------------------------


@pytest.fixture
def real_hashfs_fixture() -> Iterator[Path]:
    if not is_available():
        pytest.skip("sk-zk/Extractor binary not available")
    if not REAL_HASHFS_FIXTURE.is_file():
        pytest.skip(f"real fixture not present: {REAL_HASHFS_FIXTURE}")
    yield REAL_HASHFS_FIXTURE


@pytest.mark.integration
def test_extract_real_hashfs_archive_reads_root_files(real_hashfs_fixture: Path) -> None:
    result = extract_manifest_files(real_hashfs_fixture)

    # 51ROEXcore has icon.jpg at the root, no manifest.sii.
    assert result.icon_bytes is not None
    assert result.icon_bytes[:2] == b"\xff\xd8"  # JPEG magic
