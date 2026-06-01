"""Free-text matching for the browser search box.

A query is split into whitespace-separated tokens. A mod matches when every
token appears (as a case-insensitive substring) in at least one of the given
haystacks - so the words may be spread across the name, author, file name and
category, and their order does not matter.

The haystacks are passed in already resolved, which keeps this a pure function:
the search box looks at exactly the same display name the card shows, instead
of a second, divergent name source.
"""

from __future__ import annotations


def matches_search(query: str, *haystacks: str) -> bool:
    tokens = query.lower().split()
    if not tokens:
        return True
    fields = [h.lower() for h in haystacks]
    return all(any(token in field for field in fields) for token in tokens)
