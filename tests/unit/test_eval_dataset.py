from pathlib import Path

import pytest
from pydantic import BaseModel

EVAL_DIR = Path(__file__).resolve().parents[2] / "eval"
# Each dataset file with the entity types it must label.
DATASETS = {
    "dataset.jsonl": {"EMAIL_ADDRESS", "PERSON", "PHONE_NUMBER"},
    "dataset_nz.jsonl": {"NZ_NHI", "NZ_IRD", "NZ_DRIVER_LICENCE", "PHONE_NUMBER"},
}
dataset_names = pytest.mark.parametrize("dataset_name", list(DATASETS))


class LabeledSpan(BaseModel):
    start: int
    end: int
    type: str


class LabeledSentence(BaseModel):
    text: str
    spans: list[LabeledSpan]


def _load_dataset(dataset_name: str) -> list[LabeledSentence]:
    lines = (EVAL_DIR / dataset_name).read_text(encoding="utf-8").splitlines()
    return [LabeledSentence.model_validate_json(line) for line in lines]


@dataset_names
def test_every_span_is_non_empty_and_inside_its_text(dataset_name: str) -> None:
    for sentence in _load_dataset(dataset_name):
        for span in sentence.spans:
            assert 0 <= span.start < span.end <= len(sentence.text), sentence.text
            assert sentence.text[span.start : span.end].strip(), sentence.text


@dataset_names
def test_spans_in_one_sentence_do_not_overlap(dataset_name: str) -> None:
    for sentence in _load_dataset(dataset_name):
        ordered = sorted(sentence.spans, key=lambda span: span.start)
        for earlier, later in zip(ordered, ordered[1:], strict=False):
            assert earlier.end <= later.start, sentence.text


@dataset_names
def test_each_entity_type_has_enough_examples_and_negatives_exist(dataset_name: str) -> None:
    sentences = _load_dataset(dataset_name)
    counts: dict[str, int] = {}
    for sentence in sentences:
        for span in sentence.spans:
            counts[span.type] = counts.get(span.type, 0) + 1
    assert set(counts) == DATASETS[dataset_name]
    assert min(counts.values()) >= 20
    assert any(not sentence.spans for sentence in sentences)
