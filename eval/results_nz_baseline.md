# Evaluation results

- Command: `python -m eval.run_eval --policy config.nz.yaml --dataset eval/dataset_nz.jsonl --output eval/results_nz_baseline.md`
- Policy entities: NZ_NHI, NZ_IRD, NZ_DRIVER_LICENCE, PHONE_NUMBER
- Sentences: 133 (synthetic, English only)
- Latency per sentence: p50 5.7 ms, p95 7.5 ms (machine-dependent, not reproducible)

| Entity | Labeled | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| NZ_DRIVER_LICENCE | 26 | 0 | 0 | 26 | 0.00 | 0.00 | 0.00 |
| NZ_IRD | 26 | 0 | 0 | 26 | 0.00 | 0.00 | 0.00 |
| NZ_NHI | 27 | 0 | 0 | 27 | 0.00 | 0.00 | 0.00 |
| PHONE_NUMBER | 28 | 28 | 2 | 0 | 0.93 | 1.00 | 0.97 |

Types with fewer than ~20 labeled examples are anecdotes, not measurements.
