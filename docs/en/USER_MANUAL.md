# 📖 Easy SCSModManager - User Manual

**Platform:** Linux (AppImage, deb, rpm, AUR, tar.gz) and Windows (.exe)
**Games:** Euro Truck Simulator 2 and American Truck Simulator

---

## Table of Contents

1. [What it does](#what-it-does)
2. [The two panels](#the-two-panels)
3. [Profiles](#profiles)
4. [Activating and ordering mods](#activating-and-ordering-mods)
5. [Load-order groups](#load-order-groups)
6. [Conflicts](#conflicts)
7. [Deleting mods](#deleting-mods)
8. [Backups](#backups)
9. [Switching games](#switching-games)
10. [Settings](#settings)
11. [Updates](#updates)

---

## What it does

Easy SCSModManager reads the mods you already own (local `mod/` folder **and**
Steam Workshop), shows them with their real names and icons, and lets you build
the active load order for a profile - then writes it straight into the game's
`profile.sii` in plain text, so the game starts with exactly the order you set.

It only ever edits your own `profile.sii` and reads your own installed mods. It
is not affiliated with SCS Software or Valve.

## The two panels

- **Left - the mod library:** every installed mod as a card with icon, name,
  author and category. Search, sort and filter it from the toolbar above.
- **Right - the active list:** the load order for the selected profile, split
  into load-order groups, top to bottom (top = highest priority).

Drag the divider to resize. Maximise the window and the grid fills the extra
width with more columns.

## Profiles

The profile dropdown in the active-list header lists every profile found for
the current game. Pick one to load its active mods. **Save** writes your changes
back to `profile.sii` - the game must be closed when you save, or it overwrites
the file on exit.

## Activating and ordering mods

- **Double-click** a mod card to activate it. It lands at the bottom of its own
  load-order group's block, and the new row is selected so you can see it.
- **Drag** a card from the library into the active list to drop it at a precise
  position. Dropping it into a section also assigns it to that section.
- **Drag** rows inside the active list to reorder. **Double-click** a row in the
  active list to remove it.

## Load-order groups

The active list is split into groups (financial, sound, physics, trucks,
trailers, maps, and so on) with headers, so a mod sits near others of its kind.
The order of the groups follows the order the game loads them.

- A mod in the wrong group gets an **orange left border**. Right-click it and
  choose **Move to** -> a group to pin it there, or **Automatic (own category)**
  to send it back to its natural group.
- **Move to** acts on your whole selection at once.
- Dragging a mod into a section pins it to that section; dragging it back to its
  home section clears the pin.

## Conflicts

Two active mods conflict when they change the same `def/` file - the higher one
in the list wins. Conflicts are a hint, not an error (for maps an overlap is
often intentional).

A conflicting mod gets a glyph before its name:

- **⚠ yellow triangle - partly overwritten:** some of its files lose to mods
  above it.
- **⊘ red crossed circle - fully overwritten:** all of its files lose - the mod
  effectively does nothing where it sits.
- **No glyph:** it wins all its shared files.

Hover the mod for the full list of overwritten files and which mod wins each. A
legend appears at the bottom of the panel while any conflict exists.

## Deleting mods

Right-click a mod (or select several, or press **Delete**) and choose
**Delete...** to move local mods to the system trash - restore them from there
if you change your mind. Workshop mods stay managed by Steam (the entry is shown
but disabled). If a mod is still used by a saved profile, the confirmation names
the affected profiles first.

Tip: set the **Source** filter to **Local**, press **Ctrl+A** to select every
visible mod, then delete - a quick way to clean out local clutter.

## Backups

The profile header has **Backup** and **Restore**. A backup is a zip of the
profile, stored outside the game's own tree, so it is never touched by the game.
Restore picks an earlier backup back into place.

## Switching games

The **Game** menu switches between ETS2 and ATS (only installed games are
selectable). Your choice is remembered for next launch.

## Settings

**File -> Settings** covers the interface language, manual path overrides (when
auto-detection misses an install), the map-base term list, and behaviour toggles
(jump-to-active on click, check for updates on startup).

## Updates

**Help -> Check for Updates** asks GitHub for a newer release. The AppImage and
Windows builds can download and install a verified update; package installs
(deb/rpm/AUR/tar.gz) get a notice and keep updating through their package
manager.
