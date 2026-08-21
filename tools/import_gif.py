#!/usr/bin/env python3
"""从透明底 GIF 导入帧序列到 assets/<state>/。

GIF 的 alpha 是 1-bit（硬边），这里对边缘做轻微羽化让显示更柔和。
用法：python tools/import_gif.py <gif路径> <state>
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageFilter
import numpy as np

DST = Path(__file__).resolve().parent.parent / "assets"


def import_gif(gif_path: Path, state: str) -> int:
    im = Image.open(gif_path)
    n = getattr(im, "n_frames", 1)
    dst = DST / state
    dst.mkdir(parents=True, exist_ok=True)
    for old in dst.glob("frame_*.png"):
        old.replace(Path("/tmp/old_assets") / state / old.name)
    for i in range(n):
        im.seek(i)
        rgba = im.convert("RGBA")
        a = np.asarray(rgba)[:, :, 3]
        # 轻微羽化：1px 模糊 alpha，只在边缘产生少量半透明
        al = Image.fromarray(a).filter(ImageFilter.GaussianBlur(0.6))
        out = rgba.copy()
        out.putalpha(al)
        out.save(dst / f"frame_{i + 1:03d}.png")
    return n


def main():
    if len(sys.argv) != 3:
        print("用法: import_gif.py <gif路径> <rise|surge|fall>")
        return 1
    gif, state = Path(sys.argv[1]), sys.argv[2]
    if state not in ("rise", "surge", "fall", "idle"):
        print("state 必须是 rise/surge/fall/idle")
        return 1
    n = import_gif(gif, state)
    print(f"{gif.name} -> assets/{state}/ 共 {n} 帧")
    return 0


if __name__ == "__main__":
    sys.exit(main())
