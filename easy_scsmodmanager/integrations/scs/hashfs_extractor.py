"""Wrap sk-zk/Extractor to read SCS HashFS archives (v1 + v2).

Why this exists: the HashFS v2 format SCS Software added in ETS2 1.50
uses a custom CityHash variant plus a metadata-driven layout with
TOBJ/DDS textures. The only mature open-source reader is the .NET
``sk-zk/Extractor`` (built on ``sk-zk/TruckLib.HashFs``). Porting it
fully to Python would be 1-2 weeks of work, and a Python port does
not exist on PyPI as of writing.

This module:

* finds the ``extractor`` (Linux/macOS) or ``extractor.exe`` (Windows)
  binary - env override + a list of likely paths,
* falls back to ``wine`` on non-Windows hosts when only the ``.exe``
  build is available,
* exposes ``extract_manifest_files()`` which extracts only
  ``manifest.sii`` + ``icon.{jpg,png}`` via the ``--partial`` flag
  (fast: ~80ms for a 65 MB mod).

The mod scanner uses this when a HashFS file is detected; for ZIP
containers our native ``ZipScsReader`` is faster and avoids the
external dependency.

Get the binary: ``gh release download -R sk-zk/Extractor`` or
download manually from https://github.com/sk-zk/Extractor/releases.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

ENV_BINARY_OVERRIDE = "ESCSMM_HASHFS_EXTRACTOR"
NATIVE_NAMES = ("extractor", "extractor.exe")
MANIFEST_NAME = "manifest.sii"
ICON_CANDIDATES = ("icon.jpg", "icon.png", "mod_icon.jpg", "mod_icon.png", "preview.jpg")
PARTIAL_DEFAULT = "/manifest.sii,/icon.jpg,/icon.png,/mod_icon.jpg,/mod_icon.png,/preview.jpg"


class HashFsExtractorNotAvailable(RuntimeError):
    """Raised when no Extractor binary (or wine for the .exe build) can be found."""


@dataclass(frozen=True)
class ExtractedManifest:
    manifest_text: str | None
    icon_bytes: bytes | None


def find_extractor_binary() -> Path | None:
    """Locate the sk-zk/Extractor binary.

    Resolution order:
    1. ``ESCSMM_HASHFS_EXTRACTOR`` env var (absolute path)
    2. ``~/Tools/ets2_sii/Extractor/extractor[.exe]``
    3. ``~/Tools/ets2_sii/extractor[.exe]``
    4. ``./extractor[.exe]`` next to the project root
    """
    override = os.environ.get(ENV_BINARY_OVERRIDE)
    if override:
        candidate = Path(override)
        if candidate.is_file():
            return candidate

    home = Path(os.environ.get("HOME", "~")).expanduser()
    search_dirs = [
        home / "Tools" / "ets2_sii" / "Extractor",
        home / "Tools" / "ets2_sii",
        Path.cwd(),
    ]
    for d in search_dirs:
        for name in NATIVE_NAMES:
            p = d / name
            if p.is_file():
                return p
    return None


def is_available() -> bool:
    """True iff a usable extractor binary (+ wine if needed) is on disk."""
    binary = find_extractor_binary()
    if binary is None:
        return False
    if binary.suffix.lower() == ".exe" and sys.platform != "win32":
        return shutil.which("wine") is not None
    return True


def extract_manifest_files(scs_path: Path) -> ExtractedManifest:
    """Extract manifest.sii + icon.{jpg,png} from a HashFS archive.

    Uses ``--partial`` so only the requested files come out - takes
    around 80ms even for a 65 MB mod.

    Raises :class:`HashFsExtractorNotAvailable` when the runtime is
    missing, or ``RuntimeError`` when the extractor exits non-zero
    without producing any output.
    """
    binary = find_extractor_binary()
    if binary is None or not is_available():
        raise HashFsExtractorNotAvailable(
            "sk-zk/Extractor binary not found. "
            "Download from https://github.com/sk-zk/Extractor/releases, "
            f"place under ~/Tools/ets2_sii/Extractor/, or set ${ENV_BINARY_OVERRIDE}."
        )

    with tempfile.TemporaryDirectory(prefix="escsmm_hashfs_") as tmp:
        dest = Path(tmp)
        cmd = _build_command(binary, scs_path, dest, partial=PARTIAL_DEFAULT)
        log.debug("running %s", cmd)
        completed = subprocess.run(  # noqa: S603 - controlled command list
            cmd,
            capture_output=True,
            text=True,
        )

        manifest_text: str | None = None
        manifest_path = dest / MANIFEST_NAME
        if manifest_path.is_file():
            manifest_text = manifest_path.read_text(encoding="utf-8", errors="replace")

        icon_bytes = _read_first_existing(dest, ICON_CANDIDATES)

        # Second pass: when manifest names a custom icon (rbgw.jpg,
        # tandempack.jpg, ...) re-run --partial for that specific file.
        if manifest_text is not None and icon_bytes is None:
            custom_icon = _icon_name_from_manifest(manifest_text)
            if custom_icon and custom_icon not in ICON_CANDIDATES:
                _run_partial(binary, scs_path, dest, "/" + custom_icon)
                icon_bytes = _read_first_existing(dest, (custom_icon,))

        if completed.returncode != 0 and manifest_text is None and icon_bytes is None:
            stderr = (completed.stderr or completed.stdout or "").strip()
            if _looks_like_hard_failure(stderr):
                raise RuntimeError(f"sk-zk/Extractor failed for {scs_path.name}: {stderr[:200]}")

        return ExtractedManifest(manifest_text=manifest_text, icon_bytes=icon_bytes)


def _run_partial(binary: Path, scs_path: Path, dest: Path, partial: str) -> None:
    cmd = _build_command(binary, scs_path, dest, partial=partial)
    try:
        subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        log.debug("second-pass partial extract failed for %s: %s", scs_path, exc)


def _read_first_existing(dest: Path, names: tuple[str, ...]) -> bytes | None:
    for name in names:
        candidate = dest / name
        if candidate.is_file():
            try:
                return candidate.read_bytes()
            except OSError:
                continue
    return None


_ICON_LINE = __import__("re").compile(r'^\s*icon\s*:\s*"([^"]+)"', __import__("re").MULTILINE)


def _icon_name_from_manifest(manifest_text: str) -> str | None:
    match = _ICON_LINE.search(manifest_text)
    if match is None:
        return None
    return match.group(1).strip()


def _build_command(
    binary: Path,
    scs_path: Path,
    dest: Path,
    *,
    partial: str = PARTIAL_DEFAULT,
) -> list[str]:
    args = [str(scs_path), "--dest", str(dest), "--partial", partial, "--quiet"]
    if binary.suffix.lower() == ".exe" and sys.platform != "win32":
        return ["wine", str(binary), *args]
    return [str(binary), *args]


_HARD_FAILURE_MARKERS = (
    "probably not a hashfs",
    "probably not a zip",
    "corrupt",
    "invalid header",
    "could not open",
    "unable to open",
    "permission denied",
)


def _looks_like_hard_failure(stderr: str) -> bool:
    # 'not found' from --partial misses is expected and harmless. We only
    # raise on real failures (corrupt archive, IO errors, ...).
    lower = stderr.lower()
    return any(marker in lower for marker in _HARD_FAILURE_MARKERS)
