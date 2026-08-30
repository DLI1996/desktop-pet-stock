"""Cboe VIX daily-history data access."""
from __future__ import annotations

import csv
import io
import math
import urllib.request
from dataclasses import dataclass
from datetime import datetime

VIX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
VIX_SOURCE = "Cboe VIX History CSV"


@dataclass(frozen=True)
class VixSummary:
    date: str
    value: float
    change: float
    open: float
    high: float
    low: float
    previous_close: float
    source: str = VIX_SOURCE


def fetch_vix_csv() -> bytes:
    request = urllib.request.Request(VIX_URL, headers={"User-Agent": "desktop-pet-stock/1"})
    with urllib.request.urlopen(request, timeout=8) as response:
        return response.read()


def parse_vix_csv(data: bytes) -> list[tuple[str, float]]:
    """Return up to 60 validated daily closes sorted by observation date."""
    points = []
    for row in csv.DictReader(io.StringIO(data.decode("utf-8-sig"))):
        try:
            date = datetime.strptime(row["DATE"].strip(), "%m/%d/%Y")
            close = float(row["CLOSE"])
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(close) and close > 0:
            points.append((date.strftime("%Y-%m-%d"), close))
    if not points:
        raise ValueError("Cboe VIX CSV contains no valid observations")
    return sorted(points)[-60:]


def parse_vix_summary(data: bytes) -> VixSummary:
    """Parse the latest valid Cboe row and its previous close."""
    rows = []
    for row in csv.DictReader(io.StringIO(data.decode("utf-8-sig"))):
        try:
            date = datetime.strptime(row["DATE"].strip(), "%m/%d/%Y")
            values = [float(row[field]) for field in ("OPEN", "HIGH", "LOW", "CLOSE")]
        except (KeyError, TypeError, ValueError):
            continue
        if all(math.isfinite(value) and value > 0 for value in values):
            rows.append((date, *values))
    rows.sort()
    if not rows:
        raise ValueError("Cboe VIX CSV contains no valid observations")
    latest = rows[-1]
    previous_close = rows[-2][4] if len(rows) > 1 else latest[4]
    return VixSummary(
        latest[0].strftime("%Y-%m-%d"), latest[4], round(latest[4] - previous_close, 4),
        latest[1], latest[2], latest[3], previous_close)
