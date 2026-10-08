# Development plan

## Goal
A free-to-test NBA pregame research application comparing independent model probabilities
with sportsbook market estimates and available prices. No automatic wagering.

## Completed foundation (2026-10-08)
- Standard-library Python odds calculations: price conversion, break-even probability,
  proportional two-way de-vig, model EV, idealized two-way arbitrage stake fractions.
- Explicitly synthetic CLI example; no trained model or live prices claimed.
- Reproducible older NBA JSON audit and recent SQLite inspection.
- Eight unit tests covering known prices, invariants, invalid inputs and audit behavior.
- Data source register, development instructions, secret/data ignores, CI configuration.

## Completed recent-data validation (2026-10-08)
- Inspected upstream collection code; current defaults do not establish per-row bookmaker or timing.
- Collected and hashed 180 ESPN schedule responses across 30 teams, two seasons and three categories
  (regular, playoff, play-in). Cached outside Git with source URLs and retrieval times.
- Compared every source row in 2024-25 and partial 2025-26 by date/home/away and reconstructed scores.
- 2024-25: all 1,321 completed reference games matched source identities; 1,319 rows passed,
  two had score disagreements, and five additional source rows lacked matching completed games
  and contained invalid scores. All seven are quarantined with original records and reasons.
- 2025-26: 554 rows passed through January 7, 2026. All 768 missing reference games occur after
  that cutoff. No missing games were found inside the source date span in this reference.
- Output canonical game and separate quote JSONL files, preserving unknown price provenance,
  neutral-site information and namespaced team IDs. Existing output runs cannot be overwritten.
- 18 local tests pass, including an end-to-end importer test and reference hash-tampering test.
- Aggregate report: docs/reports/recent-validation.json. No raw datasets redistributed.

## Completed baseline research (2026-10-08)
- Froze docs/BASELINE_PROTOCOL.md before evaluating any model: 2023-24 warm-up,
  2024-25 development, 2025-26 holdout remains unscored.
- Collected 90 older reference responses and validated the 2023-24 source table:
  1,253 matched rows, two quarantines, 66 missing reference games. Used all 1,319
  completed reference games to warm up Elo; historical odds are not training inputs.
- Implemented daily-batched Elo with fixed settings, constant probability baselines,
  calibration, log loss, Brier score and paired day-cluster bootstrap intervals.
- On 1,319 development games, Elo accuracy 65.05%, log loss 0.61895, Brier 0.21554.
  Market reference: 69.14%, 0.58624, 0.20133. Elo does not beat this market benchmark.
- Reproduced predictions exactly at the published implementation commit. 26 tests passed.
- Full interpretation in docs/BASELINE_RESULTS.md; aggregate report in docs/reports/baseline-v1.json.

## Next milestone: features and application foundation
1. Establish permitted dataset use before integrating these third-party odds in a distributed product.
2. Independently verify price samples and identify a source for the missing 2026 odds; do not
   reconstruct historical prices from final results or fill gaps with invented values.
3. Define a new experiment with historically available lagged strength, rest and performance
   features; compare a regularized model with the fixed baseline, preserving the holdout.
4. Build a local research API and UI that clearly displays experimental probabilities,
   source freshness and validation status. Live prices require a separate adapter.

## Research milestone
- Pre-register time splits after establishing trustworthy coverage. Preserve the latest usable
  interval for final evaluation; do not tune against it repeatedly.
- Start with a constant/home-advantage baseline and chronological Elo; then compare a
  regularized model using lagged strength/rest features. Fit preprocessing on training data only.
- Market baseline uses matched two-way prices; closing quotes are only a retrospective benchmark
  when historical availability is unknown. Do not call that an executable betting backtest.
- Report log loss, Brier score, calibration, uncertainty and season-level results.
- Log data hash, code commit, configuration and full experiment results for every model run.

## Application milestone
- After data validation: Python service, small web interface, SQLite storage for local development.
- Game view: model probability, market estimate, best price, data freshness, provenance.
- Add provider adapters and scheduled collection; free API limits and storage terms govern frequency.
- Same event, market, rules and quote freshness required for comparisons.
- Paper predictions stored before outcomes are known; results cannot be overwritten silently.
- Load and reliability tests, outage handling, accessibility and independent review before public beta.

## Not implemented
Production model, live feed, user interface, accounts, alerts, billing, deployment and execution.
No profitability claims. Experimental development metrics are recorded above. No subscription
purchased. Raw data and per-game predictions remain local and Git-ignored.
