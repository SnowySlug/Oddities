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

## Next milestone: usable data
1. Prefer recent games: audit 2024-25 and partial 2025-26 first, then older seasons for training.
2. Establish provenance, timing semantics and permitted use for the newer database.
3. Compare coverage against an independent schedule; verify samples of scores and prices.
4. Normalize stable game/team identities; handle relocations, aliases and neutral sites explicitly.
5. Create a canonical game table and separate quote table with nullable unknown timestamps.
6. Produce a quarantine file with a reason per rejected record and an inclusion manifest.

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
