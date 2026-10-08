"""Inspect selected recent tables without modifying the third-party SQLite file.

Usage: python scripts/audit_recent.py path/to/OddsData.sqlite
Outputs aggregate metadata only; raw data is not redistributed.
"""

from collections import Counter
from datetime import date
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import sqlite3
import sys


def main():
    path = Path(sys.argv[1]).resolve()
    results = {}
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as connection:
        connection.execute('PRAGMA query_only = ON')
        connection.row_factory = sqlite3.Row
        tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in ('odds_2022-23_new', '2023-24', '2024-25', 'odds_2025-26'):
            if table not in tables:
                results[table] = {'missing_table': True}
                continue
            # Identifiers come only from the fixed allowlist above.
            rows = list(connection.execute(f'SELECT * FROM "{table}"'))
            dates, findings, keys = [], Counter(), []
            for row in rows:
                try:
                    dates.append(date.fromisoformat(row['Date']).isoformat())
                except (ValueError, TypeError):
                    findings['invalid_date'] += 1
                keys.append((row['Date'], row['Home'], row['Away']))
                try:
                    odds = [float(row[k]) for k in ('ML_Home', 'ML_Away')]
                    if any(not isfinite(x) or abs(x) < 100 for x in odds):
                        raise ValueError
                except (ValueError, TypeError):
                    findings['invalid_moneyline'] += 1
                try:
                    points, margin = float(row['Points']), float(row['Win_Margin'])
                    if (not isfinite(points) or not isfinite(margin) or points <= 0
                            or margin == 0 or abs(margin) >= points
                            or points != int(points) or margin != int(margin)
                            or (points + margin) % 2):
                        raise ValueError
                except (ValueError, TypeError):
                    findings['score_review'] += 1
            results[table] = {
                'rows': len(rows), 'date_min': min(dates) if dates else None,
                'date_max': max(dates) if dates else None,
                'duplicate_game_keys': sum(n-1 for n in Counter(keys).values()),
                'findings': dict(findings),
                'columns': list(rows[0].keys()) if rows else [],
            }
    print(json.dumps({
        'source_commit': '8e36b0b72ecc5082aa8976dff742cdf910b3aa36',
        'sha256': sha256(path.read_bytes()).hexdigest(),
        'tables': results,
        'limitations': [
            'Partial schema and plausibility checks only; not a completeness or accuracy certification.',
            'Tables overlap; never concatenate all database tables.',
            'No quote timestamp or bookmaker column in inspected tables.',
            'Source provenance and reuse permissions need review before product integration.',
        ],
    }, indent=2))


if __name__ == '__main__':
    main()
