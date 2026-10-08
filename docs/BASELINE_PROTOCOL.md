# Baseline protocol v1 — frozen before evaluation

Created 2026-10-08. This protocol is committed before running model evaluation.
No parameter search or results-driven changes are part of this first experiment.

## Purpose
Establish a reproducible probability benchmark, not a profitable betting claim.
The first comparison answers whether a simple result-based model is competitive with
the available, timing-unverified sportsbook probabilities on the same games.

## Data and splits
- Warm-up/training: independently collected completed ESPN NBA games in season year
  2024 (2023-24), regular season, playoffs and play-ins. Verify duplicated team-schedule
  copies agree and record all input hashes. Also reconcile the older odds table against
  these results to document its coverage; odds are not model training features.
- Development evaluation: 2024-25 (season year 2025). Predict all verified games,
  evaluate on the previously accepted 1,319 source/score-matched records with usable odds.
  Ratings update from all verified games, including games excluded from odds comparison.
- Final holdout: 2025-26. Do not load its outcomes into the model runner, calculate its
  performance or tune against it in this milestone. Prior data-quality checks are not
  predictive model evaluation. Missing January-June odds remain an unresolved gap.
- Repeatedly examining 2024-25 results makes it development data, not an untouched test.

## Models (fixed before evaluation)
1. Coin flip: probability 0.5 for the listed home team.
2. Training home-win rate: home wins / training games, fixed throughout development.
3. Elo: initial rating 1500, logistic scale 400, K=20; home advantage 65 rating points
   only when `neutral_site` is explicitly false; no advantage when true or unknown.
   At a season boundary regress each rating 25% toward 1500 (retain 75%).
4. Retrospective market reference: proportional normalization of the source's paired
   home/away American prices. It is not a truth label or time-aligned tradable forecast.

Predict each Eastern game-date batch using ratings available before that date. Then
update ratings using its results; never update from the current game before predicting it.
Same-date predictions cannot depend on other results that date. This conservative
daily convention assumes prior-date results are available before the next slate.
No injuries, player features, margin-of-victory boosts, odds input or fitted hyperparameters.

## Metrics and uncertainty
- Report sample size, home-win fraction, accuracy, log loss and Brier score on identical games.
- Calibration: ten fixed probability bins with counts, mean predicted probability,
  observed home-win frequency and Wilson 95% intervals (empty bins omitted).
- Compare Elo minus market and Elo minus training-home-rate in log loss and Brier score.
  Negative means Elo is better. Bootstrap paired daily clusters, 2,000 draws, seed 20261008,
  report percentile 95% intervals. These exploratory intervals do not model all serial
  dependence across dates and do not prove profitability or generalization.
- Save predictions locally, input hashes, configuration, model version, code commit,
  evaluation period and aggregate metrics. No ROI, staking or betting strategy optimization.

## Acceptance and next decision
- A working pipeline must pass chronology/leakage, duplicate-game, invalid-value and
  reproducibility tests, and must not rewrite prior experiment directories.
- Numerical improvement is evidence to investigate, not a product performance promise.
- If Elo trails the market, report that directly. Do not tune until it appears to win.
- Next features must have documented historical availability and be tested against these
  baselines, preserving the separate holdout and a record of every experiment.
- Data reuse permissions and independently verified quote timing remain product blockers;
  this local exploratory comparison does not resolve them.
