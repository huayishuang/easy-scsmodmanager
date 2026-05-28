"""CLI subcommand ``scan`` - lists mods of a given game install.

Phase 1 exit-criterion command: enumerates every .scs in mod/ +
workshop/ and marks each entry with its active state by cross-
referencing the user's profile.sii ``active_mods`` list.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable

from easy_scsmodmanager.core.game_paths import Game, detect_game_installs
from easy_scsmodmanager.services.mod_scanner import ScannedMod, scan_game_install
from easy_scsmodmanager.services.profile_reader import (
    Profile,
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
        help="profile directory name (hex). If omitted, the first profile found is used.",
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
        profile = _pick_profile(install, args.profile)
        active_names = _active_mod_names(profile)
        if profile:
            print(f"  profile  : {profile.profile_name!r} ({len(active_names)} active mods)")
        else:
            print("  profile  : (none found)")

        mods = scan_game_install(install)
        _render_mod_table(mods, active_names)
        print()
    return 0


def _pick_profile(install, profile_dir_name: str | None) -> Profile | None:
    paths = discover_profiles(install)
    if not paths:
        return None
    if profile_dir_name:
        for p in paths:
            if p.parent.name == profile_dir_name:
                try:
                    return read_profile(p)
                except Exception as exc:
                    print(f"  warn: failed to read {p}: {exc}", file=sys.stderr)
                    return None
        print(f"  warn: profile {profile_dir_name!r} not found", file=sys.stderr)
        return None
    try:
        return read_profile(paths[0])
    except Exception as exc:
        print(f"  warn: failed to read {paths[0]}: {exc}", file=sys.stderr)
        return None


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
    print(
        f"  {'status':<9}{'fmt':<10}{'name':<52}{'author':<26}categories"
    )
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
