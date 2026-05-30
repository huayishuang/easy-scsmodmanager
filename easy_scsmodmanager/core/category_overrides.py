"""Persistent per-mod category overrides.

Kept in their own SQLite file so clearing the scan cache never drops a
user's manual corrections. mod_key is the mod's path stem.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


class CategoryOverrides:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._con = sqlite3.connect(str(db_path))
        self._con.execute(
            "CREATE TABLE IF NOT EXISTS category_override "
            "(mod_key TEXT PRIMARY KEY, token TEXT NOT NULL)"
        )
        self._con.commit()

    def get(self, mod_key: str) -> str | None:
        row = self._con.execute(
            "SELECT token FROM category_override WHERE mod_key = ?", (mod_key,)
        ).fetchone()
        return row[0] if row else None

    def set(self, mod_key: str, token: str) -> None:
        self._con.execute(
            "INSERT INTO category_override (mod_key, token) VALUES (?, ?) "
            "ON CONFLICT(mod_key) DO UPDATE SET token = excluded.token",
            (mod_key, token),
        )
        self._con.commit()

    def clear(self, mod_key: str) -> None:
        self._con.execute("DELETE FROM category_override WHERE mod_key = ?", (mod_key,))
        self._con.commit()
