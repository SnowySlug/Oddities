"""Reconcile recent source rows with independently collected game results.

Accepted rows are research candidates, not licensed product data or executable odds.
Unknown quote timing and bookmaker identity remain null.
"""
from collections import Counter
from datetime import date, datetime
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo

from .odds import implied_probability

TABLES = {'2024-25': 2025, 'odds_2025-26': 2026}
EASTERN = ZoneInfo('America/New_York')


def number(value):
    if isinstance(value, bool):
        raise ValueError('Boolean numeric input')
    n = float(value)
    if not isfinite(n):
        raise ValueError('Nonfinite numeric input')
    return n


def score(value):
    if isinstance(value, dict):
        value = value.get('value')
    n = number(value)
    if n <= 0 or n != int(n):
        raise ValueError('Invalid final score')
    return int(n)


def reference_game(event):
    c = event['competitions'][0]
    if not c['status']['type']['completed']:
        return None
    competitors = {t['homeAway']: t for t in c['competitors']}
    if set(competitors) != {'home', 'away'} or len(c['competitors']) != 2:
        raise ValueError('Expected exactly two competitors')
    h, a = competitors['home'], competitors['away']
    tipoff = datetime.fromisoformat(c['date'].replace('Z', '+00:00'))
    if tipoff.tzinfo is None:
        raise ValueError('Reference tipoff lacks timezone')
    hs, aws = score(h['score']), score(a['score'])
    if hs == aws:
        raise ValueError('Final NBA score is tied')
    return {
        'game_id': 'espn:nba:' + str(event['id']),
        'game_date': tipoff.astimezone(EASTERN).date().isoformat(),
        'tipoff_utc': tipoff.isoformat(),
        'home_team_id': 'espn:nba:team:' + str(h['team']['id']),
        'away_team_id': 'espn:nba:team:' + str(a['team']['id']),
        'home_name': h['team']['displayName'], 'away_name': a['team']['displayName'],
        'home_score': hs, 'away_score': aws,
        'neutral_site': c.get('neutralSite'),
    }


def game_key(game):
    return game['game_date'], game['home_name'], game['away_name']


def load_reference(folder, season):
    folder = Path(folder)
    teams = json.loads((folder / 'teams.json').read_text())
    ids = sorted({str(t['team']['id']) for t in teams['sports'][0]['leagues'][0]['teams']})
    if len(ids) != 30:
        raise ValueError('Reference team inventory must contain 30 NBA teams')
    games, manifest, ignored, conflicts = {}, [], Counter(), set()
    for kind in (2, 3, 5):
        for team in ids:
            path = folder / f'{season}-{kind}-{team}.json'
            raw = path.read_bytes()  # Missing requests fail the report, never imply coverage.
            p = json.loads(raw)
            meta = json.loads(path.with_suffix('.meta.json').read_text())
            digest = sha256(raw).hexdigest()
            if meta['sha256'] != digest:
                raise ValueError(f'Cache hash mismatch: {path.name}')
            manifest.append({'file': path.name, **meta})
            for event in p['events']:
                event_season = event.get('season', {}).get('year')
                event_type = event.get('seasonType', {}).get('type')
                if event_season != season or event_type not in (2, 3, 5):
                    ignored['wrong_season_or_type'] += 1
                    continue
                try:
                    g = reference_game(event)
                except (KeyError, ValueError, TypeError, IndexError):
                    ignored['malformed_event'] += 1
                    continue
                if g is None:
                    ignored['not_completed'] += 1
                    continue
                gid = g['game_id']
                if gid in games and games[gid] != g:
                    conflicts.add(gid)
                games[gid] = g
    if conflicts:
        raise ValueError(f'Conflicting team schedule copies: {sorted(conflicts)}')
    return list(games.values()), manifest, dict(ignored)


