"""Skill 桥接脚本：调用 a-stock-realtime Skill 的 analyze.py，把行情写入 quote.json。

千问办公的 Skill 不能被桌面进程直接调用，采用文件桥接：
由千问办公定时任务（或手动）运行本脚本，桌宠自动读取 quote.json。

用法（在千问办公中）：
    uv run /Users/mac/.qwenworkcn/skills/a-stock-realtime/scripts/analyze.py <代码> --json
    python tools/quote_bridge.py <代码> --quote '<上述 JSON 输出>'

或直接：
    python tools/quote_bridge.py sh000001
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SKILL_SCRIPT = Path("/Users/mac/.qwenworkcn/skills/a-stock-realtime/scripts/analyze.py")
BASE = Path(__file__).resolve().parent.parent


def run_skill(code: str) -> dict | None:
    """运行 a-stock-realtime Skill 的 analyze.py --json。"""
    cmd = ["uv", "run", str(SKILL_SCRIPT), code, "--json"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    # analyze.py --json 输出 JSON（取 stdout 中第一段可解析 JSON）
    for block in out.stdout.splitlines():
        block = block.strip()
        if block.startswith("{") or block.startswith("["):
            try:
                return json.loads(block)
            except json.JSONDecodeError:
                continue
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return None


def normalize(symbol: str, data) -> dict | None:
    """解析 analyze.py --json 输出：[{code, name, realtime:{price, change_pct, ...}}]"""
    if isinstance(data, list) and data:
        data = data[0]
    if not isinstance(data, dict):
        return None
    rt = data.get("realtime") if isinstance(data.get("realtime"), dict) else data
    price = float(rt.get("price") or 0)
    if not price:
        return None
    prev = float(rt.get("pre_close") or 0)
    pct = rt.get("change_pct")
    if pct is None:
        pct = (price / prev - 1) * 100 if prev else 0.0
    name = rt.get("name") or data.get("name") or symbol
    change = rt.get("change_amt")
    if change is None:
        change = price - prev if prev else 0.0
    return {
        "symbol": normalize_symbol(symbol),
        "name": name,
        "price": price,
        "change": round(float(change), 4),
        "change_percent": round(float(pct), 4),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "a-stock-realtime Skill",
    }


def normalize_symbol(symbol: str) -> str:
    """补全市场前缀，与桌宠 config.symbol 一致（如 600519 -> sh600519）。"""
    s = symbol.strip().lower()
    if s.startswith(("sh", "sz", "bj")):
        return s
    if s.startswith("6"):
        return "sh" + s
    if s.startswith(("0", "3")):
        return "sz" + s
    if s.startswith(("8", "4")):
        return "bj" + s
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    ap.add_argument("--quote", default=None, help="直接传入 analyze.py 的 JSON 输出")
    args = ap.parse_args()

    data = json.loads(args.quote) if args.quote else run_skill(args.symbol)
    quote = normalize(args.symbol, data)
    if not quote:
        print("桥接失败：无法解析行情", file=sys.stderr)
        return 1
    out = BASE / "quote.json"
    out.write_text(json.dumps(quote, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入 {out}: {quote['name']} {quote['price']} ({quote['change_percent']:+.2f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
