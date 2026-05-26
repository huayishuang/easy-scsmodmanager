"""Shared pytest fixtures."""

from __future__ import annotations

import os

# Force offscreen Qt platform for headless test environments.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
