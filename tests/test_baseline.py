import copy
from math import log
import unittest

from oddities.baseline import Elo, EloConfig, metrics, paired_day_bootstrap


def game(gid, day, home='H', away='A', hs=100, aws=90, neutral=False):
    return {'game_id': gid, 'game_date': day, 'home_team_id': home,
            'away_team_id': away, 'home_score': hs, 'away_score': aws,
            'neutral_site': neutral}


class BaselineTests(unittest.TestCase):
    def test_current_and_future_outcomes_do_not_change_earlier_forecasts(self):
        games = [game('1','2024-01-01'), game('2','2024-01-02'), game('3','2024-01-03')]
        before = Elo().process(games)
        modified = copy.deepcopy(games)
        modified[1].update(home_score=80, away_score=110)
        modified[2].update(home_score=80, away_score=110)
        after = Elo().process(modified)
        self.assertEqual([x['elo'] for x in before[:2]], [x['elo'] for x in after[:2]])
        self.assertNotEqual(before[2]['elo'], after[2]['elo'])

    def test_same_day_batch_is_order_invariant(self):
        games = [game('1','2024-01-01'),game('2','2024-01-01',away='B')]
        a,b = Elo(),Elo()
        first,second = a.process(games),b.process(list(reversed(games)))
        self.assertEqual(first,second)
        self.assertEqual(first[0]['elo'],first[1]['elo'])
        self.assertEqual(a.ratings,b.ratings)

    def test_processed_dates_and_ids_cannot_be_replayed(self):
        model = Elo(); model.process([game('1','2024-01-01')])
        for g in [game('2','2024-01-01'),game('1','2024-01-02'),game('3','2023-12-31')]:
            with self.assertRaises(ValueError): model.process([g])

    def test_no_home_bonus_for_neutral_or_unknown_venue(self):
        model=Elo()
        self.assertEqual(model.forecast('H','A',True),.5)
        self.assertEqual(model.forecast('H','A',None),.5)
        self.assertGreater(model.forecast('H','A',False),.5)

    def test_rating_conservation_and_offseason_regression(self):
        model=Elo(); model.process([game('1','2024-01-01')])
        self.assertAlmostEqual(sum(model.ratings.values()),3000)
        before=model.rating('H'); model.regress()
        self.assertAlmostEqual(model.rating('H'),1500+.75*(before-1500))

    def test_invalid_games_and_config_fail(self):
        for changes in [dict(home_score=0),dict(home_score=90),dict(home_score=float('nan')),
                        dict(home_team_id='A')]:
            g=game('1','2024-01-01');g.update(changes)
            with self.assertRaises(ValueError): Elo().process([g])
        g=game('1','2024-01-01')
        with self.assertRaises(ValueError): Elo().process([g,g])
        with self.assertRaises(ValueError): EloConfig(scale=0)

    def test_metrics_have_known_coin_flip_values(self):
        rows=[{'home_win':y,'p':.5} for y in [0,1,1,0]]
        m=metrics(rows,'p')
        self.assertAlmostEqual(m['log_loss'],log(2))
        self.assertEqual(m['brier_score'],.25)
        self.assertEqual(m['accuracy'],.5)
        self.assertEqual(m['calibration'][0]['count'],4)
        self.assertLess(m['calibration'][0]['observed_rate_wilson95'][0],.5)
        self.assertGreater(m['calibration'][0]['observed_rate_wilson95'][1],.5)
        with self.assertRaises(ValueError):metrics([],'p')
        with self.assertRaises(ValueError):metrics([{'home_win':1,'p':float('nan')}],'p')

    def test_paired_cluster_intervals_reproducible_and_zero_for_equal_predictions(self):
        rows=[{'game_date':f'2024-01-0{i+1}','home_win':i%2,'a':.6,'b':.6} for i in range(4)]
        first=paired_day_bootstrap(rows,'a','b',draws=100)
        self.assertEqual(first,paired_day_bootstrap(rows,'a','b',draws=100))
        self.assertEqual(first['log_loss']['percentile95'],[0,0])
        self.assertEqual(first['brier_score']['difference'],0)
        self.assertEqual(first['day_clusters'],4)
