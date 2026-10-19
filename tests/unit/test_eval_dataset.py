from pathlib import Path

from pydantic import BaseModel

DATASET_PATH = Path(__file__).resolve().parents[2] / "eval" / "dataset.jsonl"


class LabeledSpan(BaseModel):
    start: int
    end: int
    type: str


class LabeledSentence(BaseModel):
    text: str
    spans: list[LabeledSpan]


def _load_dataset() -> list[LabeledSentence]:
    lines = DATASET_PATH.read_text(encoding="utf-8").splitlines()
    return [LabeledSentence.model_validate_json(line) for line in lines]


def test_every_span_is_non_empty_and_inside_its_text() -> None:
    for sentence in _load_dataset():
        for span in sentence.spans:
            assert 0 <= span.start < span.end <= len(sentence.text), sentence.text
            assert sentence.text[span.start : span.end].strip(), sentence.text


def test_spans_in_one_sentence_do_not_overlap() -> None:
    for sentence in _load_dataset():
        ordered = sorted(sentence.spans, key=lambda span: span.start)
        for earlier, later in zip(ordered, ordered[1:], strict=False):
            assert earlier.end <= later.start, sentence.text


def test_each_entity_type_has_enough_examples_and_negatives_exist() -> None:
    sentences = _load_dataset()
    counts: dict[str, int] = {}
    for sentence in sentences:
        for span in sentence.spans:
            counts[span.type] = counts.get(span.type, 0) + 1
    assert set(counts) == {"EMAIL_ADDRESS", "PERSON", "PHONE_NUMBER"}
    assert min(counts.values()) >= 20
    assert any(not sentence.spans for sentence in sentences)
