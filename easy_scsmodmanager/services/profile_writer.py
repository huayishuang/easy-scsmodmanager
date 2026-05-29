"""Writes the active mod list back into a profile.sii.

The active list lives in the ``user_profile`` unit as an indexed array::

     active_mods: 2
     active_mods[0]: "name|Display Name"
     active_mods[1]: "other|Other Name"

Index 0 is the bottom of the in-game load order, the highest index the top.
We replace just that block in the decrypted text and re-encrypt if the
original was ScsC, leaving every other byte of the profile untouched. The
write is atomic (temp file + rename) so a crash can't leave a half-written
profile.sii.
"""

from __future__ import annotations

import os
import re
import tempfile
from collections.abc import Sequence
from pathlib import Path

from easy_scsmodmanager.integrations.sii.crypto import decrypt_scsc, is_scsc
from easy_scsmodmanager.integrations.sii.parser import parse_sii
from easy_scsmodmanager.services.profile_backup import BackupEntry, create_backup
from easy_scsmodmanager.services.profile_reader import ActiveMod

_COUNT_RE = re.compile(r"^(\s*)active_mods\s*:\s*\d+\s*$")
_ENTRY_RE = re.compile(r"^\s*active_mods\s*\[\d+\]\s*:")
# captures the raw inner string, escape sequences left intact
_INNER_RE = re.compile(r'active_mods\s*\[\d+\]\s*:\s*"((?:\\.|[^"\\])*)"')


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _original_inner_by_name(text: str) -> dict[str, str]:
    # map active name -> the exact stored string, so reordering existing
    # entries never reformats (and never breaks) their escaped display names
    out: dict[str, str] = {}
    for match in _INNER_RE.finditer(text):
        inner = match.group(1)
        name = inner.split("|", 1)[0]
        out.setdefault(name, inner)
    return out


def _serialize_entry(mod: ActiveMod, originals: dict[str, str]) -> str:
    original = originals.get(mod.name)
    if original is not None:
        return original  # byte-exact, keeps the game's own escaping
    if not mod.display_name:
        return _escape(mod.name)
    return f"{_escape(mod.name)}|{_escape(mod.display_name)}"


def replace_active_mods(text: str, mods: Sequence[ActiveMod]) -> str:
    """Return ``text`` with its active_mods block swapped for ``mods``."""
    originals = _original_inner_by_name(text)
    out: list[str] = []
    replaced = False
    for line in text.split("\n"):
        if _ENTRY_RE.match(line):
            continue  # drop old indexed entries wherever they sit
        count = _COUNT_RE.match(line)
        if count:
            indent = count.group(1)
            out.append(f"{indent}active_mods: {len(mods)}")
            for i, mod in enumerate(mods):
                out.append(f'{indent}active_mods[{i}]: "{_serialize_entry(mod, originals)}"')
            replaced = True
            continue
        out.append(line)
    if not replaced:
        raise ValueError("no active_mods line found in profile text")
    return "\n".join(out)


def write_active_mods(profile_sii_path: Path, mods: Sequence[ActiveMod]) -> None:
    """Rewrite the active list in ``profile.sii`` (atomic).

    Always writes plaintext SiiNunit, even when the input was ScsC-encrypted.
    ETS2 validates the HMAC of an encrypted profile and falls back to
    profile.bak.sii if it fails - which it does for an externally written one,
    since the HMAC algorithm is not public. Plaintext profiles are read
    without that check, so our changes actually take effect.
    """
    raw = profile_sii_path.read_bytes()
    # strict decode: never risk a lossy round-trip on the user's profile
    text = (decrypt_scsc(raw) if is_scsc(raw) else raw).decode("utf-8")

    new_text = replace_active_mods(text, mods)
    # validate before touching disk: never overwrite with text the parser
    # (and therefore the game) would choke on
    parse_sii(new_text)

    _atomic_write(profile_sii_path, new_text.encode("utf-8"))


def save_active_mods(
    profile_sii_path: Path,
    mods: Sequence[ActiveMod],
    *,
    backup: bool = True,
    backup_root: Path | None = None,
) -> BackupEntry | None:
    """Optionally back up the profile, then write the new active list.

    Returns the BackupEntry when a backup was made, else None. The backup
    captures the pre-edit profile, so one is always recoverable.
    """
    entry = create_backup(profile_sii_path, root=backup_root) if backup else None
    write_active_mods(profile_sii_path, mods)
    return entry


def _atomic_write(target: Path, data: bytes) -> None:
    fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        tmp.replace(target)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
