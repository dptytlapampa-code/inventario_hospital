"""Global search utilities."""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence


def global_search(query: str, dataset: Iterable[Mapping[str, object]]) -> list[Mapping[str, object]]:
    """Return items from ``dataset`` whose values contain ``query``.

    The search is case-insensitive and inspects the string representation of
    each value in the mapping.  The function returns a list with matching
    mappings; it never mutates the original dataset.
    """

    query_lower = query.lower()
    results: list[Mapping[str, object]] = []
    for item in dataset:
        for value in item.values():
            if query_lower in str(value).lower():
                results.append(item)
                break
    return results
