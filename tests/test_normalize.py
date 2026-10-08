import copy
import json
from hashlib import sha256
from pathlib import Path
import sqlite3
import tempfile
import unittest

from oddities.normalize import reconcile, reference_game, json_safe, normalize_database


def event():
    return {'id': 'test-1', 'competitions': [{
        'date': '2025-01-02T01:00Z', 'neutralSite': False,
        'status': {'type': {'completed': True}},
        'competitors': [
            {'homeAway': 'home', 'team': {'id': '1', 'displayName': 'Home'}, 'score': {'value': 101}},
            {'homeAway': 'away', 'team': {'id': '2', 'displayName': 'Away'}, 'score': {'value': 99}},
        ],
    }]}


def row():
    return {'Date': '2025-01-01', 'Home': 'Home', 'Away': 'Away',
            'ML_Home': -110, 'ML_Away': -110, 'Points': 200, 'Win_Margin': 2}


class NormalizeTests(unittest.TestCase):
    def setUp(self):
        self.reference = [reference_game(event())]

    def test_utc_midnight_does_not_shift_us_game_date(self):
        self.assertEqual(self.reference[0]['game_date'], '2025-01-01')
        self.assertEqual(self.reference[0]['game_id'], 'espn:nba:test-1')

    def test_verified_score_and_unknown_quote_provenance(self):
        rows = [row()]
        original = copy.deepcopy(rows)
        accepted, rejected, report = reconcile(rows, self.reference)
        self.assertEqual(rows, original)
        self.assertEqual(len(accepted), 1)
        self.assertEqual(rejected, [])
        self.assertIsNone(accepted[0]['quote']['bookmaker'])
        self.assertIsNone(accepted[0]['quote']['observed_at'])
        self.assertFalse(accepted[0]['quote']['executable_backtest_eligible'])
        self.assertEqual(report['missing_reference_games'], 0)

    def test_score_mismatch_is_quarantined_without_repair(self):
        r = row(); r['Win_Margin'] = 4
        accepted, rejected, _ = reconcile([r], self.reference)
        self.assertFalse(accepted)
        self.assertIn('reference_score_mismatch', rejected[0]['reasons'])
        self.assertEqual(rejected[0]['raw_record']['Win_Margin'], 4)

    def test_all_duplicate_copies_quarantined(self):
        accepted, rejected, _ = reconcile([row(), row()], self.reference)
        self.assertEqual(len(rejected), 2)
        self.assertFalse(accepted)
        self.assertIn('duplicate_source_game', rejected[0]['reasons'])

    def test_invalid_prices_scores_and_unknown_teams(self):
        for field, value, reason in [('ML_Home', 0, 'invalid_moneyline'),
                                     ('ML_Away', float('inf'), 'invalid_moneyline'),
                                     ('Points', 0, 'invalid_final_score'),
                                     ('Points', 201, 'invalid_final_score'),
                                     ('Home', 'Unresolved', 'no_exact_reference_match')]:
            with self.subTest(field=field, value=value):
                r = row(); r[field] = value
                accepted, rejected, _ = reconcile([r], self.reference)
                self.assertFalse(accepted)
                self.assertIn(reason, rejected[0]['reasons'])

    def test_coverage_gap_is_separate_from_bad_price(self):
        extra = dict(self.reference[0], game_id='espn:nba:test-2', game_date='2025-02-01')
        r = row(); r['ML_Home'] = 0
        _, _, report = reconcile([r], self.reference + [extra])
        self.assertEqual(report['matched_source_games'], 1)
        self.assertEqual(report['missing_after_source_date_span'], 1)
        self.assertEqual(report['quarantined_rows'], 1)

    def test_incomplete_or_ambiguous_reference_not_used(self):
        e = event(); e['competitions'][0]['status']['type']['completed'] = False
        self.assertIsNone(reference_game(e))
        with self.assertRaises(ValueError):
            reconcile([row()], self.reference * 2)

    def test_quarantine_nonfinite_evidence_is_json_safe(self):
        value = json_safe({'bad_price': float('inf'), 'nested': [float('nan')]})
        encoded = json.dumps(value, allow_nan=False)
        self.assertIn('invalid_nonfinite_number', encoded)

    def test_existing_run_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            marker = output / 'keep.txt'
            marker.write_text('keep')
            with self.assertRaises(ValueError):
                normalize_database('missing.sqlite', 'missing', output)
            self.assertEqual(marker.read_text(), 'keep')

    def test_end_to_end_manifest_quarantine_and_input_integrity(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            reference = root / 'reference'; reference.mkdir()
            inventory = {'sports': [{'leagues': [{'teams': [
                {'team': {'id': str(i)}} for i in range(1, 31)
            ]}]}]}
            (reference / 'teams.json').write_text(json.dumps(inventory))
            for year in (2025, 2026):
                for kind in (2, 3, 5):
                    for team in range(1, 31):
                        e = event()
                        e.update(season={'year': year}, seasonType={'type': kind})
                        e['id'] = str(year)
                        events = [e] if team == 1 and kind == 2 else []
                        raw = json.dumps({'events': events}).encode()
                        path = reference / f'{year}-{kind}-{team}.json'
                        path.write_bytes(raw)
                        path.with_suffix('.meta.json').write_text(json.dumps({
                            'url': 'https://example.invalid/synthetic',
                            'retrieved_at': '2026-10-08T00:00:00+00:00',
                            'sha256': sha256(raw).hexdigest(),
                        }))
            database = root / 'source.sqlite'
            with sqlite3.connect(database) as con:
                for table in ('2024-25', 'odds_2025-26'):
                    con.execute(f'CREATE TABLE "{table}" (Date TEXT, Home TEXT, Away TEXT, '
                                'ML_Home REAL, ML_Away REAL, Points REAL, Win_Margin REAL)')
                    con.execute(f'INSERT INTO "{table}" VALUES (?,?,?,?,?,?,?)', tuple(row().values()))
                    bad = row(); bad['Away'] = 'Unknown'; bad['ML_Home'] = float('inf')
                    con.execute(f'INSERT INTO "{table}" VALUES (?,?,?,?,?,?,?)', tuple(bad.values()))
            before = sha256(database.read_bytes()).hexdigest()
            output = root / 'output'
            summary = normalize_database(database, reference, output)
            self.assertEqual(sha256(database.read_bytes()).hexdigest(), before)
            self.assertEqual(summary['2024-25']['accepted_research_rows'], 1)
            self.assertEqual(summary['2024-25']['quarantined_rows'], 1)
            q = json.loads((output / '2024-25/quarantine.jsonl').read_text())
            self.assertEqual(q['raw_record']['ML_Home']['invalid_nonfinite_number'], 'inf')
            quotes = json.loads((output / '2024-25/quotes.jsonl').read_text())
            self.assertEqual(quotes['source_sha256'], before)
            self.assertIsNone(quotes['bookmaker'])
            # Modified reference data must invalidate the next run.
            (reference / '2025-2-1.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                normalize_database(database, reference, root / 'another-output')
            self.assertFalse((root / 'another-output').exists())
