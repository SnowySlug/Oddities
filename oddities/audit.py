"""Read-only structural and plausibility audit of the SBR NBA JSON archive.

These checks identify problems, not authenticity or completeness. No repair
or row exclusion happens silently. Thresholds are review heuristics.
"""

from collections import Counter, defaultdict
from datetime import datetime
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path

from .odds import implied_probability


def audit_file(path: str | Path) -> dict:
    raw = Path(path).read_bytes()
    rows = json.loads(raw)
    if not isinstance(rows, list) or not rows:
        raise ValueError("Expected a nonempty JSON list of game records")
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("Every game record must be an object")
    findings = defaultdict(list)
    dates, keys, seasons = [], [], Counter()
    fields = set()

    for index, row in enumerate(rows):
        fields.update(row)
        seasons[str(row.get("season", "missing"))] += 1
        valid_date = None
        try:
            n = float(row["date"])
            if not isfinite(n) or n != int(n):
                raise ValueError
            valid_date = datetime.strptime(str(int(n)), "%Y%m%d").date().isoformat()
            dates.append(valid_date)
        except (KeyError, TypeError, ValueError, OverflowError):
            findings["invalid_date"].append(index)
        home, away = row.get("home_team"), row.get("away_team")
        valid_teams = all(isinstance(t, str) and t.strip() for t in (home, away))
        if not valid_teams or home == away:
            findings["invalid_team_pair"].append(index)
        if valid_date and valid_teams:
            keys.append((valid_date, home, away))
        try:
            h = implied_probability(row.get("home_close_ml"))
            a = implied_probability(row.get("away_close_ml"))
            if not 1 <= h + a <= 1.20:
                findings["moneyline_overround_review"].append(index)
        except ValueError:
            findings["invalid_moneyline"].append(index)
        try:
            scores = [float(row[k]) for k in ("home_final", "away_final")]
            if any(not isfinite(s) or s <= 0 or s != int(s) for s in scores):
                raise ValueError
            if scores[0] == scores[1]:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            findings["invalid_final_score"].append(index)
        for key in ("home_open_spread", "home_close_spread", "home_2H_spread"):
            try:
                v = float(row[key])
                if not isfinite(v) or abs(v) > 50:
                    raise ValueError
            except (KeyError, TypeError, ValueError):
                findings[f"{key}_review"].append(index)
        for key in ("open_over_under", "close_over_under"):
            try:
                v = float(row[key])
                if not isfinite(v) or not 100 <= v <= 350:
                    raise ValueError
            except (KeyError, TypeError, ValueError):
                findings[f"{key}_review"].append(index)

    return {
        "sha256": sha256(raw).hexdigest(),
        "rows": len(rows),
        "date_min": min(dates) if dates else None,
        "date_max": max(dates) if dates else None,
        "season_counts": dict(sorted(seasons.items())),
        "duplicate_game_keys": sum(n - 1 for n in Counter(keys).values()),
        "fields": sorted(fields),
        "findings": {
            name: {"count": len(indices), "first_row_indices": indices[:10]}
            for name, indices in sorted(findings.items())
        },
        "limitations": [
            "Row indices are zero-based. Threshold failures require review, not automatic repair.",
            "No external schedule, team identity or score verification performed.",
            "No bookmaker identity, quote timestamp or executable-price evidence in this schema.",
            "Closing moneylines must not be represented as earlier available prices.",
            "Passing these checks does not certify a record as accurate or usable.",
        ],
    }
