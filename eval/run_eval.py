"""Run the detector over eval/dataset.jsonl and report per-type precision and recall.

Usage: python -m eval.run_eval [--policy PATH]
"""

import argparse
import time
from pathlib import Path

from presidio_analyzer import AnalyzerEngine
from pydantic import BaseModel

from eval.scoring import Span, TypeScore, score_spans
from pii_gateway.config_loader import load_gateway_policy
from pii_gateway.settings import Settings

EVAL_DIR = Path(__file__).resolve().parent
DATASET_PATH = EVAL_DIR / "dataset.jsonl"
RESULTS_PATH = EVAL_DIR / "results.md"
# The demo policy requests the most entities (EMAIL_ADDRESS, PERSON, PHONE_NUMBER).
DEFAULT_POLICY_PATH = EVAL_DIR.parent / "config" / "examples" / "config.demo.yaml"


class LabeledSentence(BaseModel):
    text: str
    spans: list[Span]


def load_dataset(path: Path) -> list[LabeledSentence]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [LabeledSentence.model_validate_json(line) for line in lines if line.strip()]


def percentile(sorted_values: list[float], fraction: float) -> float:
    """Nearest-rank percentile of an ascending list."""
    index = max(0, min(len(sorted_values) - 1, round(fraction * len(sorted_values)) - 1))
    return sorted_values[index]


def detect_spans(
    analyzer: AnalyzerEngine, text: str, entities: list[str] | None
) -> tuple[list[Span], float]:
    """Same call as core/sanitize_text.py makes; returns spans and elapsed milliseconds."""
    started = time.perf_counter()
    results = analyzer.analyze(text=text, language="en", entities=entities)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return [Span(start=r.start, end=r.end, type=r.entity_type) for r in results], elapsed_ms


def format_report(
    scores: dict[str, TypeScore],
    *,
    sentence_count: int,
    policy_path: Path,
    entities: list[str],
    latencies_ms: list[float],
) -> str:
    ordered = sorted(latencies_ms)
    lines = [
        "# Evaluation results",
        "",
        f"- Command: `python -m eval.run_eval --policy {policy_path.name}`",
        f"- Policy entities: {', '.join(entities)}",
        f"- Sentences: {sentence_count} (synthetic, English only)",
        f"- Latency per sentence: p50 {percentile(ordered, 0.5):.1f} ms, "
        f"p95 {percentile(ordered, 0.95):.1f} ms (machine-dependent, not reproducible)",
        "",
        "| Entity | Labeled | TP | FP | FN | Precision | Recall | F1 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for score in scores.values():
        lines.append(
            f"| {score.entity_type} | {score.labeled_count} | {score.true_positives} "
            f"| {score.false_positives} | {score.false_negatives} "
            f"| {score.precision:.2f} | {score.recall:.2f} | {score.f1:.2f} |"
        )
    lines.append("")
    lines.append("Types with fewer than ~20 labeled examples are anecdotes, not measurements.")
    return "\n".join(lines) + "\n"


def run(policy_path: Path) -> str:
    policy = load_gateway_policy(Settings(pii_gateway_config_path=policy_path))
    entities = policy.redaction_entities or None
    analyzer = AnalyzerEngine()  # built once, like the FastAPI lifespan
    dataset = load_dataset(DATASET_PATH)
    analyzer.analyze(
        text="warm-up", language="en", entities=entities
    )  # exclude model load from timing

    pairs: list[tuple[list[Span], list[Span]]] = []
    latencies_ms: list[float] = []
    for sentence in dataset:
        predicted, elapsed_ms = detect_spans(analyzer, sentence.text, entities)
        pairs.append((predicted, sentence.spans))
        latencies_ms.append(elapsed_ms)

    return format_report(
        score_spans(pairs),
        sentence_count=len(dataset),
        policy_path=policy_path,
        entities=policy.redaction_entities,
        latencies_ms=latencies_ms,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY_PATH)
    report = run(parser.parse_args().policy)
    RESULTS_PATH.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
