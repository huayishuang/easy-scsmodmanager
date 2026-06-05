"""Tiny Windows-registry string reader.

The Steam install dir and the user's redirected Documents folder both live in
the registry on Windows. This wraps the ``winreg`` calls in one place so the
detectors stay readable and so a single function can be monkeypatched in tests
(``winreg`` itself only exists on Windows). Off Windows every read returns
None, so callers can always fall back to their environment-based guesses.
"""

from __future__ import annotations

import os
import sys

# friendly hive names so callers (and test fakes) never import winreg themselves
_HIVES = ("HKCU", "HKLM")


def read_string(hive: str, subkey: str, name: str, *, expand: bool = False) -> str | None:
    """One registry string value, or None when missing / not on Windows.

    ``expand`` runs %VAR% expansion for REG_EXPAND_SZ values (Documents path).
    """
    if sys.platform != "win32":
        return None

    import winreg  # Windows-only stdlib, imported lazily on purpose

    hives = {
        "HKCU": winreg.HKEY_CURRENT_USER,
        "HKLM": winreg.HKEY_LOCAL_MACHINE,
    }
    root = hives.get(hive)
    if root is None:
        raise ValueError(f"unknown registry hive: {hive}")

    try:
        with winreg.OpenKey(root, subkey) as key:
            val, _kind = winreg.QueryValueEx(key, name)
    except OSError:
        # key or value absent - a normal, expected miss
        return None

    text = str(val).strip()
    if not text:
        return None
    return os.path.expandvars(text) if expand else text
