"""Aggregate Presidio analyzer results (counts only, no spans)."""

from collections.abc import Iterable
from typing import Any


def entity_type_counts(results: Iterable[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in results:
        et = getattr(r, "entity_type", None)
        if et is not None:
            key = str(et)
            counts[key] = counts.get(key, 0) + 1
    return counts
