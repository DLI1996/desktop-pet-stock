"""气泡：常驻显示，按行情状态显示含关键词的短句。"""
from __future__ import annotations

import random
import time

STATE_LINES = {
    "RISE": [
        "牛来！今天红了！",
        "牛来戴上金链了！",
        "牛来要开始摸鱼了！",
    ],
    "SURGE": [
        "爆拉！豹拉都炸出来了！",
        "爆拉！刷抖音去了！",
        "爆拉！今天不上班！",
    ],
    "FALL": [
        "熊来……先哭两分钟",
        "熊来了，牛来下岗了",
        "熊来！该上班了呜呜",
    ],
}


class BubbleController:
    """气泡常驻：show_random 换台词后一直显示（点击/状态切换时换）。"""

    def __init__(self):
        self.text: str | None = None
        self.shown_at: float = 0.0

    def show_random(self, state: str | None = None) -> str:
        """换成该状态的一句台词（含 牛来/熊来/爆拉 关键词）。
        普通状态（FLAT）无气泡。"""
        pool = STATE_LINES.get(state)
        if not pool:
            self.text = None  # 普通状态：无气泡
            return ""
        self.text = random.choice(pool)
        self.shown_at = time.monotonic()
        return self.text

    def visible_text(self) -> str | None:
        return self.text  # 常驻，不过期

    def clear(self) -> None:
        self.text = None
