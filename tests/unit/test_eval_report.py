from pathlib import Path

from eval.run_eval import format_report, percentile
from eval.scoring import TypeScore


def test_percentile_uses_nearest_rank() -> None:
    values = [float(n) for n in range(1, 101)]
    assert percentile(values, 0.5) == 50.0
    assert percentile(values, 0.95) == 95.0
    assert percentile([7.0], 0.95) == 7.0


def test_report_shows_counts_beside_ratios() -> None:
    score = TypeScore(
        entity_type="PERSON",
        true_positives=3,
        false_positives=1,
        false_negatives=2,
        labeled_count=5,
        precision=0.75,
        recall=0.6,
        f1=0.67,
    )
    report = format_report(
        {"PERSON": score},
        sentence_count=10,
        policy_path=Path("config.demo.yaml"),
        entities=["PERSON"],
        latencies_ms=[1.0, 2.0, 3.0],
    )
    assert "| PERSON | 5 | 3 | 1 | 2 | 0.75 | 0.60 | 0.67 |" in report
    assert "Sentences: 10" in report
