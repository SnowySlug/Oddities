"""Fixed chronological Elo baseline; no outcome or market inputs at prediction time."""
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from itertools import groupby
from math import isfinite, log, sqrt
import random


@dataclass(frozen=True)
class EloConfig:
    initial: float = 1500.0
    scale: float = 400.0
    k: float = 20.0
    home_advantage: float = 65.0
    offseason_retention: float = 0.75

    def __post_init__(self):
        if not all(isfinite(v) for v in asdict(self).values()):
            raise ValueError('Configuration must be finite')
        if self.scale <= 0 or self.k <= 0 or not 0 <= self.offseason_retention <= 1:
            raise ValueError('Invalid Elo configuration')


def validate_games(games):
    seen = set()
    for g in games:
        date.fromisoformat(g['game_date'])
        if g['game_id'] in seen:
            raise ValueError('Duplicate game ID')
        seen.add(g['game_id'])
        if not g['home_team_id'] or not g['away_team_id'] or g['home_team_id'] == g['away_team_id']:
            raise ValueError('Invalid team identity')
        for field in ('home_score', 'away_score'):
            score = g[field]
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                raise ValueError('Invalid score type')
            if not isfinite(score) or score <= 0 or int(score) != score:
                raise ValueError('Invalid final score')
        if g['home_score'] == g['away_score']:
            raise ValueError('Final NBA game cannot be tied')


class Elo:
    def __init__(self, config=EloConfig()):
        self.config = config
        self.ratings = {}
        self.last_date = None
        self.seen_ids = set()

    def rating(self, team):
        return self.ratings.get(team, self.config.initial)

    def regress(self):
        c = self.config
        self.ratings = {t: c.initial + c.offseason_retention * (r - c.initial)
                        for t, r in self.ratings.items()}

    def forecast(self, home_id, away_id, neutral_site):
        c = self.config
        advantage = c.home_advantage if neutral_site is False else 0.0
        difference = self.rating(home_id) - self.rating(away_id) + advantage
        return 1 / (1 + 10 ** (-difference / c.scale))

    def process(self, games):
        """Predict each whole date before observing any outcome on that date.

        Calls must advance by full dates; a repeated date is rejected so splitting
        a daily batch across calls cannot accidentally leak that day's results.
        """
        games = sorted(games, key=lambda g: (g['game_date'], g['game_id']))
        validate_games(games)
        if games and self.last_date and games[0]['game_date'] <= self.last_date:
            raise ValueError('Games must advance beyond the last processed date')
        if any(g['game_id'] in self.seen_ids for g in games):
            raise ValueError('Game ID already processed')
        predictions = []
        for day, batch in groupby(games, key=lambda g: g['game_date']):
            changes = defaultdict(float)
            for g in batch:
                home, away = g['home_team_id'], g['away_team_id']
                p = self.forecast(home, away, g.get('neutral_site'))
                y = int(g['home_score'] > g['away_score'])
                predictions.append({'game_id': g['game_id'], 'game_date': day,
                                    'home_win': y, 'elo': p})
                delta = self.config.k * (y - p)
                changes[home] += delta
                changes[away] -= delta
                self.seen_ids.add(g['game_id'])
            for team, delta in changes.items():
                self.ratings[team] = self.rating(team) + delta
            self.last_date = day
        return predictions


def loss(probability, outcome):
    if not isfinite(probability) or not 0 < probability < 1 or outcome not in (0, 1):
        raise ValueError('Need finite probability strictly inside (0, 1) and binary outcome')
    return -(outcome * log(probability) + (1-outcome) * log(1-probability)), (probability-outcome)**2


def wilson(wins, n):
    z = 1.959963984540054
    p = wins/n
    denominator = 1 + z*z/n
    centre = (p + z*z/(2*n)) / denominator
    radius = z * sqrt(p*(1-p)/n + z*z/(4*n*n)) / denominator
    return [max(0, centre-radius), min(1, centre+radius)]


def metrics(rows, model):
    if not rows:
        raise ValueError('Cannot evaluate zero predictions')
    n = len(rows)
    losses = [loss(r[model], r['home_win']) for r in rows]
    bins = defaultdict(list)
    for row in rows:
        bins[min(9, int(row[model]*10))].append(row)
    calibration = []
    for index, group in sorted(bins.items()):
        wins = sum(r['home_win'] for r in group)
        calibration.append({'lower': index/10, 'upper': (index+1)/10,
                            'count': len(group),
                            'mean_probability': sum(r[model] for r in group)/len(group),
                            'observed_home_win_rate': wins/len(group),
                            'observed_rate_wilson95': wilson(wins, len(group))})
    return {'n': n, 'log_loss': sum(x[0] for x in losses)/n,
            'brier_score': sum(x[1] for x in losses)/n,
            'accuracy': sum((r[model] >= .5) == bool(r['home_win']) for r in rows)/n,
            'home_win_rate': sum(r['home_win'] for r in rows)/n,
            'calibration': calibration}


def paired_day_bootstrap(rows, first, second, draws=2000, seed=20261008):
    if not rows or draws < 2:
        raise ValueError('Need observations and at least two draws')
    grouped = defaultdict(list)
    for row in rows:
        a, b = loss(row[first], row['home_win']), loss(row[second], row['home_win'])
        grouped[row['game_date']].append((a[0]-b[0], a[1]-b[1]))
    clusters = [(len(v), sum(x[0] for x in v), sum(x[1] for x in v))
                for _, v in sorted(grouped.items())]
    rng = random.Random(seed)
    samples = [[], []]
    for _ in range(draws):
        selected = rng.choices(clusters, k=len(clusters))
        count = sum(c[0] for c in selected)
        for metric in (0, 1):
            samples[metric].append(sum(c[metric+1] for c in selected)/count)
    result = {'comparison': first + ' minus ' + second, 'negative_favors': first,
              'draws': draws, 'seed': seed, 'day_clusters': len(clusters)}
    for index, name in enumerate(('log_loss', 'brier_score')):
        ordered = sorted(samples[index])
        result[name] = {
            'difference': sum(c[index+1] for c in clusters)/len(rows),
            'percentile95': [ordered[int(.025*(draws-1))], ordered[int(.975*(draws-1))]],
        }
    return result
