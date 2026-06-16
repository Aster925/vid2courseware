# -*- coding: utf-8 -*-
"""
Clean WebVTT subtitles into plain .txt.

Drops headers/timestamps/cue indices, strips inline karaoke tags, and collapses
the consecutive duplicate lines that YouTube auto-subs love to produce.

把 .vtt 字幕清洗成纯文本：去掉时间轴/标签/自动字幕的重复行。

Usage:
    python vtt_to_text.py data/raw_vtt data/transcripts
"""
import re
import sys
import pathlib


def vtt_to_text(vtt_path):
    lines = pathlib.Path(vtt_path).read_text(encoding="utf-8").splitlines()
    out, prev = [], None
    for line in lines:
        if line.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        if "-->" in line or line.strip().isdigit():
            continue
        clean = re.sub(r"<[^>]+>", "", line).strip()   # strip <00:00:01.000><c> tags
        if clean and clean != prev:                    # collapse consecutive dupes
            out.append(clean)
            prev = clean
    return " ".join(out)


if __name__ == "__main__":
    src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "data/raw_vtt")
    dst = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "data/transcripts")
    dst.mkdir(parents=True, exist_ok=True)
    for vtt in sorted(src.glob("*.vtt")):
        stem = vtt.stem.rsplit(".", 1)[0]   # drop the ".en" language tag
        (dst / f"{stem}.txt").write_text(vtt_to_text(vtt), encoding="utf-8")
        print(f"cleaned -> {stem}.txt")
