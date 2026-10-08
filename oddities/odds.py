"""Pure calculations for two-outcome markets; no claims about execution."""

from math import isfinite


def _number(value: float) -> float:
    if isinstance(value, bool):
        raise ValueError("Boolean is not a price or probability")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Expected a finite number") from exc
    if not isfinite(result):
        raise ValueError("Expected a finite number")
    return result


def american_to_decimal(price: float) -> float:
    """Accept conventional American odds >= +100 or <= -100."""
    price = _number(price)
    if abs(price) < 100:
        raise ValueError("American odds must be >= 100 or <= -100")
    return 1 + (price / 100 if price > 0 else 100 / -price)


def implied_probability(price: float) -> float:
    return 1 / american_to_decimal(price)


def proportional_devig(home: float, away: float) -> tuple[float, float]:
    """Normalize a matched two-way quote. This is an estimate, not truth.

    Caller must ensure same event, bookmaker, time and settlement rules.
    """
    h, a = implied_probability(home), implied_probability(away)
    return h / (h + a), a / (h + a)


def expected_return(probability: float, price: float) -> float:
    """Expected net return per dollar at given probability; excludes fees."""
    probability = _number(probability)
    if not 0 <= probability <= 1:
        raise ValueError("Probability must be between 0 and 1")
    return probability * american_to_decimal(price) - 1


def two_way_arbitrage(home: float, away: float) -> dict | None:
    """Idealized stake fractions for exhaustive, mutually exclusive outcomes.

    No fees, rounding, limits, price changes, voids or execution are modeled.
    Returns None when the inverse-price sum is >= 1.
    """
    h, a = implied_probability(home), implied_probability(away)
    total = h + a
    if total >= 1:
        return None
    return {
        "home_stake_fraction": h / total,
        "away_stake_fraction": a / total,
        "theoretical_return": 1 / total - 1,
    }
