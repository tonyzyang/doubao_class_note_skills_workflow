#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 PPTX 每页幻灯片导出为 PNG（仅 Windows，需安装桌面版 PowerPoint）。

用法：
    python extract_ppt_windows.py <deck.pptx> --out raw [--width 1600]

输出：raw/01.png、raw/02.png …；并打印每页序号。导出的是幻灯片原貌，
后续用 prepare_images.py 压缩并生成 manifest。

无 PowerPoint / pywin32 时：改用 LibreOffice 命令（见 references/02-ppt-to-images.md）。
"""
import argparse
import os
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--out", default="raw")
    ap.add_argument("--width", type=int, default=1600, help="导出宽度（像素），按原比例算高度")
    args = ap.parse_args()

    deck = os.path.abspath(args.pptx)
    if not os.path.isfile(deck):
        sys.exit("找不到文件：%s" % deck)

    try:
        import win32com.client
    except ImportError:
        sys.exit("缺少 pywin32：pip install pywin32；或改用 LibreOffice 导出（见 references/02-ppt-to-images.md）。")

    os.makedirs(args.out, exist_ok=True)

    ppt = win32com.client.Dispatch("PowerPoint.Application")
    # 不指定参数时 PowerPoint 可能弹窗，加 WithWindow=False
    try:
        pres = ppt.Presentations.Open(deck, WithWindow=False)
    except Exception:
        pres = ppt.Presentations.Open(deck)

    w = float(pres.PageSetup.SlideWidth)
    h = float(pres.PageSetup.SlideHeight)
    scale = args.width / w
    px_w = int(round(w * scale))
    px_h = int(round(h * scale))

    n = pres.Slides.Count
    print("幻灯片总数：%d，导出尺寸 %dx%d" % (n, px_w, px_h))
    for i in range(1, n + 1):
        slide = pres.Slides.Item(i)
        out = os.path.abspath(os.path.join(args.out, "%02d.png" % i))
        slide.Export(out, "PNG", px_w, px_h)
        print("  %02d -> %s" % (i, out))

    pres.Close()
    ppt.Quit()
    print("完成：%s" % os.path.abspath(args.out))


if __name__ == "__main__":
    main()
