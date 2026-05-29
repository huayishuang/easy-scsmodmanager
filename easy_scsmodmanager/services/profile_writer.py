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

from easy_scsmodmanager.integrations.sii.crypto import decrypt_scsc, encrypt_scsc, is_scsc
from easy_scsmodmanager.services.profile_backup import BackupEntry, create_backup
from easy_scsmodmanager.services.profile_reader import ActiveMod

_COUNT_RE = re.compile(r"^(\s*)active_mods\s*:\s*\d+\s*$")
_ENTRY_RE = re.compile(r"^\s*active_mods\s*\[\d+\]\s*:")


def _serialize_entry(mod: ActiveMod) -> str:
    # inverse of ActiveMod.parse: "name|display", or just "name" when blank
    return f"{mod.name}|{mod.display_name}" if mod.display_name else mod.name


def replace_active_mods(text: str, mods: Sequence[ActiveMod]) -> str:
    """Return ``text`` with its active_mods block swapped for ``mods``."""
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
                out.append(f'{indent}active_mods[{i}]: "{_serialize_entry(mod)}"')
            replaced = True
            continue
        out.append(line)
    if not replaced:
        raise ValueError("no active_mods line found in profile text")
    return "\n".join(out)


def write_active_mods(profile_sii_path: Path, mods: Sequence[ActiveMod]) -> None:
    """Rewrite the active list in ``profile.sii`` (format-preserving, atomic)."""
    raw = profile_sii_path.read_bytes()
    encrypted = is_scsc(raw)
    # strict decode: never risk a lossy round-trip on the user's profile
    text = (decrypt_scsc(raw) if encrypted else raw).decode("utf-8")

    new_text = replace_active_mods(text, mods)
    payload = new_text.encode("utf-8")
    out_bytes = encrypt_scsc(payload) if encrypted else payload

    _atomic_write(profile_sii_path, out_bytes)


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
