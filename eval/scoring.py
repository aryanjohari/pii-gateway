"""Span-level precision, recall and F1 per entity type (see ADR 0004).

A predicted span is a true positive when a labeled span of the same type
overlaps it by at least one character. A labeled span is found when a
predicted span of the same type overlaps it. The two are counted separately,
so two predictions on one labeled span give two true positives but only one
found label: precision is judged per prediction, recall per label.
"""

from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict


class Span(BaseModel):
    model_config = ConfigDict(frozen=True)

    start: int
    end: int
    type: str


class TypeScore(BaseModel):
    entity_type: str
    true_positives: int
    false_positives: int
    false_negatives: int
    labeled_count: int
    precision: float
    recall: float
    f1: float


def _overlaps(first: Span, second: Span) -> bool:
    return min(first.end, second.end) > max(first.start, second.start)


def _is_matched(span: Span, candidates: list[Span]) -> bool:
    return any(c.type == span.type and _overlaps(span, c) for c in candidates)


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _build_score(
    entity_type: str,
    true_positives: int,
    false_positives: int,
    false_negatives: int,
    labeled_count: int,
) -> TypeScore:
    precision = _ratio(true_positives, true_positives + false_positives)
    recall = _ratio(labeled_count - false_negatives, labeled_count)
    f1 = _f1(precision, recall)
    return TypeScore(
        entity_type=entity_type,
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        labeled_count=labeled_count,
        precision=precision,
        recall=recall,
        f1=f1,
    )


def _f1(precision: float, recall: float) -> float:
    total = precision + recall
    return 2 * precision * recall / total if total else 0.0


def score_spans(sentences: Iterable[tuple[list[Span], list[Span]]]) -> dict[str, TypeScore]:
    """Score (predicted, labeled) span lists, one pair per sentence, per entity type."""
    counts: dict[str, list[int]] = {}  # type -> [tp, fp, fn, labeled]
    for predicted, labeled in sentences:
        for span in predicted:
            row = counts.setdefault(span.type, [0, 0, 0, 0])
            row[0 if _is_matched(span, labeled) else 1] += 1
        for span in labeled:
            row = counts.setdefault(span.type, [0, 0, 0, 0])
            row[3] += 1
            if not _is_matched(span, predicted):
                row[2] += 1
    return {t: _build_score(t, *row) for t, row in sorted(counts.items())}
