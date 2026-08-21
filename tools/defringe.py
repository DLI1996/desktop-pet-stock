#!/usr/bin/env python3
"""去黑边/白边：对所有素材帧做边缘颜色反混合。

原理：抠图时抗锯齿边缘像素 = 角色色与背景色的混合。半透明像素直接保留
会在桌面上呈现深色描边（黑边）或白边。本脚本：
1. alpha 收紧（轻微腐蚀+平滑）
2. 对 0<alpha<255 的像素做颜色反混合：
   C' = (C - (1-a) * BG) / a    （BG 为原背景色：白或深色）
   彻底消除边缘混色残留
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ASSETS = Path(__file__).resolve().parent.parent / "assets"
FOLDERS = ["idle", "rise", "surge", "fall"]


def unblend(a: np.ndarray, bg: np.ndarray) -> np.ndarray:
    """把 RGBA 数组的颜色对背景 bg 做反混合，消除边缘混色。"""
    rgb = a[:, :, :3].astype(float)
    alpha = a[:, :, 3].astype(float)
    af = alpha / 255.0
    semi = (alpha > 0) & (alpha < 255)
    # 防除零：alpha 很低的像素直接设为背景色（反正几乎不可见）
    safe_af = np.clip(af, 0.04, 1.0)
    un = (rgb - (1.0 - safe_af[..., None]) * bg) / safe_af[..., None]
    out = rgb.copy()
    out[semi] = np.clip(un[semi], 0, 255)
    a[:, :, :3] = out.astype(np.uint8)
    return a


def process(path: Path, dark_bg: bool = False) -> None:
    im = Image.open(path).convert("RGBA")
    arr = np.array(im)
    alpha = Image.fromarray(arr[:, :, 3])

    # 1) 收紧：腐蚀 1px 再平滑，去掉稀薄残留
    alpha = alpha.filter(ImageFilter.MinFilter(3))
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.8))
    # 阈值化低端：alpha<60 全透明，消除灰边
    a = np.asarray(alpha).astype(int)
    a = np.where(a < 60, 0, a)
    arr[:, :, 3] = a.astype(np.uint8)

    # 2) 颜色反混合：原背景为白(255)或深色(近黑截图背景)
    bg = np.array([16.0, 16.0, 20.0]) if dark_bg else np.array([255.0, 255.0, 255.0])
    arr = unblend(arr, bg)

    Image.fromarray(arr).save(path)


def main():
    for folder in FOLDERS:
        d = ASSETS / folder
        if not d.exists():
            continue
        for p in sorted(d.glob("frame_*.png")):
            # rise 来自深色截图背景；其余来自白底
            process(p, dark_bg=(folder == "rise"))
            print(f"defringe: {folder}/{p.name}")


if __name__ == "__main__":
    sys.exit(main())
