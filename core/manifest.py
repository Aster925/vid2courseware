# -*- coding: utf-8 -*-
"""
Inventory + de-duplication of a video corpus.

Scans one or more source folders for *.mp4, computes a cheap "head+tail"
fingerprint to detect byte-identical copies across folders, parses a date from
each file's mtime for ordering, and writes manifest.json / manifest.csv.

清点视频语料并去重：扫描 *.mp4，用「大小 + 首尾各 4MB 的哈希」判定完全相同的拷贝，
按修改时间排序，输出 manifest.json / manifest.csv。

Note: this only finds *byte-identical* copies. "Re-recordings of the same
lesson" differ byte-wise and must be found later via transcript similarity
(see core/analyze.py).

Usage:
    python -m core.manifest                       # read folders from config.yaml
    python -m core.manifest --sources D:/a E:/b   # or pass folders directly
"""
import os
import sys
import csv
import json
import hashlib
import argparse
from datetime import datetime
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
from core.cfg import load_config

HEAD_TAIL = 4 * 1024 * 1024  # 4 MB from start + 4 MB from end


def fingerprint(path, size):
    """size + sha1(first 4MB + last 4MB). Fast, and collisions are negligible."""
    if size == 0:
        return "EMPTY"
    h = hashlib.sha1(str(size).encode())
    try:
        with open(path, "rb") as f:
            h.update(f.read(HEAD_TAIL))
            if size > HEAD_TAIL:
                f.seek(size - HEAD_TAIL)
                h.update(f.read(HEAD_TAIL))
    except OSError as e:
        return "ERR:" + str(e)
    return h.hexdigest()


def guess_tags(name, tag_map):
    low = name.lower()
    hits = [tag for tag, kws in tag_map.items() if any(k.lower() in low for k in kws)]
    return "+".join(hits) if hits else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--sources", nargs="*", help="override source folders")
    ap.add_argument("--output-dir", help="override output dir")
    args = ap.parse_args()

    cfg = load_config(args.config)
    sources = args.sources or cfg.get("sources") or []
    out_dir = args.output_dir or cfg.get("output_dir", "./output")
    tag_map = cfg.get("tags") or {}
    if not sources:
        sys.exit("No sources. Set `sources:` in config.yaml or pass --sources.")
    os.makedirs(out_dir, exist_ok=True)

    rows = []
    for src in sources:
        if not os.path.isdir(src):
            print(f"[warn] not a folder: {src}")
            continue
        for root, _, files in os.walk(src):
            for fn in files:
                if not fn.lower().endswith(".mp4") or fn.startswith("._"):
                    continue
                full = os.path.join(root, fn)
                try:
                    st = os.stat(full)
                except OSError:
                    continue
                mtime = datetime.fromtimestamp(st.st_mtime)
                note = "empty/corrupt" if st.st_size == 0 else (
                    "fragment?" if st.st_size < 60 * 1024 * 1024 else "")
                rows.append({
                    "source": src,
                    "path": full,
                    "filename": fn,
                    "size_mb": round(st.st_size / 1048576, 1),
                    "date": mtime.strftime("%Y-%m-%d"),
                    "mtime": mtime.strftime("%Y-%m-%d %H:%M"),
                    "tags": guess_tags(fn, tag_map),
                    "fp": fingerprint(full, st.st_size),
                    "note": note,
                })

    # group by fingerprint, keep one canonical copy per group
    groups = {}
    for r in rows:
        groups.setdefault(r["fp"], []).append(r)
    for fp, grp in groups.items():
        canon = sorted(grp, key=lambda x: x["path"])[0]
        for r in grp:
            r["canonical"] = (r is canon) and fp not in ("EMPTY",)
            r["dup_of"] = "" if r is canon else canon["path"]

    uniques = sorted([r for r in rows if r["canonical"]],
                     key=lambda x: (x["mtime"], x["filename"]))
    for i, r in enumerate(uniques, 1):
        r["seq"] = i

    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    cols = ["seq", "canonical", "source", "date", "tags", "size_mb",
            "filename", "note", "dup_of", "fp", "path"]
    with open(os.path.join(out_dir, "manifest.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(rows, key=lambda x: (not x["canonical"], x.get("seq", 1 << 30))):
            w.writerow(r)

    dups = sum(1 for r in rows if not r["canonical"] and r["fp"] != "EMPTY")
    print(f"scanned {len(rows)} files → {len(uniques)} unique, {dups} duplicate copies")
    if any(r["tags"] for r in uniques):
        print("tag distribution:", dict(Counter(r["tags"] or "?" for r in uniques)))
    print(f"wrote {os.path.join(out_dir, 'manifest.json')} / manifest.csv")


if __name__ == "__main__":
    main()
