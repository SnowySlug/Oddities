import unittest

from oddities.odds import (
    american_to_decimal, expected_return, implied_probability,
    proportional_devig, two_way_arbitrage,
)


class OddsTests(unittest.TestCase):
    def test_known_prices(self):
        for price, decimal, probability in [(100, 2, .5), (-100, 2, .5), (200, 3, 1/3), (-200, 1.5, 2/3)]:
            with self.subTest(price=price):
                self.assertAlmostEqual(american_to_decimal(price), decimal)
                self.assertAlmostEqual(implied_probability(price), probability)

    def test_devig_balanced_and_asymmetric(self):
        self.assertEqual(proportional_devig(-110, -110), (.5, .5))
        h, a = proportional_devig(-200, 150)
        self.assertAlmostEqual(h, .625)
        self.assertAlmostEqual(h + a, 1)

    def test_expected_return_and_break_even(self):
        self.assertAlmostEqual(expected_return(.58, 110), .218)
        for price in (-2000, -110, 100, 350):
            self.assertAlmostEqual(expected_return(implied_probability(price), price), 0)
        self.assertEqual(expected_return(0, 110), -1)
        self.assertAlmostEqual(expected_return(1, 110), 1.1)

    def test_arbitrage_equal_payouts(self):
        result = two_way_arbitrage(120, 110)
        self.assertIsNotNone(result)
        h, a = result['home_stake_fraction'], result['away_stake_fraction']
        self.assertAlmostEqual(h + a, 1)
        self.assertAlmostEqual(h * 2.2, a * 2.1)
        self.assertAlmostEqual(h * 2.2 - 1, result['theoretical_return'])
        self.assertIsNone(two_way_arbitrage(-110, -110))
        self.assertIsNone(two_way_arbitrage(100, 100))

    def test_invalid_inputs_fail_closed(self):
        for value in (0, 99, -99, float('nan'), float('inf'), None, True, 'bad'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                american_to_decimal(value)
        for value in (-.1, 1.1, float('nan'), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                expected_return(value, 110)
