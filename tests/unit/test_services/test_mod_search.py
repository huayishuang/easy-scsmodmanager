from __future__ import annotations

from easy_scsmodmanager.services.mod_search import matches_search


def test_empty_query_matches_everything() -> None:
    assert matches_search("", "MAN Improved Dashboard", "Mattou") is True


def test_blank_query_matches_everything() -> None:
    assert matches_search("   ", "anything") is True


def test_substring_in_name_matches() -> None:
    # The whole point of the dash bug: "dash" must find "...Dashboard".
    assert matches_search("dash", "MAN TGX 2020 Improved Dashboard") is True


def test_search_is_case_insensitive() -> None:
    assert matches_search("DASH", "man improved dashboard") is True


def test_token_missing_everywhere_does_not_match() -> None:
    assert matches_search("volvo", "MAN TGX 2020 Improved Dashboard", "Mattou") is False


def test_multiword_all_tokens_must_match() -> None:
    # Both words appear (order-independent) so it matches.
    assert matches_search("man dash", "MAN TGX 2020 Improved Dashboard") is True


def test_multiword_one_token_missing_fails() -> None:
    # "scania" is absent, so the whole query fails even though "dash" hits.
    assert matches_search("scania dash", "MAN TGX 2020 Improved Dashboard") is False


def test_tokens_may_match_across_different_haystacks() -> None:
    # "dash" hits the name, "mattou" hits the author field.
    assert matches_search("dash mattou", "Improved Dashboard", "Mattou") is True
