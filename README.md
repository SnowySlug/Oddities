# Oddities

Sports probability research and odds comparison, starting with NBA pregame moneylines.

**Status: research foundation.** No trained model, live feed or web app yet. Current development
requires no paid services or API key. The core uses Python's standard library;
date reconciliation also requires an IANA timezone database (see Windows note below).

## Run locally

Python 3.11 or newer, from this repository's root:

```sh
python -m oddities demo
python -m unittest discover -s tests -v
```

On Windows/PyCharm, if `America/New_York` timezone data is unavailable, install it in
the project's interpreter with `python -m pip install tzdata`.

## Reconcile recent data

With the pinned third-party odds file saved as `data/raw/OddsData.sqlite` (see the
source register for its URL), collect reference schedules and run:

```sh
python scripts/fetch_reference.py --seasons 2025 2026
python -m oddities normalize data/raw/OddsData.sqlite data/raw/espn data/processed/run-001
```

This makes up to 181 initial public ESPN requests (team inventory plus 30 teams,
three competition categories and two seasons), with two concurrent requests.
Completed requests are cached. Re-running resumes from cache; failed or incomplete
reference collections must be resolved before normalization. Endpoints may change.
It checks regular-season, playoff and play-in results. It does not collect odds.

Each source table produces separate game and quote files, a quarantine with reasons,
and a provenance/coverage report. Use a new output directory per run. Raw data and
normalized datasets remain ignored by Git. Passing validation does not establish
data reuse rights or executable historical prices.

The demo uses explicitly synthetic probabilities and odds. It demonstrates the calculation flow,
not a prediction or a betting recommendation.

## Included

- American odds conversion, break-even probability and proportional two-way de-vig.
- Model-based expected return and idealized two-way arbitrage calculations.
- Fail-closed validation of invalid numeric inputs.
- Read-only audits of free historical NBA data, with reproducible aggregate reports.

## Data and next steps

See [data sources and findings](docs/DATA_SOURCES.md), [development plan](docs/PLAN.md),
and [engineering instructions](AGENTS.md).

The older archive has data-quality issues. A newer database includes 2024-25 and partial 2025-26
records, but still requires verification of coverage, provenance and permitted use. Neither source
has been approved for training or treated as proof of executable historical prices.

Raw data, credentials and model binaries stay out of Git. No open-source license has been selected.
