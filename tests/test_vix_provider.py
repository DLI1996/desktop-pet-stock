"""Deterministic checks for Cboe VIX CSV parsing."""
import unittest

from src.vix_provider import parse_vix_csv, parse_vix_summary


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

    def test_summary_includes_ohlc_previous_close_and_change(self):
        data = b"""DATE,OPEN,HIGH,LOW,CLOSE
08/21/2026,14.10,14.80,13.90,14.55
08/24/2026,14.60,15.20,14.30,15.05
08/25/2026,15.00,15.70,14.90,15.42
"""

        summary = parse_vix_summary(data)

        self.assertEqual(summary.date, "2026-08-25")
        self.assertEqual(summary.value, 15.42)
        self.assertEqual(summary.change, 0.37)
        self.assertEqual(summary.open, 15.0)
        self.assertEqual(summary.high, 15.7)
        self.assertEqual(summary.low, 14.9)
        self.assertEqual(summary.previous_close, 15.05)


if __name__ == "__main__":
    unittest.main()
