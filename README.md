# Oddities

Sports probability research and odds comparison, starting with NBA pregame moneylines.

**Status: research foundation.** No trained model, live feed or web app yet. Current development
requires no paid services, API key or third-party Python packages.

## Run locally

Python 3.11 or newer, from this repository's root:

```sh
python -m oddities demo
python -m unittest discover -s tests -v
```

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
