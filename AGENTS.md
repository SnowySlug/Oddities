# Oddities engineering instructions

## Product and scope
- $0 proof of concept: NBA pregame moneylines, probability research, odds comparison, paper tracking.
- Repository is intentionally public. No paid services or subscriptions have been authorized.
- Current milestone is the research foundation. Do not describe it as a working live app.
- Consult docs/PLAN.md and docs/DATA_SOURCES.md before expanding scope.

## Development
- Python 3.11+; current core uses the standard library. Date reconciliation requires
  IANA timezone data; install `tzdata` where the operating system does not supply it.
- Verify with `python -m unittest discover -s tests -v` and `python -m oddities demo`.
- Keep mathematical calculations independent of data providers and user interfaces.
- Make changes on focused branches. Do not merge or deploy without instruction.
- Run relevant tests before committing; tests must cover meaningful failure modes.

## Data and research integrity
- Never commit API keys, credentials, raw third-party datasets or trained binary artifacts.
- Document source URL, version/hash, retrieval date, schema, timing semantics and limitations.
- Unknown bookmaker, timestamp, settlement rule or team identity stays unknown. Never fabricate it.
- Audit and quarantine invalid records explicitly. Do not silently repair or discard data.
- Preserve untouched chronological evaluation periods; avoid random train/test splits of games.
- All features must be available at prediction time. Final scores are labels, not predictors.
- Compare models with simple baselines and market probabilities; report log loss, Brier score,
  calibration, sample size and uncertainty. Accuracy and a profitable backtest alone are insufficient.
- Synthetic demos must remain visibly labeled. No invented accuracy, profit, live status or history.
- A proportional de-vig estimate is not the true probability. A model EV estimate is not a guarantee.
- Arbitrage calculations do not establish executable profits; account for matched markets,
  timestamps, fees, limits, rounding and settlement rules before presenting actionable signals.

## Continuity
- Record completed work and concrete remaining blockers in docs/PLAN.md.
- Keep reports reproducible from documented commands. No raw-data redistribution by default.
