"""Walks the filesystem to enumerate installed mods.

A *scan* yields one :class:`ScannedMod` per ``.scs`` file found in the
mod or workshop directory of a :class:`GameInstall`. Errors during the
read (corrupt zip, missing manifest, unsupported HashFS container, ...)
are recorded on the result rather than raised - the UI surfaces them
per-mod so one bad file never breaks the whole list.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from easy_scsmodmanager.core.game_paths import GameInstall
from easy_scsmodmanager.core.models.mod_manifest import ModManifest
from easy_scsmodmanager.integrations.scs.detector import ScsFormat, detect_format
from easy_scsmodmanager.integrations.scs.zip_reader import ZipScsReader
from easy_scsmodmanager.integrations.sii.parser import parse_sii

log = logging.getLogger(__name__)

MANIFEST_ENTRY = "manifest.sii"


@dataclass(frozen=True)
class ScannedMod:
    path: Path
    format: ScsFormat
    manifest: ModManifest | None
    error: str | None


def scan_game_install(install: GameInstall) -> list[ScannedMod]:
    """Scan both the local ``mod/`` directory and the workshop tree."""
    mods = scan_mod_directory(install.mod_dir)
    if install.workshop_dir is not None:
        mods.extend(scan_workshop_directory(install.workshop_dir))
    return mods


def scan_mod_directory(directory: Path) -> list[ScannedMod]:
    """Scan a flat directory for ``.scs`` files (no recursion)."""
    if not directory.is_dir():
        return []
    files = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix == ".scs")
    return [_scan_one(p) for p in files]


def scan_workshop_directory(directory: Path) -> list[ScannedMod]:
    """Scan a Steam workshop content tree (one subdir per published item)."""
    if not directory.is_dir():
        return []
    results: list[ScannedMod] = []
    for subdir in sorted(p for p in directory.iterdir() if p.is_dir()):
        for scs in sorted(p for p in subdir.iterdir() if p.is_file() and p.suffix == ".scs"):
            results.append(_scan_one(scs))
    return results


def _scan_one(scs_path: Path) -> ScannedMod:
    try:
        fmt = detect_format(scs_path)
    except OSError as exc:
        log.warning("could not read %s: %s", scs_path, exc)
        return ScannedMod(path=scs_path, format=ScsFormat.UNKNOWN, manifest=None, error=str(exc))

    if fmt == ScsFormat.ZIP:
        return _scan_zip(scs_path, fmt)
    if fmt in (ScsFormat.HASHFS_V1, ScsFormat.HASHFS_V2):
        return ScannedMod(
            path=scs_path,
            format=fmt,
            manifest=None,
            error="HashFS container reader not implemented yet",
        )
    return ScannedMod(
        path=scs_path,
        format=fmt,
        manifest=None,
        error="Unknown SCS container format",
    )


def _scan_zip(scs_path: Path, fmt: ScsFormat) -> ScannedMod:
    try:
        with ZipScsReader(scs_path) as reader:
            if not reader.has(MANIFEST_ENTRY):
                return ScannedMod(
                    path=scs_path,
                    format=fmt,
                    manifest=None,
                    error=f"missing {MANIFEST_ENTRY}",
                )
            text = reader.read_text(MANIFEST_ENTRY)
        units = parse_sii(text)
        manifest = ModManifest.from_sii_units(units)
        return ScannedMod(path=scs_path, format=fmt, manifest=manifest, error=None)
    except Exception as exc:
        log.warning("failed to read manifest from %s: %s", scs_path, exc)
        return ScannedMod(path=scs_path, format=fmt, manifest=None, error=str(exc))
