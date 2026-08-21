#!/usr/bin/env python3
"""从黑底渲染视频提取透明帧序列（rise/surge/fall）。

用法：
    1. 先用 ffmpeg 抽帧：ffmpeg -i in.mov -vf fps=12,scale=-1:720 out/f_%03d.png
    2. 本脚本对每帧做黑底抠像（洪泛 + 反混合）后写入 assets/<state>/
"""
from __future__ import annotations

import subprocess
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

SRC = Path("/Users/mac/Downloads/桌宠assets")
DST = Path(__file__).resolve().parent.parent / "assets"
TMP = Path("/tmp/newvid/extract")

VIDEOS = {
    "rise": "牛来欢呼视频.mov",
    "surge": "牛来豹拉跳舞.mov",
    "fall": "牛来拉开拉链是熊大熊大哭.mov",
}

NEAR_BLACK = 16
FPS = 12
HEIGHT = 720


def key_black(im: Image.Image) -> Image.Image:
    """黑底抠像：边界洪泛去黑 + alpha 收紧 + 颜色反混合（预乘于黑）。"""
    im = im.convert("RGBA")
    w, h = im.size
    a = np.asarray(im).astype(float)
    near_black = a[:, :, :3].max(axis=2) < NEAR_BLACK
    visited = np.zeros((h, w), dtype=bool)
    bg = np.zeros((h, w), dtype=bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if near_black[y, x]:
                visited[y, x] = True
                q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if near_black[y, x]:
                visited[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        bg[y, x] = True
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and near_black[ny, nx] and not visited[ny, nx]:
                visited[ny, nx] = True
                q.append((ny, nx))

    alpha = np.where(bg, 0, 255).astype(np.uint8)
    al = Image.fromarray(alpha).filter(ImageFilter.MinFilter(3)).filter(
        ImageFilter.GaussianBlur(1.0))
    af = np.asarray(al).astype(float) / 255.0
    rgb = a[:, :, :3]
    semi = (af > 0.05) & (af < 0.999)
    out = rgb.copy()
    out[semi] = np.clip(rgb[semi] / af[semi][:, None], 0, 255)
    out[af <= 0.05] = 0
    arr = np.dstack([out.astype(np.uint8), np.asarray(al)])
    return Image.fromarray(arr)


def main():
    for state, vid in VIDEOS.items():
        tmp = TMP / state
        tmp.mkdir(parents=True, exist_ok=True)
        # 抽帧（fps 重采样 + 缩放到高 720）
        subprocess.run(
            ["ffmpeg", "-y", "-v", "quiet", "-i", str(SRC / vid),
             "-vf", f"fps={FPS},scale=-1:{HEIGHT}",
             str(tmp / "f_%03d.png")], check=True)
        frames = sorted(tmp.glob("f_*.png"))
        dst = DST / state
        dst.mkdir(parents=True, exist_ok=True)
        # 备份旧静态帧
        for old in dst.glob("frame_*.png"):
            old.replace(Path("/tmp/old_assets") / state / old.name)
        for n, f in enumerate(frames, 1):
            key_black(Image.open(f)).save(dst / f"frame_{n:03d}.png")
        print(f"{state}: {len(frames)} 帧 -> assets/{state}/")


if __name__ == "__main__":
    sys.exit(main())
