"""行情数据提供层。

数据链路（按优先级）：
1. Skill 桥接文件 quote.json —— 由 a-stock-realtime Skill 的 analyze.py 定时写入
   （千问办公 Skill 无法被桌面进程直接调用，采用文件桥接，见 CONNECTOR.md）。
2. 用户显式启用时，直连新浪财经公开行情接口（真实数据，界面如实标注数据源）。

所有网络请求在后台线程执行，超时 8 秒。
"""
from __future__ import annotations

import json
import logging
import math
import re
import threading
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

log = logging.getLogger("pet.quote")

SYMBOL_RE = re.compile(r"^(?:sh|sz|bj)?\d{6}$", re.IGNORECASE)

MARKET_SESSIONS = [
    (dtime(9, 15), dtime(11, 30)),
    (dtime(13, 0), dtime(15, 0)),
]

EXCHANGE_TIMEZONE = ZoneInfo("Asia/Shanghai")

BRIDGE_MAX_AGE = 120  # quote.json 超过该秒数视为过期
HTTP_TIMEOUT = 8


def validate_symbol(symbol: str) -> str | None:
    """校验并规范化代码：接受 sh000001 / 000001 等形式。"""
    s = symbol.strip().lower()
    if not SYMBOL_RE.match(s):
        return None
    if s.startswith(("sh", "sz", "bj")):
        return s
    if s.startswith("6"):
        return "sh" + s
    if s.startswith(("0", "3")):
        return "sz" + s
    if s.startswith(("8", "4")):
        return "bj" + s
    return "sh" + s


def is_market_open(now: datetime | None = None) -> bool:
    if now is None:
        now = datetime.now(EXCHANGE_TIMEZONE)
    elif now.tzinfo is not None:
        now = now.astimezone(EXCHANGE_TIMEZONE)
    if now.weekday() >= 5:  # 周末
        return False
    t = now.time()
    return any(a <= t <= b for a, b in MARKET_SESSIONS)


def parse_sina_line(line: str) -> dict | None:
    """解析新浪 hq 接口单行数据（纯函数，便于测试）。"""
    m = re.search(r'hq_str_(\w+)="([^"]*)"', line)
    if not m:
        return None
    symbol, body = m.group(1), m.group(2)
    fields = body.split(",")
    if len(fields) < 4 or not fields[0] or not fields[3]:
        return None
    try:
        open_, prev_close, price = float(fields[1]), float(fields[2]), float(fields[3])
        high, low = float(fields[4]), float(fields[5])
        volume = float(fields[8]) if len(fields) > 8 and fields[8] else 0.0
        amount = float(fields[9]) if len(fields) > 9 and fields[9] else 0.0
        date = fields[30] if len(fields) > 30 else ""
        tick = fields[31] if len(fields) > 31 else ""
    except (ValueError, IndexError):
        return None
    if prev_close == 0:
        return None
    change = price - prev_close
    return {
        "symbol": symbol,
        "name": fields[0],
        "price": price,
        "change": round(change, 4),
        "change_percent": round(change / prev_close * 100, 4),
        "open": open_,
        "high": high,
        "low": low,
        "volume": volume,
        "amount": amount,
        "date": date,
        "time": tick,
    }


def is_valid_quote_data(data: dict) -> bool:
    """Reject non-finite, impossible, or inconsistent quote fields."""
    try:
        price = float(data["price"])
        change = float(data["change"])
        change_percent = float(data["change_percent"])
    except (KeyError, TypeError, ValueError):
        return False
    if not all(math.isfinite(value) for value in (price, change, change_percent)):
        return False
    prev_close = price - change
    return (price > 0 and prev_close > 0 and
            math.isclose(change_percent, change / prev_close * 100,
                         abs_tol=0.0001))


@dataclass
class QuoteResult:
    symbol: str = ""
    name: str = ""
    price: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    timestamp: str = ""
    source: str = ""
    is_realtime: bool = False
    market_open: bool = False
    ok: bool = False
    error: str | None = None
    raw: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": self.price,
            "change": self.change,
            "change_percent": self.change_percent,
            "timestamp": self.timestamp,
            "source": self.source,
            "is_realtime": self.is_realtime,
        }


