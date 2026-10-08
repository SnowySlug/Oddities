import json
from pathlib import Path
import tempfile
import unittest

from oddities.audit import audit_file


def sample():
    # Original synthetic fixture; not a copied game record.
    return dict(season=2020, date=20210101, home_team='Home', away_team='Away',
                home_close_ml=-110, away_close_ml=-110, home_final='100', away_final='99',
                home_open_spread=-1, home_close_spread=-1, home_2H_spread=-1,
                open_over_under=200, close_over_under=200)


class AuditTests(unittest.TestCase):
    def run_audit(self, rows):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'sample.json'
            path.write_text(json.dumps(rows))
            before = path.read_bytes()
            report = audit_file(path)
            self.assertEqual(path.read_bytes(), before)
            return report

    def test_clean_schema_and_duplicate_detection(self):
        result = self.run_audit([sample(), sample()])
        self.assertEqual(result['findings'], {})
        self.assertEqual(result['duplicate_game_keys'], 1)
        self.assertEqual(result['date_min'], '2021-01-01')

    def test_suspect_values_are_reported_not_repaired(self):
        row = sample()
        row.update(home_close_spread=178, close_over_under=4, home_close_ml=0,
                   date=20210230, home_final='0')
        report = self.run_audit([row])
        for key in ('home_close_spread_review', 'close_over_under_review',
                    'invalid_moneyline', 'invalid_date', 'invalid_final_score'):
            self.assertEqual(report['findings'][key]['count'], 1)
        self.assertIsNone(report['date_min'])

    def test_unexpected_structure_rejected(self):
        for rows in ([], {}, [None]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                self.run_audit(rows)
