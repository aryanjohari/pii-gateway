# Evaluation results

- Command: `python -m eval.run_eval --policy config.demo.yaml`
- Policy entities: EMAIL_ADDRESS, PERSON, PHONE_NUMBER
- Sentences: 90 (synthetic, English only)
- Latency per sentence: p50 6.0 ms, p95 13.2 ms (machine-dependent, not reproducible)

| Entity | Labeled | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| EMAIL_ADDRESS | 25 | 25 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| PERSON | 31 | 31 | 1 | 0 | 0.97 | 1.00 | 0.98 |
| PHONE_NUMBER | 24 | 24 | 0 | 0 | 1.00 | 1.00 | 1.00 |

Types with fewer than ~20 labeled examples are anecdotes, not measurements.
