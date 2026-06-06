"""Move local (non-Workshop) mods to the OS trash, and tell which profiles
still reference a mod.

Deletion goes through the OS trash only - no hard-delete fallback. A failed
trash is an error to report, never a reason to destroy the file. Workshop mods
are not handled here at all; they belong to Steam.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QFile

from easy_scsmodmanager.services.mod_matching import ActiveModMatcher
from easy_scsmodmanager.services.mod_scanner import ScannedMod
from easy_scsmodmanager.services.profile_reader import Profile, decode_profile_dir_name


def move_path_to_trash(path: Path) -> bool:
    """Move a file or directory to the OS trash. True on success.

    Uses the INSTANCE form, which returns a plain bool. The static overload
    QFile.moveToTrash(name) returns a tuple whose (False, '') is truthy - it
    would report success on a failed move.
    """
    return QFile(str(path)).moveToTrash()


def active_profiles_for(mod: ScannedMod, profiles: list[Profile]) -> list[str]:
    """Clear-text names of profiles whose load order still lists ``mod``.

    The game writes active_mods tokens that can differ from mod_name, so each
    entry is resolved through the 4-strategy ActiveModMatcher rather than a
    naive token == mod_name compare (which would miss exactly the data-loss
    case the delete warning is for).
    """
    matcher = ActiveModMatcher([mod])
    names: list[str] = []
    for prof in profiles:
        if any(matcher.lookup(am) is not None for am in prof.active_mods):
            names.append(prof.profile_name or decode_profile_dir_name(prof.dir_name))
    return names
