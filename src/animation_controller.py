"""动画控制器：视频帧序列播放 + 待机呼吸 + 点击动效。

纯逻辑，不依赖 Qt；pet_window 的 paintEvent 按返回的变换参数绘制。
RISE / SURGE / FALL 三态来自用户提供的黑底视频帧序列（tools/extract_videos.py）：
- RISE / SURGE：无缝循环（12fps）
- FALL：一次性变身动画，播完定格在最后一帧（熊坐地哭）
FLAT 为静态待机图 + 程序呼吸动画。
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass


@dataclass
class Transform:
    x_off: float = 0.0
    y_off: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotate: float = 0.0  # 度


CLICK_ANIMS = ["jump", "squash", "shake"]
# 各状态帧序列帧率（素材来源：GIF 全部 10fps）
STATE_FPS = {"FLAT": 10, "RISE": 10, "SURGE": 10, "FALL": 10}


class AnimationController:
    def __init__(self):
        self.state_start = time.monotonic()
        self.click_start: float | None = None
        self.click_kind = ""
        self.click_index = 0
        self.click_duration = 0.9

    def on_state_changed(self) -> None:
        self.state_start = time.monotonic()

    def trigger_click(self) -> None:
        self.click_kind = CLICK_ANIMS[self.click_index % len(CLICK_ANIMS)]
        self.click_index += 1
        self.click_start = time.monotonic()

    # ---------- 视频帧序列 ----------
    def video_frame(self, state: str, t: float, total: int) -> int:
        """帧索引：RISE/SURGE 循环播放；FALL 播完定格最后一帧。"""
        idx = int(t * STATE_FPS.get(state, 12))
        if state == "FALL":
            return min(idx, total - 1)
        return idx % total

    # ---------- 状态附加动画 ----------
    def _state_transform(self, state: str, t: float) -> Transform:
        tr = Transform()
        if state == "FLAT":  # 待机呼吸 + 微晃（静态图）
            tr.scale_y = 1.0 + 0.008 * math.sin(2 * math.pi * t / 3.2)
            tr.scale_x = 1.0 - 0.005 * math.sin(2 * math.pi * t / 3.2)
            tr.rotate = 0.6 * math.sin(2 * math.pi * t / 5.0)
        # RISE/SURGE/FALL：动作由视频帧序列呈现，不叠加程序动画
        return tr

    def _click_transform(self, p: float) -> Transform:
        tr = Transform()
        if self.click_kind == "jump":
            tr.y_off = -70.0 * math.sin(math.pi * p)
        elif self.click_kind == "squash":
            k = math.sin(math.pi * p)
            tr.scale_y = 1.0 - 0.28 * k
            tr.scale_x = 1.0 + 0.22 * k
        elif self.click_kind == "shake":
            tr.x_off = 14.0 * math.sin(2 * math.pi * p * 3.0) * (1.0 - p)
            tr.rotate = 3.0 * math.sin(2 * math.pi * p * 3.0) * (1.0 - p)
        return tr

    def current(self, state: str, t: float | None = None) -> Transform:
        now = time.monotonic()
        t = now - self.state_start if t is None else t
        tr = self._state_transform(state, t)
        # 点击动效叠加（结束后自动清除，回到行情状态）
        if self.click_start is not None:
            p = (now - self.click_start) / self.click_duration
            if p >= 1.0:
                self.click_start = None
            else:
                c = self._click_transform(p)
                tr.x_off += c.x_off
                tr.y_off += c.y_off
                tr.scale_x *= c.scale_x
                tr.scale_y *= c.scale_y
                tr.rotate += c.rotate
        return tr
