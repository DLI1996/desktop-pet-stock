"""状态机与去抖逻辑测试。"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.state_machine import MarketState, StateMachine, classify


class TestClassify(unittest.TestCase):
    def test_thresholds(self):
        r, s, f = 0.10, 3.00, -0.10
        self.assertEqual(classify(3.5, r, s, f), MarketState.SURGE)
        self.assertEqual(classify(3.0, r, s, f), MarketState.SURGE)
        self.assertEqual(classify(1.0, r, s, f), MarketState.RISE)
        self.assertEqual(classify(0.10, r, s, f), MarketState.RISE)
        self.assertEqual(classify(0.05, r, s, f), MarketState.FLAT)
        self.assertEqual(classify(-0.10, r, s, f), MarketState.FALL)
        self.assertEqual(classify(-3.0, r, s, f), MarketState.FALL)


class TestDebounce(unittest.TestCase):
    def test_first_fetch_immediate(self):
        sm = StateMachine(0.1, 3.0, -0.1)
        self.assertEqual(sm.feed(1.0), MarketState.RISE)

    def test_requires_two_consecutive(self):
        sm = StateMachine(0.1, 3.0, -0.1)
        sm.feed(0.0)  # FLAT
        self.assertIsNone(sm.feed(1.0))   # 单次不切换
        self.assertEqual(sm.feed(1.0), MarketState.RISE)  # 连续两次切换

    def test_jitter_no_switch(self):
        sm = StateMachine(0.1, 3.0, -0.1)
        sm.feed(0.0)
        self.assertIsNone(sm.feed(1.0))   # RISE 一次
        self.assertIsNone(sm.feed(0.05))  # 回落，计数重置
        self.assertIsNone(sm.feed(1.0))   # RISE 一次
        self.assertIsNone(sm.feed(0.05))  # 抖动不切换

    def test_cooldown_state_stays(self):
        sm = StateMachine(0.1, 3.0, -0.1)
        sm.feed(0.0)
        self.assertIsNone(sm.feed(1.0))
        self.assertEqual(sm.feed(1.0), MarketState.RISE)
        self.assertIsNone(sm.feed(1.0))  # 已在该状态


if __name__ == "__main__":
    unittest.main()
