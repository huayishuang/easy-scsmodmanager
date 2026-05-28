"""CLI subcommand ``scan`` - lists mods of a given game install.

Phase 1 exit-criterion command: enumerates every .scs in mod/ +
workshop/ and marks each entry with its active state by cross-
referencing the user's profile.sii ``active_mods`` list.
"""

from __future__ import annotations

import argparse
import datetime
import sys
from collections.abc import Iterable
from pathlib import Path

from easy_scsmodmanager.core.game_paths import Game, detect_game_installs
from easy_scsmodmanager.services.mod_scanner import ScannedMod, scan_game_install
from easy_scsmodmanager.services.profile_reader import (
    Profile,
    decode_profile_dir_name,
    discover_profiles,
    read_profile,
)

GAME_BY_KEY = {"ets2": Game.ETS2, "ats": Game.ATS}


def add_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = subparsers.add_parser("scan", help="list installed mods and their active state")
    p.add_argument(
        "--game",
        choices=sorted(GAME_BY_KEY),
        default="ets2",
        help="game to scan (default: ets2)",
    )
    p.add_argument(
        "--profile",
        help=(
            "profile selector: dir-name (hex), display name substring, or list "
            "index (1-based). If omitted, picks the most recently modified."
        ),
    )
    p.add_argument(
        "--list-profiles",
        action="store_true",
        help="only print the available profiles and exit",
    )
    p.set_defaults(func=run)
    return p


def run(args: argparse.Namespace) -> int:
    game = GAME_BY_KEY[args.game]
    installs = detect_game_installs(game)
    if not installs:
        print(f"No {game.value.upper()} install found.", file=sys.stderr)
        return 1

    for install in installs:
        print(f"=== {game.value.upper()} ({install.kind.value}) ===")
        print(f"  documents: {install.documents_dir}")

        profile_paths = discover_profiles(install)
        if not profile_paths:
            print("  profile  : (no profiles found in this install)")
            if not args.list_profiles:
                mods = scan_game_install(install)
                _render_mod_table(mods, set())
            print()
            continue

        loaded = _load_all_profiles(profile_paths)
        selected_idx = _select_profile(loaded, args.profile)
        _render_profile_list(loaded, selected_idx)

        if args.list_profiles:
            print()
            continue

        active_names = _active_mod_names(loaded[selected_idx][1])
        mods = scan_game_install(install)
        _render_mod_table(mods, active_names)
        print()
    return 0


def _load_all_profiles(paths: list[Path]) -> list[tuple[Path, Profile | None, float]]:
    """Load each profile from disk. Tolerate read errors per-entry."""
    out: list[tuple[Path, Profile | None, float]] = []
    for sii in paths:
        mtime = sii.stat().st_mtime
        try:
            out.append((sii, read_profile(sii), mtime))
        except Exception as exc:
            print(f"  warn: failed to read {sii.parent.name}: {exc}", file=sys.stderr)
            out.append((sii, None, mtime))
    return out


def _select_profile(
    loaded: list[tuple[Path, Profile | None, float]],
    selector: str | None,
) -> int:
    if selector:
        # Try numeric index first (1-based)
        if selector.isdigit():
            idx = int(selector) - 1
            if 0 <= idx < len(loaded):
                return idx
        # Then try exact dir-name match
        for i, (path, _, _) in enumerate(loaded):
            if path.parent.name == selector:
                return i
        # Then display-name substring (case-insensitive)
        needle = selector.lower()
        for i, (path, profile, _) in enumerate(loaded):
            name = profile.profile_name if profile else decode_profile_dir_name(path.parent.name)
            if needle in name.lower():
                return i
        print(
            f"  warn: profile selector {selector!r} did not match, falling back to most recent",
            file=sys.stderr,
        )

    # Default: most recently modified
    return max(range(len(loaded)), key=lambda i: loaded[i][2])


def _render_profile_list(
    loaded: list[tuple[Path, Profile | None, float]],
    selected_idx: int,
) -> None:
    print(f"  profiles : {len(loaded)} found")
    for i, (path, profile, mtime) in enumerate(loaded):
        marker = "->" if i == selected_idx else "  "
        name = profile.profile_name if profile else decode_profile_dir_name(path.parent.name)
        active = len(profile.active_mods) if profile else "?"
        when = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        print(f"    {marker} [{i + 1}] {name!r:36}  active={active}  modified={when}")
    print("  (--profile <number|hex|substring> to pick a different one)")


def _active_mod_names(profile: Profile | None) -> set[str]:
    if profile is None:
        return set()
    return {m.name for m in profile.active_mods}


def _render_mod_table(mods: Iterable[ScannedMod], active_names: set[str]) -> None:
    rows: list[tuple[str, str, str, str, str]] = []
    counts = {"active": 0, "inactive": 0, "error": 0}
    for mod in mods:
        status = _status_for(mod, active_names)
        counts[status] += 1
        manifest = mod.manifest
        name = manifest.display_name if manifest else mod.path.stem
        author = manifest.author if manifest else "-"
        categories = ",".join(manifest.categories) if manifest else "-"
        rows.append((status, mod.format.value, name[:50], author[:24], categories[:30]))

    if not rows:
        print("  (no mods)")
        return

    print(
        f"  total={len(rows)}  active={counts['active']}  "
        f"inactive={counts['inactive']}  error={counts['error']}"
    )
    print(f"  {'status':<9}{'fmt':<10}{'name':<52}{'author':<26}categories")
    for status, fmt, name, author, categories in rows:
        print(f"  {status:<9}{fmt:<10}{name:<52}{author:<26}{categories}")


def _status_for(mod: ScannedMod, active_names: set[str]) -> str:
    # ETS2 references mods by the .scs file stem in active_mods[]. An
    # encrypted-manifest mod still counts as active for the user even
    # if we cannot parse its metadata.
    if mod.path.stem in active_names:
        return "active"
    if mod.error is not None and mod.manifest is None:
        return "error"
    return "inactive"