class SinaHttpProvider:
    """直连新浪行情接口（备用真实数据源）。"""

    NAME = "新浪财经接口(hq.sinajs.cn)"

    def get_quote(self, symbol: str) -> dict | None:
        url = f"https://hq.sinajs.cn/list={symbol},s_{symbol}"
        req = urllib.request.Request(url, headers={
            "Referer": "https://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        })
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            text = resp.read().decode("gbk", errors="replace")
        for line in text.strip().split("\n"):
            data = parse_sina_line(line)
            if data and data["symbol"] == symbol and data["price"] > 0:
                return data
        return None


class SkillBridgeProvider:
    """读取 a-stock-realtime Skill 桥接写入的 quote.json。"""

    NAME = "a-stock-realtime Skill(桥接)"

    def __init__(self, bridge_path: str):
        self.path = bridge_path

    def get_quote(self, symbol: str) -> dict | None:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                obj = json.load(f)
        except (OSError, json.JSONDecodeError):
            return None
        if obj.get("symbol") != symbol:
            return None
        try:
            ts = datetime.strptime(obj.get("timestamp", ""), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
        if (datetime.now() - ts).total_seconds() > BRIDGE_MAX_AGE:
            return None
        if not obj.get("price"):
            return None
        return {
            "symbol": obj["symbol"],
            "name": obj.get("name", ""),
            "price": float(obj["price"]),
            "change": float(obj.get("change", 0)),
            "change_percent": float(obj.get("change_percent", 0)),
            "open": 0.0, "high": 0.0, "low": 0.0,
            "volume": 0.0, "amount": 0.0,
            "date": obj["timestamp"].split(" ")[0],
            "time": obj["timestamp"].split(" ")[1] if " " in obj["timestamp"] else "",
        }


class StockDataProvider:
    """统一行情接口：get_quote(symbol) -> QuoteResult。

    优先 Skill 桥接文件（由千问办公 a-stock-realtime Skill 定时写入 quote.json），
    过期或不存在时可选直连新浪接口。两者均为真实数据，来源如实标注。
    """

    def __init__(self, bridge_path: str | None = None,
                 enable_http_fallback: bool = False):
        self.bridge = SkillBridgeProvider(bridge_path) if bridge_path else None
        self.enable_http_fallback = enable_http_fallback
        self.http = SinaHttpProvider()

    def get_quote(self, symbol: str) -> QuoteResult:
        open_ = is_market_open()
        result = QuoteResult(symbol=symbol, market_open=open_)
        data, source = None, ""
        if self.bridge:
            try:
                data = self.bridge.get_quote(symbol)
                source = SkillBridgeProvider.NAME
            except Exception as e:  # noqa: BLE001
                log.warning("bridge failed: %s", e)
        if data is None and self.enable_http_fallback:
            try:
                data = self.http.get_quote(symbol)
                source = SinaHttpProvider.NAME
            except Exception as e:  # noqa: BLE001
                log.warning("sina http failed: %s", e)
                result.error = f"网络异常: {e}"
                return result
        if data is None:
            result.error = "接口返回空数据"
            return result
        if not is_valid_quote_data(data):
            result.error = "行情数据无效"
            return result
        ts = f'{data.get("date", "")} {data.get("time", "")}'.strip() or \
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result.ok = True
        result.name = data["name"]
        result.price = data["price"]
        result.change = data["change"]
        result.change_percent = data["change_percent"]
        result.timestamp = ts
        result.source = source
        # 非交易时段为最近收盘数据，不标成实时
        result.is_realtime = open_
        result.raw = data
        return result

    def get_quote_async(self, symbol: str, callback):
        """后台线程获取，完成后回调 callback(QuoteResult)。"""

        def run():
            try:
                r = self.get_quote(symbol)
            except Exception as e:  # noqa: BLE001
                r = QuoteResult(symbol=symbol, error=str(e))
            callback(r)

        t = threading.Thread(target=run, daemon=True)
        t.start()
