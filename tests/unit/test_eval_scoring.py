import pytest
from eval.scoring import Span, score_spans


def _person(start: int, end: int) -> Span:
    return Span(start=start, end=end, type="PERSON")


def test_perfect_match_scores_one() -> None:
    score = score_spans([([_person(0, 5)], [_person(0, 5)])])["PERSON"]
    assert (score.precision, score.recall, score.f1) == (1.0, 1.0, 1.0)
    assert score.labeled_count == 1


def test_missed_span_lowers_recall_only() -> None:
    score = score_spans([([], [_person(0, 5)])])["PERSON"]
    assert (score.true_positives, score.false_negatives) == (0, 1)
    assert (score.precision, score.recall, score.f1) == (0.0, 0.0, 0.0)


def test_false_alarm_on_clean_text_lowers_precision_only() -> None:
    score = score_spans([([_person(0, 5)], [])])["PERSON"]
    assert (score.false_positives, score.labeled_count) == (1, 0)
    assert (score.precision, score.recall) == (0.0, 0.0)


def test_wrong_type_is_a_false_alarm_and_a_miss() -> None:
    email = Span(start=0, end=5, type="EMAIL_ADDRESS")
    scores = score_spans([([_person(0, 5)], [email])])
    assert scores["PERSON"].false_positives == 1
    assert scores["EMAIL_ADDRESS"].false_negatives == 1


def test_partial_overlap_counts_but_touching_spans_do_not() -> None:
    partial = score_spans([([_person(3, 10)], [_person(0, 5)])])["PERSON"]
    assert partial.true_positives == 1
    touching = score_spans([([_person(5, 10)], [_person(0, 5)])])["PERSON"]
    assert (touching.true_positives, touching.false_negatives) == (0, 1)


def test_two_predictions_on_one_label_are_two_true_positives_but_one_found_label() -> None:
    score = score_spans([([_person(0, 3), _person(2, 5)], [_person(0, 5)])])["PERSON"]
    assert score.true_positives == 2
    assert score.recall == 1.0


def test_counts_add_up_across_sentences() -> None:
    sentences = [
        ([_person(0, 5)], [_person(0, 5)]),
        ([], [_person(0, 5)]),
        ([_person(0, 5)], []),
    ]
    score = score_spans(sentences)["PERSON"]
    assert (score.true_positives, score.false_positives, score.false_negatives) == (1, 1, 1)
    assert score.precision == pytest.approx(0.5)
    assert score.recall == pytest.approx(0.5)
