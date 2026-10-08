# Data source register

Inspected 2026-10-08. Public availability does not establish completeness, accuracy or redistribution rights.
Only aggregate audit reports are checked in; raw files remain outside Git.

## 1. Older SBR-derived NBA JSON

- Repository: https://github.com/flancast90/sportsbookreview-scraper
- Pinned file: https://raw.githubusercontent.com/flancast90/sportsbookreview-scraper/1a820e50c6fbd0276cde073c22bfffae78930868/data/nba_archive_10Y.json
- SHA-256: `0c9858489d224c54dcf2f2d1b70c3a122675381d35ae03ce0a81204f739f0e98`
- Actual coverage: 13,903 rows, 2011-12-25 through 2022-06-13. Season labels 2011-2021.
- Has closing home/away moneylines and final scores; no bookmaker identity or quote timestamps.
- Audit found 11 invalid moneyline rows, 11 invalid final-score rows and 10 invalid team-pair rows.
  Counts overlap. 933 closing-spread values exceed the +/-50 review threshold and 936 totals
  fall outside 100-350. These are review heuristics, not a license to auto-correct values.
- The mismatched spread/total magnitudes suggest parsing errors; moneylines still need independent
  validation even where they pass basic checks. Team-name consistency is not verified.
- Source repository declares MIT for its software. Underlying third-party data reuse needs separate review.
- Status: useful audit fixture and potential older research data; not accepted as clean training data.

Reproduce after downloading the pinned file to `data/raw/nba.json`:

```sh
python -m oddities audit data/raw/nba.json --output docs/reports/sbr-nba-audit.json
```

## 2. More recent NBA odds database

- Repository: https://github.com/kyleskom/NBA-Machine-Learning-Sports-Betting
- Pinned file: https://raw.githubusercontent.com/kyleskom/NBA-Machine-Learning-Sports-Betting/8e36b0b72ecc5082aa8976dff742cdf910b3aa36/Data/OddsData.sqlite
- Actually downloaded and inspected in read-only mode. See `reports/recent-nba-audit.json`.
- Includes a 2024-25 table with 1,326 rows and a 2025-26 table with 554 rows.
- Columns include date, team names, moneylines, spread, total, result and rest days.
- Multiple overlapping legacy/normalized tables exist: never concatenate them all.
- No bookmaker or quote timestamp in inspected tables. Opening/closing timing is not yet established.
- No top-level license was found in the inspected tree. Do not copy its implementation or redistribute
  its dataset without resolving permissions. Local inspection is not acceptance for product use.
- Status: priority candidate for recent research; schedule completeness, source accuracy,
  quote timing and permissions remain unresolved. A partial season is not a full-season evaluation.

```sh
python scripts/audit_recent.py data/raw/OddsData.sqlite > docs/reports/recent-nba-audit.json
```

## 3. Recent snapshots for collection

- The Odds Gap: https://theoddsgap.com/data
- Provider advertises a free rolling seven-day window with timestamped game-line snapshots;
  older history requires a subscription. This has not been ingested or independently verified.
- The Odds API: https://the-odds-api.com/
- Provider advertises 500 free monthly credits without historical access. Not connected.
- Before collecting either: inspect terms for storage/display, validate sample data and coverage,
  track quotas, retain source timestamps and use shared cached pulls.

## Provenance inspection and independent results (2026-10-08)

The pinned newer repository's `src/Process-Data/Get_Odds_Data.py` reads SBR through
`sbrscrape`, selects a sportsbook (default `fanduel`), and saves prices and results.
It does not save a bookmaker identifier, quote timestamp or opening/closing marker.
The current default cannot prove which parameters produced older rows, so the importer
leaves those fields null. No upstream code was copied into Oddities.

An independent results cache is collected from ESPN's public team schedule endpoints:
`https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{id}/schedule?season={year}&seasontype={type}`.
Types 2, 3 and 5 cover regular season, playoffs and play-ins. Completed games are
deduplicated by ESPN event ID; conflicting copies cause failure. Tipoff timestamps
are converted to America/New_York dates for exact source matching. Neutral-site flags
are retained. Team IDs are explicitly namespaced to ESPN, not presented as NBA IDs.

Every cache response includes URL, retrieval timestamp and SHA-256 metadata. Coverage
counts are relative to this collected reference, not a league completeness certification.
The reference is used to check scores and identities only; historical prices remain
independently unverified. No automated fetch job or data redistribution is enabled.

### Reconciliation results

See `reports/recent-validation.json` for source and reference manifest hashes.

| Source table | Source rows | Matched completed games | Passed checks | Quarantined |
|---|---:|---:|---:|---:|
| 2024-25 | 1,326 | 1,321 | 1,319 | 7 |
| odds_2025-26 | 554 | 554 | 554 | 0 |

The seven quarantines comprise two disagreements in reconstructed final scores and five
zero-score rows without a completed reference match on the same date. They are not repaired.
No reference games are missing inside either source's date span. The 2025-26 odds table is
missing 768 completed reference games after 2026-01-07. These counts are relative to the
collected ESPN schedules. Passing checks is not an independent validation of the odds themselves.

## Research boundary

Train on past games, evaluate on later games. Knowing a game's eventual closing odds is not evidence
that those odds were available when an earlier prediction was made. Keep retrospective model
comparisons separate from prospective paper performance. Missing recent data is a documented gap,
not a reason to imply the old archive represents current conditions.
