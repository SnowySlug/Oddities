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

## Next milestone: baseline research
1. Establish permitted dataset use before integrating these third-party odds in a distributed product.
2. Independently verify price samples and identify a source for the missing 2026 odds; do not
   reconstruct historical prices from final results or fill gaps with invented values.
3. Expand independent result validation to older training seasons. Resolve aliases explicitly.
4. Freeze the research protocol and data inclusion manifest before tuning any model.
5. Build chronological baseline models using verified past results. Unknown quote times prevent
   executable betting backtests; retrospective probability comparisons remain a separate exercise.

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
Trained predictions, live feed, user interface, accounts, alerts, billing, deployment and execution.
No accuracy or profitability claims. No subscription purchased. Research data remains local.
