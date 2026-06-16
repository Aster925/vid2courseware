# -*- coding: utf-8 -*-
"""
Keyframe extraction for on-screen slides / documents.

Many lessons show the actual courseware on screen (slides, a Word doc, a PDF).
That on-screen text is far cleaner than the audio, so we grab it as images:
sample frames at a fixed interval, then drop near-identical frames using a
perceptual hash (average-hash + Hamming distance). To survive *scrolling* text,
the hash is computed on a cropped central region, ignoring static UI chrome.

抽帧+感知哈希去重，只保留画面有变化的关键帧（幻灯片/文档页）。对中央正文区域做哈希，
以便捕捉文档滚动。

Usage:
    python -m core.extract_frames --input lecture.mp4
    python -m core.extract_frames --seq 6          # a manifest row
"""
import os
import sys
import glob
import json
import argparse
import subprocess

sys.stdout.reconfigure(encoding="utf-8")
from core.cfg import load_config

import imageio_ffmpeg
from PIL import Image

FF = imageio_ffmpeg.get_ffmpeg_exe()


def ahash(path, crop, n=32):
    """average-hash of a cropped region → list of bits."""
    img = Image.open(path).convert("L")
    w, h = img.size
    box = (int(w * crop[0]), int(h * crop[1]), int(w * crop[2]), int(h * crop[3]))
    img = img.crop(box).resize((n, n))
    px = list(img.getdata())
    avg = sum(px) / len(px)
    return [1 if p > avg else 0 for p in px]


def hamming(a, b):
    return sum(x != y for x, y in zip(a, b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--input", help="single video file")
    ap.add_argument("--seq", type=int, help="manifest row to use as input")
    ap.add_argument("--interval", type=int)
    ap.add_argument("--thresh", type=int)
    args = ap.parse_args()

    cfg = load_config(args.config)
    fcfg = cfg.get("frames", {})
    out_dir = cfg.get("output_dir", "./output")
    interval = args.interval or int(fcfg.get("interval_sec", 10))
    thresh = args.thresh or int(fcfg.get("hash_threshold", 45))
    crop = fcfg.get("crop", [0.0, 0.0, 1.0, 1.0])

    if args.input:
        src, key = args.input, os.path.splitext(os.path.basename(args.input))[0]
    elif args.seq is not None:
        with open(os.path.join(out_dir, "manifest.json"), encoding="utf-8") as f:
            row = next(r for r in json.load(f) if r.get("seq") == args.seq)
        src, key = row["path"], f"seq{args.seq}"
    else:
        sys.exit("Pass --input FILE or --seq N")

    raw = os.path.join(out_dir, "frames", key, "_raw")
    keep = os.path.join(out_dir, "frames", key)
    for d in (raw, keep):
        os.makedirs(d, exist_ok=True)
        for f in glob.glob(os.path.join(d, "*.jpg")):
            os.remove(f)

    print(f"sampling every {interval}s ...")
    subprocess.run([FF, "-y", "-i", src, "-vf", f"fps=1/{interval},scale=1280:-1",
                    "-q:v", "3", os.path.join(raw, "r%05d.jpg")],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    rawfiles = sorted(glob.glob(os.path.join(raw, "*.jpg")))
    last, kept = None, 0
    for i, rf in enumerate(rawfiles):
        h = ahash(rf, crop)
        if last is None or hamming(h, last) >= thresh:
            t = i * interval
            os.replace(rf, os.path.join(keep, f"f{kept:03d}_{t//60:02d}m{t%60:02d}s.jpg"))
            last, kept = h, kept + 1
    for f in glob.glob(os.path.join(raw, "*.jpg")):
        os.remove(f)
    os.rmdir(raw)
    print(f"{len(rawfiles)} sampled → {kept} keyframes kept → {keep}")


if __name__ == "__main__":
    main()