def reconcile(rows, reference):
    """Return accepted game/quote pairs, per-row quarantine and coverage summary."""
    ref_by_key = {}
    for g in reference:
        k = game_key(g)
        if k in ref_by_key:
            raise ValueError(f'Ambiguous reference game key: {k}')
        ref_by_key[k] = g
    counts = Counter((r.get('Date'), r.get('Home'), r.get('Away')) for r in rows)
    accepted, quarantine, matched = [], [], set()
    for index, row in enumerate(rows):
        reasons = []
        k = row.get('Date'), row.get('Home'), row.get('Away')
        if counts[k] > 1:
            reasons.append('duplicate_source_game')
        try:
            date.fromisoformat(row['Date'])
        except (KeyError, TypeError, ValueError):
            reasons.append('invalid_date')
        g = ref_by_key.get(k)
        if g is None:
            reasons.append('no_exact_reference_match')
        else:
            matched.add(g['game_id'])
        try:
            hml, aml = number(row['ML_Home']), number(row['ML_Away'])
            overround = implied_probability(hml) + implied_probability(aml)
            if not 1 <= overround <= 1.20:
                reasons.append('moneyline_overround_review')
        except (KeyError, TypeError, ValueError):
            reasons.append('invalid_moneyline')
        try:
            points, margin = number(row['Points']), number(row['Win_Margin'])
            hs, aws = score((points + margin) / 2), score((points - margin) / 2)
            if hs == aws:
                raise ValueError('Tied final')
            if g and (hs, aws) != (g['home_score'], g['away_score']):
                reasons.append('reference_score_mismatch')
        except (KeyError, TypeError, ValueError):
            reasons.append('invalid_final_score')
        if reasons:
            quarantine.append({'source_row_index': index, 'game_key': list(k),
                               'reasons': reasons, 'raw_record': row})
            continue
        accepted.append({
            'game': dict(g),
            'quote': {
                'game_id': g['game_id'], 'market': 'moneyline',
                'home_american': hml, 'away_american': aml,
                'bookmaker': None, 'observed_at': None, 'quote_phase': 'unknown',
                'settlement_rules': None, 'executable_backtest_eligible': False,
                'validation_status': 'results_matched_prices_unverified',
                'reuse_status': 'pending_data_rights_review',
            },
            'source_row_index': index,
            'status': 'research_candidate_pending_data_rights_review',
        })
    reason_counts = Counter(reason for r in quarantine for reason in r['reasons'])
    source_dates = sorted(r['Date'] for r in rows if isinstance(r.get('Date'), str)
                          and len(r['Date']) == 10)
    first, last = (source_dates[0], source_dates[-1]) if source_dates else (None, None)
    missing = [g for g in reference if g['game_id'] not in matched]
    return accepted, quarantine, {
        'source_rows': len(rows), 'reference_completed_games': len(reference),
        'matched_source_games': len(matched), 'accepted_research_rows': len(accepted),
        'quarantined_rows': len(quarantine), 'reason_counts': dict(reason_counts),
        'source_date_min': first, 'source_date_max': last,
        'missing_reference_games': len(missing),
        'missing_within_source_date_span': sum(first <= g['game_date'] <= last for g in missing) if first else 0,
        'missing_after_source_date_span': sum(g['game_date'] > last for g in missing) if last else 0,
        'missing_before_source_date_span': sum(g['game_date'] < first for g in missing) if first else 0,
        'missing_reference_ids': sorted(g['game_id'] for g in missing),
        'accepted_date_min': min((x['game']['game_date'] for x in accepted), default=None),
        'accepted_date_max': max((x['game']['game_date'] for x in accepted), default=None),
        'limitations': [
            'Exact date/home/away matching only; no fuzzy identity or date repair.',
            'Source date is interpreted as America/New_York game date for this comparison.',
            'Coverage is relative to collected completed ESPN regular/playoff/play-in events, not certified league completeness.',
            'Prices were checked for numerical plausibility only, not independently verified.',
            'Unknown sportsbook, quote timing and settlement rules prohibit executable historical-price claims.',
            'Accepted denotes structural/result checks only, not permission for product use.',
        ],
    }


def normalize_database(database, reference_folder, output):
    database, output = Path(database).resolve(), Path(output)
    if output.exists():
        raise ValueError('Output already exists; use a new run directory to preserve prior results')
    # Validate all inputs before creating output.
    source_hash = sha256(database.read_bytes()).hexdigest()
    batches = []
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as con:
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA query_only = ON')
        for table, year in TABLES.items():
            rows = [dict(r) for r in con.execute(f'SELECT * FROM "{table}" ORDER BY rowid')]
            reference, provenance, ignored = load_reference(reference_folder, year)
            accepted, quarantine, report = reconcile(rows, reference)
            report.update(source_table=table, source_sha256=source_hash,
                          reference_responses=provenance, reference_ignored=ignored)
            batches.append((table, accepted, quarantine, report))
    output.mkdir(parents=True)
    summary = {}
    for table, accepted, quarantine, report in batches:
        folder = output / table
        folder.mkdir()
        for filename, objects in [('games.jsonl', [r['game'] for r in accepted]),
                                  ('quotes.jsonl', [dict(r['quote'], source_sha256=source_hash,
                                                       source_table=table, source_row_index=r['source_row_index']) for r in accepted]),
                                  ('quarantine.jsonl', quarantine)]:
            (folder / filename).write_text(''.join(json.dumps(json_safe(r), allow_nan=False) + '\n' for r in objects))
        (folder / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False))
        summary[table] = {k: v for k, v in report.items()
                          if k not in ('reference_responses', 'missing_reference_ids')}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False))
    return summary


def json_safe(value):
    """Preserve invalid nonfinite raw values as explicit tagged evidence."""
    if isinstance(value, float) and not isfinite(value):
        return {'invalid_nonfinite_number': repr(value)}
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value
