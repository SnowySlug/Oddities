"""Cache ESPN team schedules for independent result checks, not odds.

Run: python scripts/fetch_reference.py --seasons 2025 2026
Uses public endpoints without authentication. Service availability/terms may change.
Two concurrent requests, immutable local cache, explicit failures; no live scheduler.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import json
from pathlib import Path
from urllib.request import Request, urlopen

BASE = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba'


def fetch(url, path):
    if path.exists():
        return json.loads(path.read_text())
    with urlopen(Request(url, headers={'User-Agent': 'OdditiesResearch/0.1'}), timeout=30) as response:
        raw = response.read()
    if raw.startswith(b'\x1f\x8b'):
        raw = gzip.decompress(raw)
    payload = json.loads(raw)
    if 'code' in payload and payload['code'] != 200:
        raise ValueError(f'Provider error: {payload}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    path.with_suffix('.meta.json').write_text(json.dumps({
        'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
        'sha256': sha256(raw).hexdigest(),
    }, indent=2))
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seasons', nargs='+', type=int, required=True)
    parser.add_argument('--types', nargs='+', type=int, choices=(2, 3, 5), default=[2, 3, 5],
                        help='2 regular, 3 playoffs, 5 play-in')
    parser.add_argument('--output', type=Path, default=Path('data/raw/espn'))
    args = parser.parse_args()
    teams = fetch(BASE + '/teams?limit=100', args.output / 'teams.json')
    ids = sorted({t['team']['id'] for t in teams['sports'][0]['leagues'][0]['teams']})
    if len(ids) != 30:
        raise ValueError(f'Expected 30 NBA teams, got {len(ids)}; review scope')
    tasks = [(year, kind, team) for year in args.seasons for kind in args.types for team in ids]

    def one(task):
        year, kind, team = task
        url = f'{BASE}/teams/{team}/schedule?season={year}&seasontype={kind}'
        path = args.output / f'{year}-{kind}-{team}.json'
        p = fetch(url, path)
        if not isinstance(p.get('events'), list):
            raise ValueError(f'No events list in {path}')
        # Persist empty postseason responses too; not every team qualifies.
        return {'season': year, 'type': kind, 'team': team, 'events': len(p['events'])}

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(one, tasks))
    print(json.dumps({'requests': len(tasks), 'responses': results}, indent=2))


if __name__ == '__main__':
    main()
