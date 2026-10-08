# Baseline v1 results

The first Elo model improves on a constant home-win probability, but trails the
retrospective sportsbook probability reference. This does not establish a betting edge.

## Same-game development comparison

Warm-up uses 1,319 completed 2023-24 reference games. Evaluation covers 1,319 accepted
2024-25 records (2024-10-22 through 2025-06-22). The Elo settings were fixed in the
[protocol](BASELINE_PROTOCOL.md) before the run. The 2025-26 model holdout was not loaded.

| Model | Accuracy | Log loss (lower better) | Brier score (lower better) |
|---|---:|---:|---:|
| Constant training home-win rate | 54.44% | 0.68923 | 0.24804 |
| Fixed Elo | 65.05% | 0.61895 | 0.21554 |
| Timing-unverified market reference | 69.14% | 0.58624 | 0.20133 |

The constant training probability is 54.74%; it is held fixed throughout development.
All accuracy calculations select the home team on an exact 50% tie. The JSON report
also includes a 50% probability baseline, calibration bins and Wilson intervals.

Elo minus market log loss is **+0.03271**, with a paired day-cluster bootstrap 95%
interval of **[+0.02061, +0.04494]**. The Brier difference is **+0.01421**, interval
**[+0.00870, +0.01963]**. Positive means Elo is worse. These exploratory intervals
do not capture all serial dependence across dates or resolve quote timing differences.

## Data checks and reproducibility

- Training odds table: 1,255 rows, 1,253 source/result matches, two quarantined rows,
  66 reference games missing (14 inside its date span, 52 after). Elo instead warms up
  on all 1,319 verified completed reference games, without using odds as input.
- Development ratings update on all 1,321 completed reference games. The two games
  with source-score disagreements are excluded from the paired odds evaluation.
- The protocol, implementation and evaluation results are separate commits.
- Aggregate report: [baseline-v1.json](reports/baseline-v1.json).
- Published implementation commit: `d9953832c6d85024567cecb256bd20f346b10950`.
- Re-running the published implementation reproduced the original predictions byte-for-byte.
  Prediction SHA-256: `1a035fe6b989e89e807943fd574011123a05d4217073fad9da5b723f898b0eed`.
- 26 tests passed, including current/future outcome perturbation, same-date batch ordering,
  replay prevention, probability metrics, and deterministic paired bootstrap checks.

## Interpretation and next experiment

This is a useful floor for model quality, not evidence of a commercial forecasting advantage.
The market quotes have unknown observation times and may incorporate information unavailable
to the daily Elo forecast. Historical prices have not been independently verified.

Next: define a separate, recorded experiment for a regularized model with lagged team strength,
rest and recent performance features. Include a market-informed comparator only where quote
timing supports it. Keep 2025-26 held out from model selection, and retain this failed-to-beat-market
result rather than replacing it with a better-looking tuned run. No ROI or live execution claims.
