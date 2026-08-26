"""Deterministic checks for Cboe VIX CSV parsing."""
import unittest

from src.vix_provider import parse_vix_csv


class TestVixProvider(unittest.TestCase):
    def test_filters_invalid_rows_and_sorts_valid_observations(self):
        data = b"""DATE,OPEN,HIGH,LOW,CLOSE
08/22/2026,0,0,0,18.5
bad-date,0,0,0,17
08/20/2026,0,0,0,NaN
08/19/2026,0,0,0,0
08/18/2026,0,0,0,-1
08/21/2026,0,0,0,17.25
08/17/2026,0,0,0,bad
"""

        self.assertEqual(
            parse_vix_csv(data),
            [("2026-08-21", 17.25), ("2026-08-22", 18.5)],
        )

    def test_raises_when_no_valid_observations_remain(self):
        with self.assertRaisesRegex(ValueError, "no valid observations"):
            parse_vix_csv(b"DATE,CLOSE\ninvalid,NaN\n08/20/2026,-1\n")


if __name__ == "__main__":
    unittest.main()
