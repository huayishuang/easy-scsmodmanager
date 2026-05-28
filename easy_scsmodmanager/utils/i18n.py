"""Translation lookup. Single JSON per language, flat dotted keys.

Usage:
    from easy_scsmodmanager.utils.i18n import t
    label.setText(t("app.title"))

If a key is missing, the key itself is returned so the bug is visible in the UI.
"""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from importlib import resources

DEFAULT_LANG = "en"
SUPPORTED_LANGS = ("en", "de")

log = logging.getLogger(__name__)


def _detect_language() -> str:
    env = os.environ.get("ESCSMM_LANG") or os.environ.get("LANG") or ""
    code = env.split(".")[0].split("_")[0].lower()
    if code in SUPPORTED_LANGS:
        return code
    return DEFAULT_LANG


@lru_cache(maxsize=4)
def _load(lang: str) -> dict[str, str]:
    try:
        data = (
            resources.files("easy_scsmodmanager.resources.i18n")
            .joinpath(f"{lang}.json")
            .read_text(encoding="utf-8")
        )
        return json.loads(data)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        log.warning("Failed to load i18n for %s: %s", lang, exc)
        return {}


_active_lang = _detect_language()


def set_language(lang: str) -> None:
    global _active_lang
    if lang in SUPPORTED_LANGS:
        _active_lang = lang
    else:
        log.warning("Unsupported language %s, keeping %s", lang, _active_lang)


def t(key: str, **kwargs: object) -> str:
    table = _load(_active_lang)
    value = table.get(key)
    if value is None and _active_lang != DEFAULT_LANG:
        value = _load(DEFAULT_LANG).get(key)
    if value is None:
        return key
    if kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, IndexError):
            return value
    return value
