"""Cboe VIX daily-history data access."""
from __future__ import annotations

import csv
import io
import math
import urllib.request
from datetime import datetime

VIX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
VIX_SOURCE = "Cboe VIX History CSV"


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
