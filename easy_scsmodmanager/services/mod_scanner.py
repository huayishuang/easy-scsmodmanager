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
from typing import TYPE_CHECKING

from easy_scsmodmanager.core.game_paths import GameInstall
from easy_scsmodmanager.core.models.mod_manifest import ModManifest
from easy_scsmodmanager.integrations.scs.detector import ScsFormat, detect_format
from easy_scsmodmanager.integrations.scs.hashfs_extractor import (
    HashFsExtractorNotAvailable,
    extract_manifest_files,
)
from easy_scsmodmanager.integrations.scs.hashfs_extractor import (
    is_available as hashfs_extractor_available,
)
from easy_scsmodmanager.integrations.scs.zip_reader import ZipScsReader
from easy_scsmodmanager.integrations.sii.parser import parse_sii

if TYPE_CHECKING:
    from easy_scsmodmanager.core.db.scan_cache import ScanCache

log = logging.getLogger(__name__)

MANIFEST_ENTRY = "manifest.sii"


@dataclass(frozen=True)
class ScannedMod:
    path: Path
    format: ScsFormat
    manifest: ModManifest | None
    error: str | None


def scan_game_install(
    install: GameInstall,
    cache: ScanCache | None = None,
) -> list[ScannedMod]:
    """Scan both the local ``mod/`` directory and the workshop tree."""
    mods = scan_mod_directory(install.mod_dir, cache=cache)
    if install.workshop_dir is not None:
        mods.extend(scan_workshop_directory(install.workshop_dir, cache=cache))
    return mods


def scan_mod_directory(directory: Path, cache: ScanCache | None = None) -> list[ScannedMod]:
    """Scan a flat directory for ``.scs`` files (no recursion)."""
    if not directory.is_dir():
        return []
    files = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix == ".scs")
    return [_scan_one(p, cache=cache) for p in files]


def scan_workshop_directory(directory: Path, cache: ScanCache | None = None) -> list[ScannedMod]:
    """Scan a Steam workshop content tree (one subdir per published item)."""
    if not directory.is_dir():
        return []
    results: list[ScannedMod] = []
    for subdir in sorted(p for p in directory.iterdir() if p.is_dir()):
        for scs in sorted(p for p in subdir.iterdir() if p.is_file() and p.suffix == ".scs"):
            results.append(_scan_one(scs, cache=cache))
    return results


def _scan_one(scs_path: Path, cache: ScanCache | None = None) -> ScannedMod:
    if cache is not None:
        cached = cache.get(scs_path)
        if cached is not None:
            return cached.mod

    try:
        fmt = detect_format(scs_path)
    except OSError as exc:
        log.debug("could not read %s: %s", scs_path, exc)
        result = ScannedMod(path=scs_path, format=ScsFormat.UNKNOWN, manifest=None, error=str(exc))
        _store_if_caching(cache, scs_path, result)
        return result

    if fmt == ScsFormat.ZIP:
        result, icon = _scan_zip_with_icon(scs_path, fmt)
    elif fmt in (ScsFormat.HASHFS_V1, ScsFormat.HASHFS_V2):
        result, icon = _scan_hashfs_with_icon(scs_path, fmt)
    else:
        result = ScannedMod(
            path=scs_path,
            format=fmt,
            manifest=None,
            error="Unknown SCS container format",
        )
        icon = None

    _store_if_caching(cache, scs_path, result, icon)
    return result


def _store_if_caching(
    cache: ScanCache | None,
    scs_path: Path,
    mod: ScannedMod,
    icon_bytes: bytes | None = None,
) -> None:
    if cache is None:
        return
    try:
        cache.put(scs_path, mod, icon_bytes=icon_bytes)
    except Exception as exc:
        log.debug("cache write failed for %s: %s", scs_path, exc)


def _scan_hashfs_with_icon(scs_path: Path, fmt: ScsFormat) -> tuple[ScannedMod, bytes | None]:
    if not hashfs_extractor_available():
        mod = ScannedMod(
            path=scs_path,
            format=fmt,
            manifest=None,
            error="HashFS reader requires sk-zk/Extractor (not available)",
        )
        return mod, None
    try:
        extracted = extract_manifest_files(scs_path)
    except HashFsExtractorNotAvailable as exc:
        return ScannedMod(path=scs_path, format=fmt, manifest=None, error=str(exc)), None
    except Exception as exc:
        log.debug("hashfs extract failed for %s: %s", scs_path, exc)
        return ScannedMod(path=scs_path, format=fmt, manifest=None, error=str(exc)), None

    if extracted.manifest_text is None:
        return (
            ScannedMod(path=scs_path, format=fmt, manifest=None, error=f"missing {MANIFEST_ENTRY}"),
            extracted.icon_bytes,
        )
    try:
        units = parse_sii(extracted.manifest_text)
        manifest = ModManifest.from_sii_units(units)
    except Exception as exc:
        log.debug("hashfs manifest parse failed for %s: %s", scs_path, exc)
        return (
            ScannedMod(path=scs_path, format=fmt, manifest=None, error=str(exc)),
            extracted.icon_bytes,
        )
    return (
        ScannedMod(path=scs_path, format=fmt, manifest=manifest, error=None),
        extracted.icon_bytes,
    )


def _scan_zip_with_icon(scs_path: Path, fmt: ScsFormat) -> tuple[ScannedMod, bytes | None]:
    try:
        with ZipScsReader(scs_path) as reader:
            if not reader.has(MANIFEST_ENTRY):
                return (
                    ScannedMod(
                        path=scs_path, format=fmt, manifest=None, error=f"missing {MANIFEST_ENTRY}"
                    ),
                    None,
                )
            text = reader.read_text(MANIFEST_ENTRY)
            icon_bytes: bytes | None = None
            for icon_name in ("icon.jpg", "icon.png"):
                if reader.has(icon_name):
                    icon_bytes = reader.read_bytes(icon_name)
                    break
        units = parse_sii(text)
        manifest = ModManifest.from_sii_units(units)
        return (
            ScannedMod(path=scs_path, format=fmt, manifest=manifest, error=None),
            icon_bytes,
        )
    except Exception as exc:
        log.debug("failed to read manifest from %s: %s", scs_path, exc)
        return ScannedMod(path=scs_path, format=fmt, manifest=None, error=str(exc)), None
