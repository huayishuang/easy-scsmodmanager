from __future__ import annotations

import pytest

pytest.importorskip("pytestqt")

from easy_scsmodmanager.ui.menu import main_menu  # noqa: E402


def test_open_doc_builds_github_blob_url_with_language(monkeypatch) -> None:
    opened: list[str] = []
    monkeypatch.setattr(main_menu.webbrowser, "open", lambda url: opened.append(url))
    monkeypatch.setattr(main_menu, "current_language", lambda: "de")

    main_menu._open_doc("USER_MANUAL.md")

    assert opened == [
        "https://github.com/Switch-Bros/easy-scsmodmanager/blob/main/docs/de/USER_MANUAL.md"
    ]


def test_docs_entries_cover_the_four_manuals() -> None:
    keys = {key for key, _ in main_menu._DOCS}
    assert keys == {"manual", "tips", "shortcuts", "faq"}
