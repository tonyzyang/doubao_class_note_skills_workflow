#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把课程录音转码为 Chrome 可播放、体积适中的单声道 MP3，并校验编码规格。

为什么需要它：
  - 环境通常没有 ffmpeg；本脚本用系统已装的 VLC（或显式 --vlc 指定）做转码。
  - 关键：必须输出 MP3 Layer III（acodec=mp3）。acodec=mpga 会产出 Layer II，
    Chrome 无法播放（音频元素静默失败）。
  - 转成 64kbps、单声道、44.1kHz：讲课语音听感足够，且 base64 内嵌后
    文件体积约为原来的 1/3~1/4（base64 会再放大约 1/3，需在估算时计入）。

用法：
    python transcode_audio.py "<源音频>" "<输出.mp3>" [--bitrate 64] [--vlc "<vlc路径>"]
    python transcode_audio.py "<某.mp3>"            # 只做规格校验，不转码
"""
import argparse
import os
import shutil
import subprocess
import sys

# MPEG1 Layer III 比特率表（索引 0..14），单位 kbps
BR_L3 = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]
# MPEG1 采样率表
SR = [44100, 48000, 32000]

VLC_CANDIDATES = [
    r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    "/Applications/VLC.app/Contents/MacOS/VLC",
    "/usr/bin/vlc",
    "/usr/local/bin/vlc",
    "/snap/bin/vlc",
]


def find_vlc(explicit=None):
    if explicit and os.path.exists(explicit):
        return explicit
    found = shutil.which("vlc")
    if found:
        return found
    for p in VLC_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def mp3_info(path):
    """扫描 MP3 帧头，返回 {layer,bitrate,samplerate,dur,frames}；无法识别返回 None。"""
    with open(path, "rb") as f:
        data = f.read()
    frames = 0
    layer = 0
    bitrate = 0
    samplerate = 0
    i = 0
    n = len(data)
    while i + 4 <= n:
        if data[i] == 0xFF and (data[i + 1] & 0xE0) == 0xE0:
            b1 = data[i + 1]
            b2 = data[i + 2]
            mpeg_id = (b1 >> 3) & 0x03          # 3 = MPEG1
            layer_id = (b1 >> 1) & 0x03         # 1 = Layer III
            br_idx = (b2 >> 4) & 0x0F
            sr_idx = (b2 >> 2) & 0x03
            if mpeg_id == 3 and layer_id == 1 and 1 <= br_idx <= 14 and sr_idx < 3:
                if not frames:
                    layer = 3
                    bitrate = BR_L3[br_idx]
                    samplerate = SR[sr_idx]
                frames += 1
                # 跳到下一帧（按比特率估算帧长，Layer III 每帧 1152 样本）
                flen = (144 * bitrate * 1000) // samplerate
                if b2 & 0x02:
                    flen += 1
                i += flen
                continue
        i += 1
    if not frames:
        return None
    dur = frames * 1152 / samplerate
    return {"layer": layer, "bitrate": bitrate, "samplerate": samplerate,
            "dur": dur, "frames": frames}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst", nargs="?", default="")
    ap.add_argument("--bitrate", type=int, default=64)
    ap.add_argument("--vlc", default="")
    args = ap.parse_args()

    if not args.dst:
        info = mp3_info(args.src)
        if not info:
            sys.exit("无法识别为 MP3：%s" % args.src)
        print("layer=%s bitrate=%dkbps sr=%d dur=%.1fs frames=%d"
              % (info["layer"], info["bitrate"], info["samplerate"],
                 info["dur"], info["frames"]))
        if info["layer"] != 3:
            print("警告：不是 Layer III，Chrome 可能无法播放，请用本脚本重新转码。")
        return

    vlc = find_vlc(args.vlc)
    if not vlc:
        sys.exit("未找到 VLC，请用 --vlc 指定路径，或先安装 VLC。")

    outdir = os.path.dirname(os.path.abspath(args.dst))
    os.makedirs(outdir, exist_ok=True)

    # 关键：acodec=mp3 出 Layer III；channels=1 单声道；mux=raw 按扩展名封装
    transcode = (
        "acodec=mp3,ab=%d,channels=1,samplerate=44100" % args.bitrate
    )
    cmd = [
        vlc, "-I", "dummy", "--no-sout-all", "--sout-keep",
        os.path.abspath(args.src),
        ":sout=#transcode{%s}:std{access=file,mux=raw,dst=%s}"
        % (transcode, os.path.abspath(args.dst).replace("\\", "/")),
        "vlc://quit",
    ]
    print("运行：", " ".join('"%s"' % c if " " in c else c for c in cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(args.dst):
        sys.exit("转码失败，VLC 输出：\n%s\n%s" % (r.stdout, r.stderr))

    info = mp3_info(args.dst)
    if not info:
        sys.exit("输出文件无法识别为 MP3：%s" % args.dst)
    print("完成：%s" % args.dst)
    print("layer=%s bitrate=%dkbps sr=%d dur=%.1fs frames=%d"
          % (info["layer"], info["bitrate"], info["samplerate"],
             info["dur"], info["frames"]))
    if info["layer"] != 3:
        print("警告：产出不是 Layer III，Chrome 可能无法播放，请改用 acodec=mp3 重转。")
    print("体积 %.2f MB；base64 内嵌后预计约 %.2f MB"
          % (os.path.getsize(args.dst) / 1048576,
             os.path.getsize(args.dst) / 1048576 * 1.34))


if __name__ == "__main__":
    main()
