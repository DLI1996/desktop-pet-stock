#!/usr/bin/env python3
"""素材预处理：白底抠图 -> 透明PNG，保留角色内部白色区域，边缘羽化。

规则（与需求一致）：
- 只删除与画面边界连通的近白色背景（洪泛填充）
- 保留角色身体、眼睛高光、牙齿、金链等内部的白色/高亮区域
- 边缘羽化（alpha 高斯模糊 + 1px 腐蚀）
- 裁剪到内容包围盒，脚底贴近画布底边（统一脚底锚点）
"""
import sys
from pathlib import Path

from PIL import Image, ImageFilter
from collections import deque

SRC = Path("/Users/mac/Downloads/桌宠assets")
DST = Path(__file__).resolve().parent.parent / "assets"

MAPPING = {
    "idle/frame_001.png": "牛来.png",
    "rise/frame_001.png": "牛来欢呼.png",
    "surge/frame_001.png": "牛来豹拉跳舞.png",
    "fall/frame_001.png": "牛来拉开拉链露出熊大.png",
    "fall/frame_002.png": "熊大哭.png",
}

WHITE_TOL = 242  # RGB 全部 >= 该值视为候选背景


def remove_white_bg(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()

    visited = bytearray(w * h)
    bg = bytearray(w * h)  # 1 = 背景
    q = deque()

    def is_bg(i, j):
        r, g, b = px[i, j][:3]
        return r >= WHITE_TOL and g >= WHITE_TOL and b >= WHITE_TOL

    # 从四条边上的近白像素开始洪泛
    for x in range(w):
        for y in (0, h - 1):
            if is_bg(x, y):
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if is_bg(x, y):
                q.append((x, y))

    while q:
        x, y = q.popleft()
        idx = y * w + x
        if visited[idx]:
            continue
        visited[idx] = 1
        bg[idx] = 1
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not visited[ny * w + nx]:
                if is_bg(nx, ny):
                    q.append((nx, ny))

    # 生成 alpha
    alpha = Image.new("L", (w, h), 255)
    ap = alpha.load()
    for idx in range(w * h):
        if bg[idx]:
            ap[idx % w, idx // w] = 0

    # 羽化：轻微模糊 + 腐蚀，去白边
    alpha = alpha.filter(ImageFilter.MinFilter(3))       # 腐蚀 1px 去残留白边
    alpha = alpha.filter(ImageFilter.GaussianBlur(1.2))  # 羽化

    im.putalpha(alpha)
    return im


def crop_to_content(im: Image.Image, pad: int = 12) -> Image.Image:
    bbox = im.getbbox()
    if not bbox:
        return im
    l, t, r, b = bbox
    l = max(0, l - pad)
    t = max(0, t - pad)
    r = min(im.width, r + pad)
    b = min(im.height, b + pad)
    return im.crop((l, t, r, b))


def main():
    for rel, src_name in MAPPING.items():
        src = SRC / src_name
        dst = DST / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        im = Image.open(src)
        out = crop_to_content(remove_white_bg(im))
        out.save(dst)
        print(f"{src_name} -> {rel}  {out.size}")


if __name__ == "__main__":
    sys.exit(main())
