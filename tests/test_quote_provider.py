"""行情解析、代码校验、交易时段测试。"""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.quote_provider import (StockDataProvider, is_market_open,
                                parse_sina_line, validate_symbol)

SINA_LINE = ('var hq_str_sh000001="上证指数,3907.2058,3894.4224,3903.7210,'
             '3925.0615,3888.0989,0,0,506633954,1018568353177,0,0,0,0,0,0,'
             '0,0,0,0,0,0,0,0,0,0,0,0,0,0,2026-08-20,15:35:32,00,";')


class TestParse(unittest.TestCase):
    def test_parse_index(self):
        d = parse_sina_line(SINA_LINE)
        self.assertIsNotNone(d)
        self.assertEqual(d["symbol"], "sh000001")
        self.assertEqual(d["name"], "上证指数")
        self.assertAlmostEqual(d["price"], 3903.7210, places=3)
        self.assertAlmostEqual(d["change"], 3903.7210 - 3894.4224, places=3)
        self.assertAlmostEqual(d["change_percent"],
                               (3903.7210 / 3894.4224 - 1) * 100, places=2)
        self.assertEqual(d["date"], "2026-08-20")

    def test_parse_garbage(self):
        self.assertIsNone(parse_sina_line("var x='';"))
        self.assertIsNone(parse_sina_line(""))


class TestSymbol(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate_symbol("600519"), "sh600519")
        self.assertEqual(validate_symbol("000001"), "sz000001")
        self.assertEqual(validate_symbol("300750"), "sz300750")
        self.assertEqual(validate_symbol("830799"), "bj830799")
        self.assertEqual(validate_symbol("sh000001"), "sh000001")
        self.assertEqual(validate_symbol(" SZ000002 "), "sz000002")

    def test_invalid(self):
        for bad in ("", "12345", "1234567", "abcdef", "sh1234", "60051a"):
            self.assertIsNone(validate_symbol(bad), bad)


class TestMarketOpen(unittest.TestCase):
    def test_weekend(self):
        self.assertFalse(is_market_open(datetime(2026, 8, 22, 10, 0)))  # 周六

    def test_trading_hours(self):
        self.assertTrue(is_market_open(datetime(2026, 8, 20, 10, 0)))   # 周四早盘
        self.assertFalse(is_market_open(datetime(2026, 8, 20, 12, 0)))  # 午休
        self.assertTrue(is_market_open(datetime(2026, 8, 20, 14, 0)))
        self.assertFalse(is_market_open(datetime(2026, 8, 20, 15, 30)))
        self.assertFalse(is_market_open(datetime(2026, 8, 20, 9, 5)))

    def test_uses_exchange_timezone_for_aware_datetime(self):
        # 02:00 UTC is 10:00 in Shanghai: the continuous session is open.
        self.assertTrue(is_market_open(
            datetime(2026, 8, 20, 2, 0, tzinfo=timezone.utc)))


class TestQuoteValidation(unittest.TestCase):
    def test_rejects_unsafe_quote_data_before_state_machine(self):
        provider = StockDataProvider()
        provider.http = Mock()
        base = {
            "symbol": "sh000001", "name": "上证指数", "price": 100.0,
            "change": 10.0, "change_percent": 100 / 9,
            "date": "2026-08-20", "time": "10:00:00",
        }
        for field, value in (("price", float("nan")), ("price", 0.0),
                             ("change_percent", 5.0)):
            with self.subTest(field=field, value=value):
                data = {**base, field: value}
                provider.http.get_quote.return_value = data

                result = provider.get_quote("sh000001")

                self.assertFalse(result.ok)
                self.assertEqual(result.error, "行情数据无效")


if __name__ == "__main__":
    unittest.main()
