"""Run the fixed v1 protocol, without loading the 2025-26 holdout.

python scripts/run_baseline.py --reference data/raw/espn \
    --validated data/processed/recent-001/2024-25 --output artifacts/baseline-v1
"""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from oddities.baseline import Elo, EloConfig, metrics, paired_day_bootstrap
from oddities.normalize import load_reference
from oddities.odds import proportional_devig


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--validated', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; preserve prior experiments')
    train, train_manifest, train_ignored = load_reference(args.reference, 2024)
    development, dev_manifest, dev_ignored = load_reference(args.reference, 2025)
    if not train or not development or max(g['game_date'] for g in train) >= min(g['game_date'] for g in development):
        raise ValueError('Training and development periods must be nonempty and ordered')
    matched_games = read_rows(args.validated / 'games.jsonl')
    quote_rows = read_rows(args.validated / 'quotes.jsonl')
    quotes = {r['game_id']: r for r in quote_rows}
    included = {g['game_id']: g for g in matched_games}
    if len(quotes) != len(quote_rows) or len(included) != len(matched_games):
        raise ValueError('Duplicate normalized game/quote IDs')
    if set(quotes) != set(included):
        raise ValueError('Game and quote IDs differ')
    reference_by_id = {g['game_id']: g for g in development}
    if any(reference_by_id.get(gid) != game for gid, game in included.items()):
        raise ValueError('Validated game differs from the current reference')
    config = EloConfig()
    model = Elo(config)
    model.process(train)
    model.regress()
    home_rate = sum(g['home_score'] > g['away_score'] for g in train)/len(train)
    predictions = model.process(development)
    evaluated = []
    for prediction in predictions:
        gid = prediction['game_id']
        if gid not in included:
            continue
        q = quotes[gid]
        market, _ = proportional_devig(q['home_american'], q['away_american'])
        evaluated.append(dict(prediction, coin_flip=.5, training_home_rate=home_rate, market=market))
    if len(evaluated) != len(included):
        raise ValueError('Not every included game received a prediction')
    root = Path(__file__).resolve().parents[1]
    code_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True).strip():
        raise ValueError('Commit research code before running to make the experiment reproducible')
    report = {
        'experiment': 'baseline-v1', 'created_at': datetime.now(timezone.utc).isoformat(),
        'code_commit': code_commit, 'model_version': 'daily-elo-v1', 'config': asdict(config),
        'protocol_sha256': sha256((root/'docs/BASELINE_PROTOCOL.md').read_bytes()).hexdigest(),
        'training': {'season': '2023-24', 'games': len(train), 'home_win_rate': home_rate,
                     'start': min(g['game_date'] for g in train), 'end': max(g['game_date'] for g in train),
                     'ignored_reference_copies': train_ignored},
        'development': {'season': '2024-25', 'reference_games': len(development),
                        'evaluated_games': len(evaluated), 'excluded_games': len(development)-len(evaluated),
                        'start': min(p['game_date'] for p in evaluated), 'end': max(p['game_date'] for p in evaluated),
                        'ignored_reference_copies': dev_ignored},
        'metrics': {m: metrics(evaluated, m) for m in ('coin_flip','training_home_rate','elo','market')},
        'comparisons': [paired_day_bootstrap(evaluated, 'elo', other) for other in ('market','training_home_rate')],
        'inputs': {p.name: sha256(p.read_bytes()).hexdigest()
                   for p in [args.validated/'games.jsonl', args.validated/'quotes.jsonl']},
        'reference_manifest_sha256': sha256(json.dumps(train_manifest+dev_manifest, sort_keys=True).encode()).hexdigest(),
        'holdout': '2025-26 not loaded or scored by this runner',
        'limitations': [
            'Development evaluation only; fixed parameters, no optimization or final holdout evaluation.',
            'Market probabilities use timing-unverified quotes and may have an information advantage.',
            'No price verification, ROI calculation or executable betting backtest.',
            'Daily bootstrap intervals omit some serial dependence across dates.',
            'Current result snapshots may include retrospective score corrections.',
            'Data reuse rights are unresolved; this is local exploratory research.',
        ],
    }
    args.output.mkdir(parents=True)
    (args.output/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    (args.output/'predictions.jsonl').write_text(''.join(json.dumps(p)+'\n' for p in evaluated))
    (args.output/'reference-manifest.json').write_text(json.dumps(train_manifest+dev_manifest,indent=2))
    print(json.dumps({k: v for k,v in report.items() if k not in ('metrics',)},indent=2))
    print(json.dumps({m: {k:v for k,v in data.items() if k != 'calibration'} for m,data in report['metrics'].items()},indent=2))


if __name__ == '__main__':
    main()
