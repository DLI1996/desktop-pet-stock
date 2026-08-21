"""行情状态机：FLAT / RISE / SURGE / FALL，带两次去抖。"""
from __future__ import annotations

from enum import Enum


class MarketState(Enum):
    FLAT = "FLAT"
    RISE = "RISE"
    SURGE = "SURGE"
    FALL = "FALL"


def classify(change_percent: float, rise: float, surge: float, fall: float) -> MarketState:
    """按阈值分类（阈值来自 config.json，不写死）。"""
    if change_percent >= surge:
        return MarketState.SURGE
    if change_percent >= rise:
        return MarketState.RISE
    if change_percent <= fall:
        return MarketState.FALL
    return MarketState.FLAT


class StateMachine:
    """去抖状态机：连续两次同属新状态才切换。首次数据立即生效。"""

    def __init__(self, rise: float, surge: float, fall: float):
        self.rise, self.surge, self.fall = rise, surge, fall
        self.state: MarketState = MarketState.FLAT
        self._pending: MarketState | None = None
        self._pending_count = 0
        self._first = True

    def feed(self, change_percent: float) -> MarketState | None:
        """喂入一次行情，返回新状态（切换时）或 None。"""
        target = classify(change_percent, self.rise, self.surge, self.fall)
        if self._first:
            self._first = False
            self.state = target
            return target
        if target == self.state:
            self._pending, self._pending_count = None, 0
            return None
        if target == self._pending:
            self._pending_count += 1
        else:
            self._pending, self._pending_count = target, 1
        if self._pending_count >= 2:
            self.state = target
            self._pending, self._pending_count = None, 0
            return target
        return None

    def force(self, state: MarketState) -> None:
        """演示模式/测试强制切换。"""
        self.state = state
        self._pending, self._pending_count = None, 0
