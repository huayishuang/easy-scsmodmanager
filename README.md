# Easy SCSModManager

Cross-platform mod and profile manager for **Euro Truck Simulator 2** and **American Truck Simulator**. Built because the in-game mod-manager is painful and external tools like Trucky are only download wrappers.

> Status: **Pre-Alpha** - core scaffolding only. See `docs/` for the design spec.

## What it will do

- Read your installed mods from `mod/` and Steam Workshop (`workshop/content/<appid>/`) on Linux and Windows
- Show them in a familiar ETS2-style mod browser (card grid, search, sort, multi-category filter)
- Manage the active mods list with **real drag and drop** between panels, multi-select with Ctrl/Shift, drop position indicators
- Edit and re-save `profile.sii` (encrypted, AES-256-CBC + zlib) with automatic backups
- Detect mod conflicts via def-file overlap analysis and manifest version checks
- Save and load mod presets (Vutomy / GMC / ProMods style combos)
- Workshop integration: live update notifications, one click to the Steam Workshop page
- Profile manager with backup and restore, multi-profile switching
- Both ETS2 and ATS from day one, with a game switcher in the UI

## What it will not do

- Download mods directly through Steam authentication (use Steam to subscribe; this app reads from the Workshop folder afterward)
- Save game editing (separate concern)
- Mod creation tooling

## Status

This repository currently contains only the project scaffold. The full design lives in the Obsidian vault under `02 Projekte/EasySCSModManager/`. Implementation starts with Phase 1 (read-only foundation) once the scaffold is in place.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
