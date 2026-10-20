#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""压缩幻灯片图片，按教学顺序编号输出 images/NN.jpg，并生成 manifest.json。

适用两种来源：
  - PPT 导出：staging 即 raw/，文件已是 01..N 顺序；
  - 现场照片：先按讲课顺序重排、去重，并把要保留的文件复制进 staging，
    以 01_、02_… 命名（“谢谢”等无内容页不要放进 staging，或用 --exclude 排除）。

用法：
    python prepare_images.py <staging_dir> --out images \
        [--width 1600] [--quality 82] [--exclude 40]

输出：images/01.jpg … 与 manifest.json（含 n、file、宽高）。
"""
import argparse
import glob
import json
import os
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("staging")
    ap.add_argument("--out", default="images")
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--quality", type=int, default=82)
    ap.add_argument("--exclude", default="", help="按排序后的 1 基序号排除，逗号分隔，如 40 或 3,7")
    args = ap.parse_args()

    files = []
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp"):
        files += glob.glob(os.path.join(args.staging, ext))
    files = sorted(files, key=lambda p: os.path.basename(p).lower())
    if not files:
        sys.exit("staging 目录里没有图片：%s" % args.staging)

    exclude = {int(x) for x in args.exclude.split(",") if x.strip()}
    os.makedirs(args.out, exist_ok=True)

    try:
        from PIL import Image
    except ImportError:
        sys.exit("缺少 Pillow：pip install pillow")

    manifest = []
    n = 0
    for idx, src in enumerate(files, 1):
        if idx in exclude:
            print("跳过：%s" % os.path.basename(src))
            continue
        n += 1
        im = Image.open(src)
        if im.mode != "RGB":
            im = im.convert("RGB")
        if im.width > args.width:
            h = int(round(im.height * args.width / im.width))
            im = im.resize((args.width, h), Image.LANCZOS)
        out = os.path.join(args.out, "%02d.jpg" % n)
        im.save(out, "JPEG", quality=args.quality, optimize=True)
        manifest.append({"n": n, "file": out.replace("\\", "/"), "w": im.width, "h": im.height})
        print("  %02d  %s  (%dx%d, %dKB)" % (n, os.path.basename(src), im.width, im.height,
                                             os.path.getsize(out) // 1024))

    with open("manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("完成：共 %d 张，manifest.json 已生成" % n)


if __name__ == "__main__":
    main()
